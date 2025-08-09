
import requests
import websocket
import urllib.request
import json
import time
CLIENT_ID = 1
TIME_LIMIT = 60*15
def get_history(prompt_id,address = "127.0.0.1:8188"):
    response = requests.get(f"http://{address}/history/{prompt_id}")
    
    return response.json()

def get_prompt_queue(address = "127.0.0.1:8188"):
    response = requests.get(f"http://{address}/prompt")
    
    return response.json()
def interrupt_prompt(address = "127.0.0.1:8188"):
    response = requests.get(f"http://{address}/interrupt")
    
    
def execute_prompt(prompt,address = "127.0.0.1:8188"):
    
    data = {
        "prompt": prompt,  # 替换为你的工作流节点数据
        "client_id": CLIENT_ID
    }
    outputs = {}


    # print(prompt_id)
    # socket = websocket.WebSocket()
    # socket.connect(f"ws://{address}/ws?clientId={CLIENT_ID}")
    
    prompt_response = requests.post(f"http://{address}/prompt", json=data).json()
    # print(prompt_response)
    if 'prompt_id' not in prompt_response:
        print("promopt_response:",prompt_response)
        return None,prompt_response['error']['type']
        # raise("validate error")
    prompt_id = prompt_response['prompt_id']
    ##判断成功
    # work()
    start_time = time.time()
    while True:
        # print(1)
        elapsed_time = time.time() - start_time
        if elapsed_time > TIME_LIMIT:
            inter_time = time.time()

            while True:
                interrupt_prompt(address)
                interrupt_time = time.time() - inter_time
                if interrupt_time>60*5:
                    break
                queue = get_prompt_queue(address)
                # print(queue)
                # print(queue)
                if queue['exec_info']['queue_remaining'] == 0:
                    break
                        
            return None,"e_error"
        # data = socket.recv()
        # print(data)
        queue = get_prompt_queue(address)
        # print(queue)
        # print(queue)
        if queue['exec_info']['queue_remaining'] == 0:
            break
        # if isinstance(data, str):
        #     message = json.loads(data)
            
        #     if message['type'] == 'executing':
        #         message = message['data']
        #         if message['node'] is None and message['prompt_id'] == prompt_id:
        #             break
            # elif message['type'] == "crystools.monitor":
            #     print("1")
            #     break
        # if time.time() > timeout:
        #     interrupt_prompt()
        #     raise TimeoutError('execution timeout')
        
    history = get_history(prompt_id,address)[prompt_id]
    
    # for node_output in history['outputs'].values():
    #     for type_output in node_output.values():
    #         for spec_output in type_output:
    #             if isinstance(spec_output, dict) and spec_output['type'] == 'output':
    #                 output = fetch_output(spec_output['filename'], spec_output['subfolder'])
    #                 outputs[spec_output['filename']] = output

    status = history['status']
    
    status_str = status.get("status_str","success")
    # print(status)
    if status_str =="error":
        # print(status)
        return status,"e_error"
  
    return status,"success"




# def work():
#     ws = websocket.WebSocket()
#     ws.connect("ws://{}/ws?clientId={}".format("127.0.0.1:8080", CLIENT_ID))

#     while True:
#         out = ws.recv()
#         print(out)
        
        
        


if __name__ == '__main__':
    client_id = "1"
    data = json.load(open("./example.json",'r'))
    data = {
        "prompt": data,  # 替换为你的工作流节点数据
        "client_id": client_id
    }

    print(execute_prompt(data))
    