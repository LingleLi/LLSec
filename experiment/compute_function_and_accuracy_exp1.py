import copy
import json
import re
import nltk
import os
from specification_generation.rule_assembly import is_key_for_time, is_key_for_quantity, is_key_for_price


def judge_str_same(s1, s2, threshold=0.8):
    # s1是预测值，s2是真实值
    distance = nltk.edit_distance(s1, s2)
    score = 1 - (distance / max(len(s1), len(s2)))
    if score >= threshold:
        return True
    else:
        if "方式" == s1[:-2] and s1[:-2] == s2 or "方式" == s2[:-2] and s1 == s2[:-2]:
            return True
        return False

def judge_tqp_same(s1, s2):
    if s1 == s2:
        return True
    if s1 in s2:
        b, e = s2.find(s1), s2.find(s1)+len(s1)
        if "," not in s2[:b] and "," not in s2[e:] and len(re.findall(r"\d+", s2[:b])) == 0 and len(re.findall(r"\d+", s2[e:])) == 0:
            return True
    if s2 in s1:
        b, e = s1.find(s2), s1.find(s2)+len(s2)
        if "," not in s1[:b] and "," not in s1[e:] and len(re.findall(r"\d+", s1[:b])) == 0 and len(re.findall(r"\d+", s1[e:])) == 0:
            return True
    return False

def judge_op(value):
    value = value.replace("得", "")
    
    if "不低于" in value or "达到" in value or "以上" in value:
        return ">="
    if "不高于" in value or "以下" in value or "不超过" in value or "以内" in value:
        return "<="
    if "低于" in value or "未达到" in value or "不足" in value or "小于" in value:
        return "<"
    if "高于" in value or "超过" in value or "优于" in value or "大于" in value:
        return ">"
    if "等于" in value or "为" in value:
        return "=="
    if "不等于" in value:
        return "!="
    return ""

def is_number(s):
    try:
        s = float(s)
        return True
    except ValueError:
        return False




