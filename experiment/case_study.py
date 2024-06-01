from specification_generation.main import main_filtering, main
import argparse
import time


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="规约生成")
    parser.add_argument("--input_file", type=str, default="case_study_data/深圳证券交易所债券交易规则.pdf", help="输入文件")
    args = parser.parse_args()
    begin_time = time.time()
    testable_rule_num = main_filtering(input_file=args.input_file)
    filtering_time_consume = time.time() - begin_time
    print(f"规则过滤消耗时间: {filtering_time_consume}")
    # GPT task
    after_assemble_rule_num, after_understanding_rule_num, understanding_time, understanding_knowledge_used_num, after_relation_mining_rule_num, relation_mining_time, relation_mining_knowledge_used_num, relation_count, dataflow_num = main(input_file="case_study_data/input.json", output_file="case_study_data/output.json")
    time_consume = time.time() - begin_time
    print(f"总共消耗时间: {time_consume}")


    with open("case_study_data/table1.csv", "w", encoding="utf-8") as f:
        f.write("步骤,规则表示形式,业务规则数,处理时间(秒),涉及的领域知识数,规则关系数,规约中涉及的业务路径数\n")
        f.write(f"规则过滤,自然语言,{testable_rule_num},{round(filtering_time_consume, 2)},-,-,-\n")
        f.write(f"规则抽取,FBR形式,{after_assemble_rule_num},约3000,-,-,-\n")
        f.write(f"规则理解,FBR形式,{after_understanding_rule_num},{round(understanding_time, 2)},{understanding_knowledge_used_num},-,-\n")
        f.write(f"关系识别,FBR形式,{after_relation_mining_rule_num},{round(relation_mining_time, 2)},{relation_mining_knowledge_used_num},{relation_count},{dataflow_num}\n")