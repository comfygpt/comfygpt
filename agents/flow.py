from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModel,LlamaForCausalLM
from utils.process_utils import *
import json

class FlowAgent:
    def __init__(self, cfg):

        self.model = AutoModelForCausalLM.from_pretrained(
                cfg.flow_agent.model_path,
                torch_dtype="auto",
                device_map="auto",
                trust_remote_code=True
                
        )
        self.top_p = cfg.flow_agent.top_p
        self.max_new_tokens = cfg.flow_agent.max_new_tokens
        self.temperature = cfg.flow_agent.temperature
        self.primitive = cfg.flow_agent.primitive
        self.tokenizer = AutoTokenizer.from_pretrained(cfg.flow_agent.model_path,trust_remote_code=True)
        self.template ="Based on the description I provided, generate a JSON example of the required ComfyUi workflow. description: "


    def generate(self,prompt):
        if self.template not in prompt:
            prompt = self.template + prompt

        messages = [            
            {"role": "user", "content": prompt}
        ]
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        # print(text)
        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=self.max_new_tokens,
            temperature = self.temperature,
            do_sample=True, 
            top_p=self.top_p,     
        )
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]

        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        diagram = self.post_process(response)
        return diagram 

    def post_process(self,response):
        
        diagram = response
        if isinstance(diagram,str):
            diagram = json.loads(diagram)

        if not self.primitive:
            # print(1)
            diagram = del_digram_primitive(diagram)
        # print(isinstance(diagram,str))
        return diagram
    