def compute_accuracy(testcases, scenarios, f, without_knowledge=False):
    # 预处理scenarios
    new_scenarios = []  # new_scenarios[i]['交易市场']='深圳证券交易所'
    scenarios_variables = []  # scenario_variables[i]['交易市场'] = 0代表该元素未被覆盖，1代表覆盖
    max_cover_varnum = [0] * len(scenarios)  # 每个测试场景的最大覆盖变量数量

    for scenario in scenarios:
        s = {}
        variables = {}
        scs = scenario.split(";")
        for sc in scs:
            if sc == "":
                continue
            if "时间" not in sc:
                ss = sc.split(":")
                s[ss[0]] = ss[1]
                variables[ss[0]] = 0
            else:
                ss = sc.split(":")
                s[ss[0]] = ":".join(ss[1:])
                variables[ss[0]] = 0
        new_scenarios.append(s)
        scenarios_variables.append(variables)
    scenarios = new_scenarios

    for scenario_index, scenario in enumerate(scenarios):
        scenario_variables_total = copy.deepcopy(scenarios_variables[scenario_index])  # 最大的覆盖记录
        for testcase_index, testcase in enumerate(testcases):
            scenario_variables = copy.deepcopy(scenarios_variables[scenario_index])
            
            # 计算这个testcase在scenario中覆盖了多少
            for testcase_key, testcase_value in testcase.items():
                # 无关的测试用例key跳过
                if testcase_key in ['id', '测试关注点'] or not isinstance(testcase_value, str) or (without_knowledge and (testcase_key.find("状态") == 0 or testcase_key.find("结果状态") == 0)):
                    continue
                for scenario_key, scenario_value in scenario.items():
                    testcase_value = testcase_value.replace("、", ",")
                    if scenario_value.find("不") == 0 and testcase_value.find("不") != 0 or scenario_value.find("不") != 0 and testcase_value.find("不") == 0:
                        continue
                    if is_key_for_time(scenario_key) and is_key_for_time(testcase_key) or is_key_for_quantity(scenario_key) and is_key_for_quantity(testcase_key) or is_key_for_price(scenario_key) and is_key_for_price(testcase_key):
                        if judge_tqp_same(scenario_value, testcase_value):
                            scenario_variables[scenario_key] = 1
                    if judge_str_same(scenario_value, testcase_value):
                        scenario_variables[scenario_key] = 1
                    # 对于scenario中的一条枚举变量，如果在testcase中存在value相似的字符串，则算覆盖；否则不算
                    if scenario_variables[scenario_key] != 1 and not is_key_for_quantity(scenario_key) and not is_key_for_time(scenario_key) and not is_key_for_price(scenario_key):
                        for s_value in scenario_value.split(","):
                            if judge_str_same(s_value, testcase_value):
                                scenario_variables[scenario_key] = 1
                                break

            if "id" in testcase:
                f.write(f"## 测试场景\"{scenario_index+1}\", 测试用例\"{testcase['id']}\", 覆盖变量数目为{sum(scenario_variables.values())}, 未覆盖的变量包括{[key for key in scenario_variables.keys() if scenario_variables[key] == 0]}\n")
            else:
                f.write(f"## 测试场景\"{scenario_index+1}\", 测试用例\"{testcase_index}\", 覆盖变量数目为{sum(scenario_variables.values())}, 未覆盖的变量包括{[key for key in scenario_variables.keys() if scenario_variables[key] == 0]}\n")
            
            for key in scenario_variables_total.keys():
                if scenario_variables[key] == 1:
                    scenario_variables_total[key] = 1
        
        max_cover_varnum[scenario_index] = sum(scenario_variables_total.values())
        if len(scenario_variables_total.keys()) > max_cover_varnum[scenario_index]:
            f.write(f"### 测试场景\"{scenario_index+1}\", 覆盖变量的最大数目为{max_cover_varnum[scenario_index]}, 整体未覆盖的变量包括{[key for key in scenario_variables_total.keys() if scenario_variables_total[key] == 0]}\n\n")
        else:
            f.write(f"### 测试场景\"{scenario_index+1}\", 覆盖变量的最大数目为{max_cover_varnum[scenario_index]}, 所有变量全部覆盖\n\n")
    
    max_cover_rate = [max_cover_varn / len(scenarios[i]) for i, max_cover_varn in enumerate(max_cover_varnum)]
    cover_rate = sum(max_cover_rate) / len(max_cover_rate)
    return cover_rate





def compute_acc_ours(our_dir, specification_dir, without_knowledge=False):
    num, accuracy = [], []
    for file in sorted(os.listdir(specification_dir)):
        # if "data5" not in file:
        #     continue
        if "exp1" in our_dir:
            f = open(f"exp1_data/log/ours_{file.split('_')[0]}.log", "w", encoding="utf-8")
        elif "exp4" in our_dir:
            f = open(f"exp4_data/log/ours_{file.split('_')[0]}.log", "w", encoding="utf-8")
        else:
            if without_knowledge:
                f = open(f"exp2_data/log/ours_without_knowledge_{file.split('_')[0]}.log", "w", encoding="utf-8")
            else:
                f = open(f"exp2_data/log/ours_{file.split('_')[0]}.log", "w", encoding="utf-8")
        if without_knowledge:
            testcase_file = f"{our_dir}/{file.split('_')[0]}_output_without_knowledge.json"
        else:
            testcase_file = f"{our_dir}/{file.split('_')[0]}_output.json"
        scenario_file = f"{specification_dir}/{file}"
        testcases = json.load(open(testcase_file, "r", encoding="utf-8"))
        scenarios = open(scenario_file, "r", encoding="utf-8").read().strip().split("\n")
        num.append(len(testcases))
        acc = compute_accuracy(testcases, scenarios, f, without_knowledge)
        print(f"我们的工具在数据集{file.split('_')[0]}上的生成功能点正确率为{round(acc, 4)}")
        f.write(f"我们的工具在数据集{file.split('_')[0]}上的生成功能点正确率为{round(acc, 4)}\n")
        accuracy.append(acc)
        f.close()
    return num, accuracy

