from agents.execute import ExecuteAgent,NAME_EXCEPTION,REQUIR_MISS_EXCEPTION
from agents.refine import RefineAgent,NODE_MISS_EXCEPTION,NodeBase
from agents.flow import FlowAgent
import os
import json
import argparse
import yaml
from omegaconf import OmegaConf

# instruction = "This workflow can generate image, using sd3 model."
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", type=str, default="config/comfygpt.yaml", help="Path to YAML config file")
    parser.add_argument("--instruction",type=str,required=True,help="Instruction to process")
    parser.add_argument("--refine",type=bool,default=True,help="is refine diagram")
    return parser.parse_args()

def main():
    args = parse_args()
    cfg = OmegaConf.load(args.config_path)
    # print(cfg)
    pipe(args,cfg)
    # 推理/训练逻辑



def pipe(args,cfg,is_refine = True):
    instruction = args.instruction
    flow_agent = FlowAgent(cfg)

    node_base = NodeBase(cfg)
    refine_agent = RefineAgent(node_base,cfg)
    execute_agent = ExecuteAgent(node_base,cfg)

    diagram = flow_agent.generate(instruction)


  
    if args.refine:
        print(f"Refine Agent: refining diagram.....")
        diagram = refine_agent.refine_diagram(diagram,instruction)
        print(f"Refine Over")
    
    workflow = execute_agent.parse_diagram_to_workflow(diagram)
    with open("workflow.json",'w') as f:
        json.dump(workflow,f)

if __name__ == '__main__':

    main()
