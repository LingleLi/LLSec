from specification_generation.main import *
import time
import os


def generate_specification():
    for file in sorted(os.listdir("exp2_data/our_inputs")):
        if "input.json" in file:
            # if "data1" not in file:
            #     continue
            print(f"处理文件{file}")
            filename = file[:5]
            begin_time = time.time()

            input_file="exp2_data/our_inputs/" + file
            output_file="exp2_data/our_outputs/" + filename + "_output.json"
            output_file_without_knowledge = "exp2_data/our_outputs/" + filename + "_output_without_knowledge.json"
            relation_file = "exp2_data/our_outputs/" + filename + "_relation.json"
            setting_file="exp2_data/our_inputs/setting.json"
            explicit_relation_file="exp2_data/our_outputs/" + filename + "_explicit_relation.json"
            implicit_relation_file="exp2_data/our_outputs/" + filename + "_implicit_relation.json"
            knowledge_file = "../data/knowledge.json"
            assembled_rule_file="rules_cache/BR.mydsl"
            after_understanding_json_file="rules_cache/UBR.json"
            after_understanding_mydsl_file="rules_cache/UBR.mydsl"
            after_relation_mining_json_file="rules_cache/RUBR.json"
            after_relation_mining_mydsl_file="rules_cache/RUBR.mydsl"

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
            print(f"规则组合完成，包含规则数：{len(rules)}，消耗时间{time.time()-begin_time}")

            # 规则写成json格式
            test_scenarioes = mydsl_to_json.mydsl_to_json(BRs)
            json.dump(test_scenarioes, open(output_file_without_knowledge, "w" ,encoding="utf-8"), ensure_ascii=False, indent=4)

            # 规则理解
            defines, vars, rules, _ = understanding(defines, vars, rules, knowledge)
            json.dump(rules, open(after_understanding_json_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
            json_rules = rules_to_json_and_mydsl.r2_to_json(rules)
            UBR = rules_to_json_and_mydsl.to_mydsl(json_rules)
            with open(after_understanding_mydsl_file, "w", encoding="utf-8") as f:
                f.write(UBR)
            print(f"规则理解完成，包含规则数：{len(rules)}，消耗时间{time.time()-begin_time}")

            # # 规则写成json格式
            # test_scenarioes = mydsl_to_json.mydsl_to_json(UBR)
            # json.dump(test_scenarioes, open(output_file_without_relation, "w" ,encoding="utf-8"), ensure_ascii=False, indent=4)

            # 规则间关系挖掘
            defines, vars, rules, explicit_relation_count, implicit_relation_count, explicit_relation, implicit_relation, relation, _ = relation_mining(defines, vars, rules, knowledge, id_example)
            json.dump(rules, open(after_relation_mining_json_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
            json_rules = rules_to_json_and_mydsl.r3_to_json(rules)
            RUBR = rules_to_json_and_mydsl.to_mydsl(json_rules)
            with open(after_relation_mining_mydsl_file, "w", encoding="utf-8") as f:
                f.write(RUBR)
            json.dump(relation, open(relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
            json.dump(explicit_relation, open(explicit_relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
            json.dump(implicit_relation, open(implicit_relation_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
            print(f"规则间关系挖掘完成，包含规则数：{len(rules)}，消耗时间{time.time()-begin_time}")
            print(f"包含关系数：{explicit_relation_count + implicit_relation_count}, 其中显式关系{explicit_relation_count}, 隐式关系{implicit_relation_count}")
            
            # 规则写成json格式
            test_scenarioes = mydsl_to_json.mydsl_to_json(RUBR)
            json.dump(test_scenarioes, open(output_file, "w" ,encoding="utf-8"), ensure_ascii=False, indent=4)


            time_consume = time.time() - begin_time
            print(f"《{filename}》总共消耗时间: {time_consume}")


if __name__ == "__main__":
    generate_specification()