import json
import copy
from specification_generation.rule_assembly import is_key_for_price, is_key_for_time, is_key_for_quantity

def counter_example(test_scenarioes):
    # 为时间、数量、价格取反
    new_scenarioes = []
    for scenario in test_scenarioes:
        new_scenarioes.append(copy.deepcopy(scenario))
        new_scenarioes[-1]['id'] = new_scenarioes[-1]['id'] + "_1"
        key_for_time_quantity_price = []
        for key, value in scenario.items():
            if is_key_for_time(key) or is_key_for_price(key) or is_key_for_quantity(key):
                key_for_time_quantity_price.append(key)
        # 合并时间
        array = []
        time_key = ""
        for key in key_for_time_quantity_price:
            if is_key_for_time(key):
                time_key += key + ","
            else:
                array.append(key)
        if time_key != "":
            array.append(time_key[:-1])
        key_for_time_quantity_price = array
        # 二进制，特殊处理时间
        for i in range(1, 2**len(key_for_time_quantity_price), 1):
            sc = copy.deepcopy(scenario)
            for j in range(len(key_for_time_quantity_price)):
                index = 1 << j
                if i & index > 0:
                    if is_key_for_time(key_for_time_quantity_price[j]):
                        # 时间并集
                        time_union = ""
                        for key in key_for_time_quantity_price[j].split(","):
                            del sc[key]
                            value = scenario[key]
                            time_union += value + "、"
                        sc['交易时间'] = "非" + time_union[:-1]
                    else:
                        sc[key_for_time_quantity_price[j]] = "非" + scenario[key_for_time_quantity_price[j]]
            sc['id'] = sc['id'] + "_" + str(i+1)
            if sc['结果'] == "成功":
                sc['结果'] = "不成功"
                if "结果状态" in sc and "状态" in sc:
                    sc['结果状态'] = sc['状态']
            else:
                sc['结果'] = "成功"
            new_scenarioes.append(sc)

    return new_scenarioes




if __name__ == "__main__":
    test_scenarioes = json.load(open("rules_cache/JRUBR.json", "r", encoding="utf-8"))
    test_scenarioes = counter_example(test_scenarioes)
    json.dump(test_scenarioes, open("rules_cache/output.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)