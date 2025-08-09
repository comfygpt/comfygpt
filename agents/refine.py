from tinydb import TinyDB, Query
from sentence_transformers import SentenceTransformer
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics.pairwise import cosine_similarity
import os
from collections import Counter
# from utils.gpt_utils import get_gpt_response
import json
import re
import traceback
from utils.process_utils import *


class RefineAgent():
    def __init__(self,node_base,cfg):
        
        self.k = cfg.refine_agent.k
        self.node_base = node_base
        if cfg.refine_agent.local:

            self.max_new_tokens = cfg.refine_agent.max_new_tokens
            self.local = True
            self.model = AutoModelForCausalLM.from_pretrained(
                cfg.refine_agent.model_path,
                torch_dtype="auto",
                device_map="auto"
            )
            self.tokenizer = AutoTokenizer.from_pretrained(cfg.refine_agent.model_path)
    
    def refine_diagram(self,diagram,prompt):
      
        swap_map = {}
        # print(diagram)
        for edge in diagram:
            # print(edge)
            src_type,src_name,dst_type,dst_name = edge
            src_node = format(src_type)
            dst_node = format(dst_type)
            if not self.node_base.not_in_sql(src_node):
                if src_node not in swap_map:
                    print(f"1 {edge}  miss:{src_node}")
                    if self.local:
                        swap_name = self.fix_node_name_local(prompt,diagram,src_node)
                    else:
                        swap_name = self.fix_node_name(prompt,diagram,src_node)
                    if swap_name is not None:
                        swap_map[src_node] = swap_name
                        # print(swap_map)
         
            if not self.node_base.not_in_sql(dst_node):
                if dst_node not in swap_map:
                    print(f"2 {edge}  miss:{dst_node}")
                    if self.local:
                        swap_name = self.fix_node_name_local(prompt,diagram,src_node)
                    else:
                        swap_name = self.fix_node_name(prompt,diagram,src_node)
                    if swap_name is not None:
                        swap_map[dst_node] = swap_name
                        # print(swap_map)            
                        
        for i,edge in enumerate(diagram):
    
            src_type,src_name,dst_type,dst_name = edge
            src_node = format(src_type)
            dst_node = format(dst_type)
            if src_node in swap_map:
                swap_name = swap_map[src_node]
                edge[0] = edge[0].replace(src_node,swap_name)
            if dst_node in swap_map:
                swap_name = swap_map[dst_node]
                edge[2] = edge[2].replace(dst_node,swap_name)
            diagram[i] =edge
        print(swap_map) 
        return diagram
    
    
    # def fix_node_name(self,desc,diagram,error_name):
    #     candidate_nodes = self.node_base.find_most_similar(error_name,self.k)
    #     candidate_node_names = [e['node_name'] for e in candidate_nodes]
    #     request_text = f"I would like you to act as an expert in ComfyUI platform. I will provide a example, including a description about ComfyUI workflow and a logical diagram in json format represents the comfyui workflow. The logical diagram is a edges list [edge_1, edge_2, edge_3, ... , edge_n],  each edge is consist of [output_node_name,output_name,input_node_name,input_name], represents a line between output node and input node. Example: description: {desc}. logical diagram: {str(diagram)}. Now, This logical diagram has one error node name. error name: {error_name}. I will give you some candidate nodes. Please combine the above information to select the most suitable candidate node. Candidate nodes: {str(candidate_nodes)}. You just need to return you choose node name. Please return result in pure JSON format, including: " +"'''json{\"candidate_node_name\":\"...\"}'''"
    #     try: 
    #         code,result = get_gpt_response(request_text=request_text,model_name="chatgpt-4o-latest")
    #         result = result.replace('```json\n', '').replace('```', '').strip()
    #         result = result.replace("'",'"')
    #         result = result.replace("\n",'')
    #         result = json.loads(result)
    #         result = result['candidate_node_name']
    #     except Exception as e:
    #         traceback.print_exc()
    #         return None

        # if result not in candidate_node_names:
        #     return None

        
        # return result


    def fix_node_name_local(self,desc,diagram,error_name):
 
        candidate_nodes = self.node_base.find_most_similar(error_name,self.k)
        candidate_node_names = [e['node_name'] for e in candidate_nodes]
        prompt = f"I would like you to act as an expert in ComfyUI platform. I will provide a example, including a description about ComfyUI workflow and a logical diagram in json format represents the comfyui workflow. The logical diagram is a edges list [edge_1, edge_2, edge_3, ... , edge_n],  each edge is consist of [output_node_name,output_name,input_node_name,input_name], represents a line between output node and input node. Example: description: {desc}. logical diagram: {str(diagram)}. Now, This logical diagram has one error node name. error name: {error_name}. I will give you some candidate nodes. Please combine the above information to select the most suitable candidate node. Candidate nodes: {str(candidate_nodes)}. You just need to return you choose node name. Please return result in pure JSON format, including: " +"'''json{\"candidate_node_name\":\"...\"}'''"

        messages = [
            {"role": "system", "content": "You are Qwen, created by Alibaba Cloud. You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = self,tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=self.max_new_token
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        result = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]


        try: 
            result = json_format(result)
        except Exception as e:
            traceback.print_exc()
            return None

        print(candidate_nodes)
        if result not in candidate_node_names:
            return None
   
        return result
   
        
    
class NODE_MISS_EXCEPTION(Exception):
    pass


class NodeBase():
    def __init__(self,cfg):
        self.node_list = json.load(open(cfg.node_base.node_list_path,'r'))
        self.node_info_db = TinyDB(cfg.node_base.node_info_db_path)
    

        self.cache_node_meta_info = {}
        print(f"Load Local Node Base: total node: {len(self.node_list)} total node info: {len(self.node_info_db.all())}")
        self.embedding_model = SentenceTransformer(cfg.node_base.embedding_model_path)
        self.list_embeddings = self.embedding_model.encode(self.node_list)
        
    
    def fetch_node_meta_info(self,node_type):
        if node_type not in self.node_list:
            print(f"miss {node_type}")
            return None

        node_meta_info = self.cache_node_meta_info.get(node_type,None)
        if node_meta_info == None:
            query = Query()
            node_meta_info_list = self.node_info_db.search(query.node_type == node_type)

            if len(node_meta_info_list)==0:
                print(f"miss {node_type}")
                raise(NODE_MISS_EXCEPTION(node_type))
                node_meta_info = None
            else:
                node_meta_info = node_meta_info_list[0]
                self.cache_node_meta_info[node_type] = node_meta_info
      
        return node_meta_info

    def find_most_similar(self,node_type,k = 5):

        query_embedding = self.embedding_model.encode([node_type])
    
        similarities = cosine_similarity(query_embedding, self.list_embeddings)[0]
        

        top_k_indices = np.argsort(similarities)[-k:][::-1]
        similar_node_list = [self.node_list[i] for i in top_k_indices]
        similar_node_infos = []
        for node_type in similar_node_list:

            similar_node_infos.append(self.get_node_diagram_info(node_type))

        return similar_node_infos
    
    def not_in_sql(self,node_type):
        return node_type in self.node_list
      

    def get_node_diagram_info(self,node_type):
        meta_info = self.node_base.fetch_node_meta_info(node_type)
        input_names = fetch_node_input_names(meta_info)
        output_names = fetch_node_output_names(meta_info)
        info = {
            "node_name":node_type,
            "input_names":input_names,
            "output_names":output_names
        }
        return info