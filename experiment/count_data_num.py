import json



def count_rule_filtering_data():
    datas_train = json.load(open("../data/rule_filtering_train_augmented.json", "r", encoding="utf-8"))
    datas_validate = json.load(open("../data/rule_filtering_validate.json", "r", encoding="utf-8"))
    print(f"规则筛选任务, 训练集大小: {len(datas_train)}, 验证集大小: {len(datas_validate)}")

    document_1 = json.load(open("../data/business_rules/json_for_rule_filtering/finish_深圳证券交易所债券交易规则.json", "r", encoding="utf-8"))
    print(f"1 document shot, 规则数量: {len(document_1)}")

def count_rule_extraction_data():
    datas_train = json.load(open("../data/rule_extraction_train_augmented.json", "r", encoding="utf-8"))
    datas_validate = json.load(open("../data/rule_extraction_validate.json", "r", encoding="utf-8"))
    print(f"规则抽取任务, 训练集大小: {len(datas_train)}, 验证集大小: {len(datas_validate)}")






if __name__ == "__main__":
    count_rule_filtering_data()
    count_rule_extraction_data()