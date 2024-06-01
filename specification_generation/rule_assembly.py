import json
import re

def is_key_for_time(key):
    if key[-1] == "日" or key[-2:] == "时间" or "期" in key:
        return True
    return False

def is_key_for_quantity(key):
    if "量" in key or "数" in key:
        return True
    return False

def is_key_for_price(key):
    if ("价" in key or "基准" == key or "金额" in key) and "要素" not in key and "指令" not in key and "类型" not in key and "方式" not in key:
        return True
    return False

def get_clause_for_single_value(value_cache, op_cache, knowledge, key=None):
    v_key = list(value_cache.keys())[0]
    v_value = value_cache[v_key]

    if key is not None:
        if v_key == "时间" and is_key_for_time(key) or v_key == "数量" and is_key_for_quantity(key) or v_key == "价格" and is_key_for_price(key):

            if op_cache != "":
                op = op_cache
                op_cache = ""
            else:
                op = "is"
            if "时间" == v_key and ("前" in op or "后" in op) or v_key in ["数量", "价格"]:
                clause = f"{key} {op} \"{v_value}\""
            else:
                clause = f"{key} is \"{v_value}\""
            return clause, op_cache, True
        elif v_key not in ["时间", "数量", "价格"] and (not is_key_for_time(key) and not is_key_for_quantity(key) and not is_key_for_price(key) or len(re.findall(r"\d+", key)) == 0):
            clause = f"{key} is \"{v_value}\""
            op_cache = ""
            return clause, op_cache, True

    # key不存在或和value_cache不配对
    if v_key in ["时间", "数量", "价格"]:
        if op_cache != "":
            op = op_cache
            op_cache = ""
        else:
            op = "is"
        clause = f"{v_key} {op} \"{v_value}\""
    else:
        # 查找领域知识
        find = False
        for knowledge_key in list(knowledge.keys()):
            knowledge_value = knowledge[knowledge_key]
            if isinstance(knowledge_value, list) and v_value in knowledge_value:
                clause = f"{knowledge_key} is \"{v_value}\""
                find = True
                break
        if not find:
            clause = f"约束 is \"{v_value}\""
    return clause, op_cache, False

def generate_BR_clause(rule: dict, knowledge: list):
    clauses = []
    key_cache, value_cache = {}, {}
    op_cache = ""
    for key, value in rule.items():
        numbers = re.findall(f"\d+", key)
        if len(numbers) > 0:
            number = numbers[0]
            loc = key.find(number)
            key = key[:loc]
        # print(value, key_cache, value_cache, op_cache)
        if key == "id":
            continue
        if key not in ["时间", "数量", "价格", "op"] and "key" not in key and "value" not in key:
            if value == "失败":
                value = "不成功"
            if key == "交易方式" and "方式" in value:
                value = value[:value.find("方式")]
            clauses.append(f"{key} is \"{value}\"")
        elif key == "op":
            op_cache = value
        elif key == "时间":
            if not key_cache:  # 没有缓存的key
                if value_cache:  # 有缓存的value
                    clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge)
                    clauses.append(clause)
                value_cache = {key:value}
            else:  # 有缓存的key
                k_key = list(key_cache.keys())[0]
                k_value = key_cache[k_key]
                # 判断缓存的key和当前时间是否配对
                if is_key_for_time(k_value):
                    if op_cache != "":
                        op = op_cache
                        op_cache = ""
                    else:
                        op = "is"
                    clauses.append(f"{k_value} {op} \"{value}\"")
                else:
                    if value_cache:
                        clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                        if not if_add:
                            clauses.append(f"约束 is \"{k_value}\"")
                        clauses.append(clause)
                    value_cache = {key:value}
                key_cache = {}
        elif key == "数量":
            if not key_cache:  # 没有缓存的key
                if value_cache:  # 有缓存的value
                    clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge)
                    clauses.append(clause)
                value_cache = {key:value}
            else:  # 有缓存的key
                k_key = list(key_cache.keys())[0]
                k_value = key_cache[k_key]
                # 判断缓存的key和当前数量是否配对
                if is_key_for_quantity(k_value):
                    if op_cache != "":
                        op = op_cache
                        op_cache = ""
                    else:
                        op = "is"
                    clauses.append(f"{k_value} {op} \"{value}\"")
                else:
                    if value_cache:
                        clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                        if not if_add:
                            clauses.append(f"约束 is \"{k_value}\"")
                        clauses.append(clause)
                    value_cache = {key:value}
                key_cache = {}
        elif key == "价格":
            if not key_cache:  # 没有缓存的key
                if value_cache:  # 有缓存的value
                    clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge)
                    clauses.append(clause)
                value_cache = {key:value}
            else:  # 有缓存的key
                k_key = list(key_cache.keys())[0]
                k_value = key_cache[k_key]
                # 判断缓存的key和当前价格是否配对
                if is_key_for_price(k_value):
                    if op_cache != "":
                        op = op_cache
                        op_cache = ""
                    else:
                        op = "is"
                    clauses.append(f"{k_value} {op} \"{value}\"")
                else:
                    if value_cache:
                        clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                        if not if_add:
                            clauses.append(f"约束 is \"{k_value}\"")
                        clauses.append(clause)
                    value_cache = {key:value}
                key_cache = {}
        elif "key" in key:
            if not value_cache:
                key_cache = {key:value}
            else:
                if key_cache:
                    k_key = list(key_cache.keys())[0]
                    k_value = key_cache[k_key]
                    clause, assume_op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                    if if_add:
                        key_cache = {key:value}
                        value_cache = {}
                        op_cache = assume_op_cache
                        clauses.append(clause)
                        continue
                    else:
                        clauses.append(f"约束 is \"{k_value}\"")
                        key_cache = {}
                clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, value)
                clauses.append(clause)
                value_cache = {}
                key_cache = {}
                if not if_add:
                    key_cache = {key:value}
        else:  # "value" in key
            if not key_cache:
                if value_cache:
                    clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge)
                    clauses.append(clause)
                value_cache = {key:value}
            else:
                k_key = list(key_cache.keys())[0]
                k_value = key_cache[k_key]
                # 如果存在未使用的value，判断未使用的key、value是否配对
                if value_cache:
                    clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                    
                    clauses.append(clause)
                    if if_add:
                        value_cache = {key:value}
                        key_cache = {}
                        continue
                    else:
                        value_cache = {}

                value_cache = {key:value}
                clause, assume_op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
                if if_add:
                    clauses.append(clause)
                    op_cache = assume_op_cache
                    value_cache = {}
                else:
                    clauses.append(f"约束 is \"{k_value}\"")
                key_cache = {}
    
    if key_cache and value_cache:
        k_key = list(key_cache.keys())[0]
        k_value = key_cache[k_key]
        clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge, k_value)
        clauses.append(clause)
        if if_add:
            key_cache = {}
        value_cache = {}
    if key_cache:
        k_key = list(key_cache.keys())[0]
        k_value = key_cache[k_key]
        clauses.append(f"约束 is \"{k_value}\"")
        key_cache = {}
    if value_cache:
        clause, op_cache, if_add = get_clause_for_single_value(value_cache, op_cache, knowledge)
        clauses.append(clause)
        value_cache = {}

    return clauses




