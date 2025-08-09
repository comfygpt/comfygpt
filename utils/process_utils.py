import json
def format(node_type):
    last_index = node_type.rfind('_')
    if last_index==-1:
        raise("error")
    if last_index != -1:
        result = node_type[:last_index]
    return result
def del_digram_primitive(digram):
    result_digram = []
    for edge in digram:
        # print(edge)
        src_type,src_name,dst_type,dst_name = edge
        src_node = format(src_type)
        dst_node = format(dst_type)
        if src_node =="PrimitiveNode" or dst_node == "PrimitiveNode":
            continue
        result_digram.append(edge)
    return result_digram


def json_format(encode):
    if not isinstance(encode,str):
        return encode
    if ("'''json") in encode:
        start = int(encode.find("'''json") + len("'''json"))
        end = int(encode.find("'''", start))
        # print(start,end)
        if start == -1 or end == -1:
            raise("error")
        encode = encode[start:end].strip().strip('"')
    if ("```json") in encode:
        start = int(encode.find("```json") + len("```json"))
        end = int(encode.find("```", start))
        # print(start,end)
        if start == -1 or end == -1:
            raise("error")
        encode = encode[start:end].strip().strip('"')
    # print(encode)
    # encode = encode.replace("，",',')
    encode = encode.replace("'",'"')
    encode = encode.replace("\n",'')
    count_1 = 0
    count_2 = 0
    for char in encode:
        if char =="[":
            count_1+=1
        if char =="]":
            count_2+=1 
    if count_1 == 0 or count_2 == 0 or count_1 != count_2:
        print(encode)
        raise("error")
   
    
    start = int(encode.find("[") )
    end = int(encode.rfind("]"))
   
    encode = encode[start:end+1]
    # print("ok")
    # print(encode)
    encode = json.loads(encode)

    return encode