def compute_acc_llm(llm_dir, specification_dir):
    num = {}
    accuracy = {}
    for file in sorted(os.listdir(llm_dir)):
        if "test_scenario" in file:
            llm = file.split("_")[0]
            if "exp1" in llm_dir:
                f = open(f"exp1_data/log/{llm}_{file.split('_')[-1].split('.')[0]}.log", "w", encoding="utf-8")
            elif "exp4" in llm_dir:
                f = open(f"exp4_data/log/{llm}_{file.split('_')[-1].split('.')[0]}.log", "w", encoding="utf-8")
            else:
                f = open(f"exp2_data/log/{llm}_{file.split('_')[-1].split('.')[0]}.log", "w", encoding="utf-8")
            testcase_file = llm_dir + "/" + file
            scenario_file = f"{specification_dir}/{file.split('_')[-1].split('.')[0]}_scenario.txt"
            testcases = json.load(open(testcase_file, "r", encoding="utf-8"))
            scenarios = open(scenario_file, "r", encoding="utf-8").read().strip().split("\n")
            if llm not in num:
                num[llm] = []
            num[llm].append(len(testcases))
            acc = compute_accuracy(testcases, scenarios, f)
            print(f"{llm}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}")
            f.write(f"{llm}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}\n")
            if llm not in accuracy:
                accuracy[llm] = []
            accuracy[llm].append(acc)
            f.close()
    return num, accuracy

def compute_acc_non_expert(non_expert_dir, specification_dir):
    num_list, acc_list = [], []
    for file in sorted(os.listdir(non_expert_dir)):
        if ".json" in file:
            # if "data4" not in file:
            #     continue
            testcases = json.load(open(f"{non_expert_dir}/{file}", "r", encoding="utf-8"))
            dataset = file.split(".")[0].split("_")[-1]
            scenarios = open(f"{specification_dir}/{dataset}_scenario.txt", "r", encoding="utf-8").read().strip().split("\n")
            if "exp1" in non_expert_dir:
                f = open(f"exp1_data/log/{file.split('.')[0]}.log", "w", encoding="utf-8")
            else:
                f = open(f"exp2_data/log/{file.split('.')[0]}.log", "w", encoding="utf-8")
            acc = compute_accuracy(testcases, scenarios, f)
            acc_list.append(acc)
            num_list.append(len(testcases))
            human = "_".join(file.split("_")[:2])
            print(f"{human}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}")
            f.write(f"{human}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}\n")
            f.close()
    # 计算均值
    if "exp1" in non_expert_dir:
        dataset_num = 5
        people_num = 2
    else:
        dataset_num = 4
        people_num = 1
    num, accuracy = [], []
    for dataset in range(dataset_num):
        num_sum, acc_sum = 0.0, 0.0
        for i in range(dataset, len(acc_list), dataset_num):
            acc_sum += acc_list[i]
            num_sum += num_list[i]
        acc_avg = acc_sum / people_num
        num_avg = num_sum / people_num
        print(f"non-expert在数据集{dataset+1}上的平均业务场景覆盖率为{round(acc_avg, 4)}")
        accuracy.append(acc_avg)
        num.append(int(num_avg))
    return num, accuracy

def compute_acc_expert(expert_dir, specification_dir):
    num, accuracy = [], []
    for file in sorted(os.listdir(expert_dir)):
        # if "data4" not in file:
        #     continue
        if ".json" in file:
            testcases = json.load(open(f"{expert_dir}/{file}", "r", encoding="utf-8"))
            dataset = file.split(".")[0].split("_")[-1]
            scenarios = open(f"{specification_dir}/{dataset}_scenario.txt", "r", encoding="utf-8").read().strip().split("\n")
            if "exp1" in expert_dir:
                f = open(f"exp1_data/log/{file.split('.')[0]}.log", "w", encoding="utf-8")
            else:
                f = open(f"exp2_data/log/{file.split('.')[0]}.log", "w", encoding="utf-8")
            num.append(len(testcases))
            acc = compute_accuracy(testcases, scenarios, f)
            human = "_".join(file.split("_")[:2])
            print(f"{human}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}")
            f.write(f"{human}在数据集{file.split('_')[-1].split('.')[0]}上的业务场景覆盖率为{round(acc, 4)}\n")
            accuracy.append(acc)
            f.close()
    return num, accuracy

