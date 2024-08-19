import os
import json
import copy

def read_llmchat_to_test_scenario(s):
    s = s.replace("：", ":").replace("（", "(").replace("）", ")").replace(" ", "")
    lines = s.split("\n")
    test_scenarioes = []
    test_scenario = {}
    A_num = 0
    begin = False
    for line in lines:
        line = line.strip().replace("ID", "id")
        if "(" in line:
            line = line.split("(")[0]
        if line == "" or "前置规则" in line:
            continue
        if "A" == line:
            A_num += 1
        if A_num <= 1:
            continue
        end = False
        if line[:2] == "id":
            k, v = line.split(":")[0].strip(), ":".join(line.split(":")[1:])
            if v.find("(") != -1:
                v = v[:v.find("(")]
            test_scenario[k] = v
            begin = True
        elif line[:4] == "后置规则":
            end = True
        elif begin:
            k, v = line.split(":")[0].strip(), ":".join(line.split(":")[1:])
            test_scenario[k] = v
        
        if end:
            begin = False
            if "交易方向" in test_scenario and test_scenario['交易方向'] == "买入/卖出":
                test_scenario_1 = copy.deepcopy(test_scenario)
                test_scenario['交易方向'] = '买入'
                test_scenario_1['交易方向'] = '卖出'
                test_scenarioes.append(test_scenario)
                test_scenarioes.append(test_scenario_1)
            else:
                test_scenarioes.append(test_scenario)
            test_scenario = {}
    return test_scenarioes


if __name__ == "__main__":
    for file in sorted(os.listdir("exp1_data/llm_result/")):
        if "_chat_" in file:
            print("处理文件" + file)
            llm = file.split("_")[0]
            dataset = file.split("_")[-1].split(".")[0]
            with open("exp1_data/llm_result/" + file, "r", encoding="utf-8") as f:
                s = f.read()
            test_scenarioes = read_llmchat_to_test_scenario(s)
            json.dump(test_scenarioes, open(f"exp1_data/llm_result/{llm}_test_scenario_{dataset}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    
    for file in sorted(os.listdir("exp2_data/llm_result")):
        if "_chat_" in file:
            print("处理文件" + file)
            llm = file.split("_")[0]
            dataset = file.split("_")[-1].split(".")[0]
            with open("exp2_data/llm_result/" + file, "r", encoding="utf-8") as f:
                s = f.read()
            test_scenarioes = read_llmchat_to_test_scenario(s)
            json.dump(test_scenarioes, open(f"exp2_data/llm_result/{llm}_test_scenario_{dataset}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)

    for file in sorted(os.listdir("exp4_data/llm_result")):
        if "_chat_" in file and "_chinese" in file and "traditional" not in file:
            print("处理文件" + file)
            llm = file.split("_")[0]
            dataset = file.split("_")[2]
            with open("exp4_data/llm_result/" + file, "r", encoding="utf-8") as f:
                s = f.read()
            test_scenarioes = read_llmchat_to_test_scenario(s)
            json.dump(test_scenarioes, open(f"exp4_data/llm_result/{llm}_test_scenario_{dataset}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)