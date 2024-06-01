# 主程序
from specification_generation.document_preprocess import preprocess
from specification_generation.rule_filtering import filtering
from specification_generation.rule_assembly import assembly
from specification_generation.rule_understanding import understanding, is_key_for_time, is_key_for_price, is_key_for_quantity
from specification_generation.rule_relation_mining import relation_mining
from specification_generation.generate_counterexample import counter_example
from transfer import mydsl_to_rules, rules_to_json_and_mydsl, mydsl_to_json
import json
import pprint
import time
import argparse


def main_filtering(input_file="rules_cache/深圳证券交易所债券交易规则.pdf", model_path="../train_rule_filtering_model/model/mengzi_rule_filtering", setting_file="rules_cache/setting.json"):
    # 读输入文件
    sci, setting = preprocess(nl_file=input_file)
    # 规则筛选
    sco = filtering(sci, model_path)
    # 保存结果
    json.dump(sco, open("rules_cache/sco.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(setting, open(setting_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    f = open("rules_cache/rules.txt", "w", encoding="utf-8")
    non_rule_num, rule_num, knowledge_num = 0, 0, 0
    for data in sco:
        if data["type"] == "0":
            non_rule_num += 1
        elif data["type"] == "1":
            f.write(f"{data['id']} {data['text']}\n")
            rule_num += 1
        elif data["type"] == "2":
            knowledge_num += 1
    f.close()
    print(f"规则筛选完成，包含句子数：{len(sco)}，其中规则有{rule_num}条，非规则有{non_rule_num}条，领域知识有{knowledge_num}条")
    return rule_num

def main(input_file="rules_cache/input.json", output_file="rules_cache/output.json", assembled_rule_file="rules_cache/BR.mydsl", after_understanding_json_file="rules_cache/UBR.json", after_understanding_mydsl_file="rules_cache/UBR.mydsl", after_relation_mining_json_file="rules_cache/RUBR.json", after_relation_mining_mydsl_file="rules_cache/RUBR.mydsl", knowledge_file="../data/knowledge.json", setting_file="rules_cache/setting.json", explicit_relation_file = "rules_cache/explicit_relation.json", implicit_relation_file = "rules_cache/implicit_relation.json", relation_file="rules_cache/relation.json"):
    begin_time = time.time()
    # 读输入文件
    inputs = json.load(open(input_file, "r", encoding="utf-8"))
    id_example = inputs[0]["id"]
    # 领域知识
    knowledge = json.load(open(knowledge_file, "r", encoding="utf-8"))
    # 环境变量
    setting = json.load(open(setting_file, "r", encoding="utf-8"))
    # 生成BR
    BRs = assembly(setting, inputs, knowledge)
    with open(assembled_rule_file, "w", encoding="utf-8") as f:
        f.write(BRs)

    # 读文件转换格式
    BRs = open(assembled_rule_file, "r", encoding="utf-8").read()
    defines, vars, rules = mydsl_to_rules.mydsl_to_rules(BRs)
    after_assemble_rule_num = len(rules)
    print(f"规则组合完成，包含规则数：{after_assemble_rule_num}，消耗时间{time.time()-begin_time}")

    # 规则理解
    begin_time = time.time()
    defines, vars, rules, understanding_knowledge_used_num = understanding(defines, vars, rules, knowledge)
    json.dump(rules, open(after_understanding_json_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json_rules = rules_to_json_and_mydsl.r2_to_json(rules)
    UBR = rules_to_json_and_mydsl.to_mydsl(json_rules)
    with open(after_understanding_mydsl_file, "w", encoding="utf-8") as f:
        f.write(UBR)
    after_understanding_rule_num, understanding_time = len(rules), time.time()-begin_time
    print(f"规则理解完成，包含规则数：{after_understanding_rule_num}，消耗时间{understanding_time}")

    # 规则间关系挖掘
    begin_time = time.time()
    defines, vars, rules, explicit_relation_count, implicit_relation_count, explicit_relation, implicit_relation, relation, relation_mining_knowledge_used_num = relation_mining(defines, vars, rules, knowledge, id_example)
    json.dump(rules, open(after_relation_mining_json_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json_rules = rules_to_json_and_mydsl.r3_to_json(rules)
    RUBR = rules_to_json_and_mydsl.to_mydsl(json_rules)
    with open(after_relation_mining_mydsl_file, "w", encoding="utf-8") as f:
        f.write(RUBR)
    json.dump(relation, open(relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(explicit_relation, open(explicit_relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(implicit_relation, open(implicit_relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    after_relation_mining_rule_num, relation_mining_time = len(rules), time.time() - begin_time
    print(f"规则间关系挖掘完成，包含规则数：{after_relation_mining_rule_num}，消耗时间{relation_mining_time}")
    print(f"包含关系数：{explicit_relation_count + implicit_relation_count}, 其中显式关系{explicit_relation_count}, 隐式关系{implicit_relation_count}")
    
    # 规则写成json格式
    test_scenarioes = mydsl_to_json.mydsl_to_json(RUBR)
    json.dump(test_scenarioes, open(output_file, "w" ,encoding="utf-8"), ensure_ascii=False, indent=4)
    dataflow_num = len(test_scenarioes)

    # 为规则生成反例
    # test_scenarioes = counter_example(test_scenarioes)
    # json.dump(test_scenarioes, open(output_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    # print(f"规则生成，包含规则数目: {len(test_scenarioes)}")
    return after_assemble_rule_num, after_understanding_rule_num, understanding_time, understanding_knowledge_used_num, after_relation_mining_rule_num, relation_mining_time, relation_mining_knowledge_used_num, explicit_relation_count + implicit_relation_count, dataflow_num


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="规约生成")
    parser.add_argument("--input_file", type=str, default="rules_cache/深圳证券交易所债券交易规则.pdf", help="输入文件")
    args = parser.parse_args()
    begin_time = time.time()
    main_filtering(input_file=args.input_file)
    time_consume = time.time() - begin_time
    print(f"规则过滤消耗时间: {time_consume}")
    # GPT task
    main(input_file="rules_cache/input.json")
    time_consume1 = time.time() - begin_time
    print(f"总共消耗时间: {time_consume1}")