def get_dataset_feature(datasets_d, specification_d):
    rule_num, relation_num, df_num = [], [], []
    for file in sorted(os.listdir(datasets_d)):
        s = open(datasets_d + file, "r", encoding="utf-8").read()
        c = len([line for line in s.split("\n") if line.strip() != ""])
        rule_num.append(c-1)  # 去掉空行和标题
    for file in sorted(os.listdir(specification_d)):
        s = open(specification_d + file, "r", encoding="utf-8").read()
        c = len([line for line in s.split("\n") if line.strip() != ""])
        df_num.append(c)  # 去掉空行
    relation_num = [0,0,4,3,17]
    return rule_num, relation_num, df_num


def exp1():
    summary_f = open("exp1_data/table3.csv", "w", encoding="utf-8")
    summary_f.write("数据集,数据集特征,,,领域专家,,,非专家,,,ChatGPT,,,ChatGLM,,,LLSec,,\n")
    summary_f.write(",#规则,#依赖关系,#DF,#DF,FPI(%),时间(分),#DF,FPI(%),时间(分),#DF,FPI(%),时间(分),#DF,FPI(%),时间(分),#DF,FPI(%),时间(分)\n")
    
    ours_num, ours_acc = compute_acc_ours(our_dir="exp1_data/our_outputs", specification_dir = "exp1_data/specification")
    # exit(0)
    non_expert_num, non_expert_acc = compute_acc_non_expert(non_expert_dir = "exp1_data/non_expert_result", specification_dir = "exp1_data/specification")
    llm_num, llm_acc = compute_acc_llm(llm_dir="exp1_data/llm_result", specification_dir="exp1_data/specification")
    expert_num, expert_acc = compute_acc_expert(expert_dir="exp1_data/expert_result", specification_dir="exp1_data/specification")
    chatgpt_acc, chatglm_acc = llm_acc['chatgpt'], llm_acc['chatglm']
    chatgpt_num, chatglm_num = llm_num['chatgpt'], llm_num['chatglm']
    ours_acc = [round(acc, 4)*100 for acc in ours_acc]
    expert_acc = [round(acc, 4)*100 for acc in expert_acc]
    non_expert_acc = [round(acc, 4)*100 for acc in non_expert_acc]
    chatglm_acc = [round(acc, 4)*100 for acc in chatglm_acc]
    chatgpt_acc = [round(acc, 4)*100 for acc in chatgpt_acc]

    rule_num, relation_num, df_num = get_dataset_feature("exp1_data/dataset/", "exp1_data/specification/")
    expert_time = [33,40,35,40,50]
    non_expert_time = [75,73,85,70,74]
    chatgpt_time = [20,15,25,17,25]
    chatglm_time = [18,19,9,20,20]
    ours_time = [4,5,5,6,6]

    for i in range(5):
        summary_f.write(f"{i+1},{rule_num[i]},{relation_num[i]},{df_num[i]},{expert_num[i]},{expert_acc[i]},{expert_time[i]},{non_expert_num[i]},{non_expert_acc[i]},{non_expert_time[i]},{chatgpt_num[i]},{chatgpt_acc[i]},{chatgpt_time[i]},{chatglm_num[i]},{chatglm_acc[i]},{chatglm_time[i]},{ours_num[i]},{ours_acc[i]},{ours_time[i]}\n")
    summary_f.close()



if __name__ == "__main__":
    exp1()