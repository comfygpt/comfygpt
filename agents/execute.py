import sys
import json
import utils.comfy_api
from utils.process_utils import *
NO_LINK_TYPES = ['STRING','FLOAT','INT','BOOLEAN']

class ExecuteAgent:
    
    def __init__(self,node_base,cfg):
        self.node_base = node_base
        self.comfyui_address = cfg.execute_agent.comfyui_address


    
    def parse_diagram_to_workflow(self,diagram,version=0.4,type_to_pos = None):
        count = 1
        type_to_id = {}
        links = []
        link_count = 1
        inputs_dict = {}
        outputs_dict = {}
        catch_candidate_inputs = {}
        for i,(src_node,src_name,dst_node,dst_name) in enumerate(diagram):
            # print(i,src_node,dst_node)
            if src_node not in type_to_id:
                type_to_id[src_node] = count
                count+=1
            if dst_node not in type_to_id:
                type_to_id[dst_node] = count
                count+=1

            src_id = type_to_id[src_node]
            dst_id = type_to_id[dst_node]
            src_type = format(src_node)
            dst_type = format(dst_node)

            if src_id not in outputs_dict:
                # print(src_type)
                outputs_dict[src_id] = self.fetch_node_outputs(src_type)

            if dst_id not in inputs_dict:
                inputs_dict[dst_id],catch_candidate_inputs[dst_type] = self.fetch_node_inputs(dst_type)
            
            outputs = outputs_dict[src_id]
            inputs = inputs_dict[dst_id]
            candidate_inputs = catch_candidate_inputs[dst_type]

            ##########  Judge Valid
            outputs,inputs,link,link_count = decode_edge(outputs,inputs,candidate_inputs,link_count,src_id,dst_id,src_name,dst_name)


            outputs_dict[src_id] = outputs
            inputs_dict[dst_id] = inputs
            
            link_count+=1
            links.append(link)
        
        # print(outputs_dict[9])
        for id,inputs in inputs_dict.items():
            tmp_input = []
            for input in inputs:
                if len(input) == 0:
                    continue
                tmp_input.append(input)
            inputs_dict[id] = tmp_input
        
        nodes = []
        for type,id in type_to_id.items():
            # print(type)
            inputs = []
            if id in inputs_dict:
                inputs = inputs_dict[id]
            outputs = []
            if id in outputs_dict:
                outputs = outputs_dict[id]

            node = {
                "id":id,
                "type":format(type),
                # "order":i,
                "inputs":inputs,
                "outputs":outputs
            }
            if type_to_pos is not None:
                node['pos'] = type_to_pos[type]['pos']
                node['size'] = type_to_pos[type]['size']
            nodes.append(node)


        decode_payload = {
            "last_link_id":link_count-1,
            "nodes":nodes,
            "links":links,
            "version":version
        }

        decode_payload['extra'] = {"extra": {
        "ds": {
        "scale": 0.952486143572623,
        "offset": [
        163.72358533046707,
        22.018287636666063
            ]
        }}}
        return decode_payload
    def fetch_node_inputs(self,node_type):
        input_types = self.node_base.fetch_node_meta_info(node_type)['inputs']
        if input_types is None:
            input_types = {}
            
        inputs = []
        else_inputs = []
        for key,item in input_types.items():
            if key != 'hidden':
                for name,val in item.items():
                    val_type = val[0]
                
                    if isinstance(val_type,list):
                        continue
                    if val_type not in NO_LINK_TYPES:
                        input = {
                            "name":name,
                            "type":val_type
                        }
                        inputs.append(input)

                    elif len(val)>1:
                        val_info = val[1]
                        if 'defaultInput' in val_info:
                            input = {
                                "name":name,
                                "type":val_type
                            }
                            else_inputs.append(input)
        inputs.extend(else_inputs)
        candidate_inputs = get_node_candidate_inputs(input_types,inputs)
        return inputs,candidate_inputs

    def fetch_node_outputs(self,node_type):
        node_meta_info = self.node_base.fetch_node_meta_info(node_type)
        output_types = node_meta_info['outputs']
        if output_types is None:
            output_types = {}
        output_names = node_meta_info.get("output_names",None)
        outputs = []

        for i,type in enumerate(output_types):
            output = {
                "type":type,
                "slot_index":i,
                "links":[]
            }
            if output_names is not None:
                output['name'] = output_names[i]
            else:
                output['name'] = type
            outputs.append(output)
        return outputs



def get_output_info(outputs):
    has_name = False
    erro_tag = False
    type_dict = []
    output_names = {}
    for index,val in enumerate(outputs):
        if 'name' in val:
            has_name = True
        if val['type'] in type_dict:
            erro_tag = True
        type_dict.append(val['type'])


        
        output_names[val['name']] = index

        
        
    if not has_name and erro_tag:
        raise ValueError("ouputs format error")
    
    return output_names
def get_node_candidate_inputs(input_types,inputs):
    candidate_inputs = []
    inputs_names = [ input['name'] for input in inputs]
    for key,item in input_types.items():
        if key != 'hidden':
            for name,val in item.items():
                val_type = val[0]
                if name in inputs_names:
                    continue
                if val_type not in NO_LINK_TYPES and not isinstance(val,list):
                    continue
                    
                input= {
                    'name':name,
                    'type':val_type
                }

                candidate_inputs.append(input)

    return candidate_inputs   
def decode_edge(outputs,inputs,candidate_inputs,link_count,src_id,dst_id,output_name,input_name):
        link = []
        
    
        output_names= get_output_info(outputs)
        if output_name not in output_names:
            # print(output_name,dst_id)
            raise(NAME_EXCEPTION(output_name))
        
        src_port = output_names[output_name]

        output = outputs[src_port]
        links = output['links']
        links.append(link)
        output['links'] = links
        outputs[src_port] = output

        input = None
        for i,_input in enumerate(inputs):
            if _input['name'] == input_name:
                input = _input
                input['link'] = link_count
                dst_port = i
                break
        if input is None:
            for _input in candidate_inputs:
                if _input['name'] == input_name:
                    input = {
                    "name":input_name,
                    "type":_input['type'],
                    "link":link_count,
                    "widget": {
                        "name": input_name
                        }
                    }
                    dst_port = len(inputs)
                    inputs.append(input)
                    break
        if input is None:
            print(input_name)
            # print(candidate_inputs)
            raise(NAME_EXCEPTION(output_name))
        if input['type'] != output['type']:
            raise("input and output type not consistant")


        #link
        link_type = input['type']
        
        link = [link_count,src_id,src_port,dst_id,dst_port,link_type]

        
        return outputs,inputs,link,link_count   

    


class NAME_EXCEPTION(Exception):
    pass


    
class REQUIR_MISS_EXCEPTION(Exception):
    pass