def compose_clause(id, clauses):
    BR = f"rule {id}\n"
    focus = []
    condition, consequence = "\tif ", "\tthen "
    have_op = False
    for clause in clauses:
        if "操作" in clause:
            have_op = True
        if is_key_for_time(clause.split(" ")[0]) and "时间" not in focus:
            focus.append("时间")
        if is_key_for_price(clause.split(" ")[0]) and "价格" not in focus:
            focus.append("价格")
        if is_key_for_quantity(clause.split(" ")[0]) and "数量" not in focus:
            focus.append("数量")
        if "订单连续性操作" not in focus and clause.split(" ")[0] == "操作":
            focus.append("订单连续性操作")
        
        if "最大申报数量" in clause:
            clause = "申报数量 " + " ".join(clause.split(" ")[1:])
        if "结果" not in clause:
            if "数量" in clause.split(" ")[0] and "and" in condition and "数量" in condition.split("and")[-2].strip().split(" ")[0]:
                condition = condition[:-6] + "," + clause.split(" ")[-1][1:] + " and "
            else:
                condition += clause + " and "
        else:
            consequence += clause + " and "
    if not have_op:
        condition += "操作 is \"申报\" and "
    if focus == []:
        focus.append("订单连续性操作")
    BR += f"focus {','.join(focus)}\n"
    BR += condition[:-5] + "\n"
    BR += consequence[:-5] + "\n\n"
    return BR


def add_define_elements(BRs, setting):
    for key in list(setting.keys()):
        BRs += f"define {key} = {setting[key]}\n"
    BRs += "\n\n"
    return BRs

def assembly(setting, rules, knowledge):
    BRs = ""
    BRs = add_define_elements(BRs, setting)
    for rule in rules:
        id = rule['id']
        clauses = generate_BR_clause(rule, knowledge)
        BR = compose_clause(id, clauses)
        BRs += BR
    return BRs



if __name__ == "__main__":
    setting = json.load(open("rules_cache/setting.json", "r", encoding="utf-8"))
    input_rules = json.load(open("rules_cache/input.json", "r", encoding="utf-8"))
    knowledge = json.load(open("../data/knowledge.json", "r", encoding="utf-8"))
    BRs = assembly(setting, input_rules, knowledge)
    with open("rules_cache/BR.mydsl", "w", encoding="utf-8") as f:
        f.write(BRs)