import copy
import pprint
import re
from specification_generation.rule_assembly import is_key_for_time, is_key_for_quantity, is_key_for_price

knowledge_used = {}


def understanding(defines, vars, rules, preliminaries):
    """
    规则组合函数, 包含:
    1. 组合明显嵌套的规则
    2. 补全单规则相关的字段
    3. 将规则中的时间替换为具体的时间（开盘集合匹配阶段）
    4. 补全"其他"交易方式等
    5. 申报数量<100...0和其他规则的组合, 同一rule下subrule的组合
    6. 除本规则规定的不接受撤销申报的时间段外，其他接受申报的时间内怎样怎样
    7. 没有then就删掉，这是另一个去重步
    """
    id_example = list(rules.keys())[0]
    knowledge_used.clear()

    # 组合明显嵌套的规则
    vars, rules = compose_nested_rules(vars, rules)

    # 必须交易阶段相同，一个是订单连续性操作，一个是交易时间，组合
    vars, rules = compose_same_stage(vars, rules)
    # "其他"补全
    vars, rules = supply_other_rules(vars, rules, preliminaries)

    # 统一规则下的子规则组合，申报数量<100...0和其他规则的组合
    vars, rules = subrule_compose(vars, rules, id_example)

    # 补全单规则相关的字段
    vars, rules = supply_rules_on_prelim(defines, vars, rules, preliminaries)

    # 除本规则规定的不接受撤销申报的时间段外，其他接受申报的时间内怎样怎样
    vars, rules = compute_other_time_in_rules(vars, rules, preliminaries)
    # 没有then就删掉
    vars, rules = delete_then(vars, rules)

    # 后处理
    vars, rules = post_process(vars, rules)


    # 打印中间结果
    # with open(f"rules/r2_{rule_name}.txt", "w", encoding="utf-8") as f:
    #     f.write(pprint.pformat(rules))
    # print(f"R2包含的规则数：{len(vars.keys())}")
    print(f"规则理解阶段用到的领域知识数：{len(knowledge_used)}")
    
    return defines, vars, rules, len(knowledge_used)









def judge_rule_conflict(rule1, rule2):
    for c1 in rule1['constraints']:
        conflict = False
        for c2 in rule2['constraints']:
            if c1['key'] == c2['key'] and c1['key'] in ["交易市场", "交易品种", "交易方式", "交易方向"]:
                if c1['value'] == c2['value']:
                    conflict = False
                else:
                    conflict = True
                    break
        if conflict:
            return True
    return False


def compose_nested_rules(vars, rules):
    # 遍历，找到所有结合规则
    rule_to_del = []
    for rule_id in list(rules.keys()):
        rule = rules[rule_id]
        var = vars[rule_id]
        for c in rule['constraints']:
            if c['key'] == '结合规则':
                rule_to_del.append(rule_id)
                # 找到要结合的规则的id
                if len(re.findall(r"\d+", c['value']))>0:
                    loc1 = c['value'].find("第")
                    loc2 = c['value'].find("条")
                    compose_rule_id = c['value'][loc1+1:loc2]
                else:
                    compose_rule_id = c['value']
                # 找到要结合的规则，要求不互相冲突
                for rule_id1 in list(rules.keys()):
                    if compose_rule_id in rule_id1 and not judge_rule_conflict(rule, rules[rule_id1]):
                        # 构建结合后的规则
                        new_rule = {
                            "constraints": copy.deepcopy(rules[rule_id1]['constraints']),
                            "focus": list(set(rule['focus'] + rules[rule_id1]['focus'])),
                            "results": copy.deepcopy(rule['results'])
                        }
                        for ci in rule['constraints']:
                            if ci not in new_rule['constraints'] and ci['key'] != "结合规则":
                                new_rule['constraints'].append(ci)
                        new_id = rule_id + "," + rule_id1
                        rules[new_id] = new_rule
                        var = {}
                        for ci in new_rule['constraints']:
                            var[ci['key']] = []
                        vars[new_id] = var

    for rule_id in rule_to_del:
        del rules[rule_id]
        del vars[rule_id]

    return vars, rules



def construct_tree(preliminaries, jypz):
    arr = []
    for key in list(preliminaries.keys()):
        if "交易方式" in key and jypz in key:
            knowledge_used[key] = preliminaries[key]
            for value in preliminaries[key]:
                arr.append(["交易方式", value])
    end = False
    while not end:
        end = True
        new_arr = []
        for kv in arr:
            father_key, father_value = kv[-2], kv[-1]
            add_old_kv = True
            arr_local = []
            for key in list(preliminaries.keys()):
                # 大宗交易 必须在 大宗交易交易方式 的开头才行
                if (key.find(father_value) == 0 or len(kv)>=4 and key.find(kv[-3])==0 and father_value in key) and isinstance(preliminaries[key], list):
                    # 如果当前要添加的key、value已存在，跳过
                    if key in kv:
                        continue
                    find = False
                    knowledge_used[key] = preliminaries[key]
                    for value in preliminaries[key]:
                        if value in kv:
                            find = True
                            break
                    if find:
                        continue
                    
                    # 添加
                    if len(arr_local) == 0:
                        if "指令" in key or "要素" in key or "内容" in key:
                            if len(kv)>=4 and key.find(kv[-3])==0 and father_value in key:
                                knowledge_used[key] = preliminaries[key]
                                arr_local.append(copy.deepcopy(kv) + [key, ",".join(preliminaries[key])])
                                end = False
                                add_old_kv = False
                        else:
                            knowledge_used[key] = preliminaries[key]
                            for value in preliminaries[key]:
                                new_kv = copy.deepcopy(kv)
                                new_kv += [key, value]
                                arr_local.append(new_kv)
                            end = False
                            add_old_kv = False
                    else:
                        if "指令" in key or "要素" in key or "内容" in key:
                            
                            if len(kv)>=4 and key.find(kv[-3])==0 and father_value in key:
                                for kv1 in arr_local:
                                    kv1 += [key, ",".join(preliminaries[key])]
                                    knowledge_used[key] = preliminaries[key]
                                end = False
                                add_old_kv = False
                        else:
                            a = []
                            multi_num = len(preliminaries[key])
                            for _ in range(multi_num):
                                a += copy.deepcopy(arr_local)
                            arr_local = a
                            knowledge_used[key] = preliminaries[key]
                            for i, value in enumerate(preliminaries[key]):
                                for kvi in arr_local[int(len(arr_local)/multi_num*i):int(len(arr_local)/multi_num*(i+1))]:
                                    kvi += [key, value]
                            end = False
                            add_old_kv = False
                    
            if add_old_kv:
                arr_local.append(kv)
            new_arr += arr_local
        arr = copy.deepcopy(new_arr)
    # pprint.pprint(arr)
    return arr



def supply_rules_on_prelim(defines, vars, rules, preliminaries):
    # 如果规则中没有"单独可测试规则要素"，添加
    elements = preliminaries["单独可测试规则要素"]
    knowledge_used["单独可测试规则要素"] = elements
    tree = {}
    # beside_key = ["交易品种", "操作", "操作部分", "事件", "状态", "操作人", "条件", "结合规则"]

    for element in elements:
        if element == "交易方向":
            # 交易操作
            to_delete = []
            for rule_id in list(rules.keys()):
                index = 1
                rule = rules[rule_id]
                find = False
                for c in rule['constraints']:
                    if c['key'] == '操作':  # 认购(买)、申购(买)、赎回(卖)、申购(买卖)、竞买(卖)、应价(买)
                        if '买入' in c['value'] or "认购" in c['value'] or "申购" in c['value'] or "应价" in c['value']:
                            rule['constraints'].append({"key":"交易方向","operation":"is","value":"买入"})
                            vars[rule_id]['交易方向'] = []
                            find = True
                            break
                        if '卖出' in c['value'] or "赎回" in c['value'] or "竞买" in c['value']:
                            rule['constraints'].append({"key":"交易方向","operation":"is","value":"卖出"})
                            vars[rule_id]['交易方向'] = []
                            find = True
                            break
                if not find:
                    to_delete.append(rule_id)
                    knowledge_used[element] = preliminaries[element]
                    for direction in preliminaries[element]:
                        new_rule = copy.deepcopy(rule)
                        new_var = copy.deepcopy(vars[rule_id])
                        new_rule['constraints'].append({"key":element, "operation":"is", "value":direction})
                        new_var[element] = []
                        rules[f"{rule_id}.{index}"] = new_rule
                        vars[f"{rule_id}.{index}"] = new_var
                        index += 1
            for rule_id in to_delete:
                del vars[rule_id]
                del rules[rule_id]
        if element in defines or element == "交易品种":  # 交易品种/交易市场
            old_element = element
            if element in defines:
                e = defines[element][0]
                if e == "证券":
                    e = preliminaries['交易品种']
                    knowledge_used["交易品种"] = e
            else:
                e = preliminaries['交易品种']
                knowledge_used["交易品种"] = e
            old_e = e
            to_delete = []
            for rule_id in list(rules.keys()):
                element = old_element
                e = old_e
                rule = rules[rule_id]
                # if "第五十二条" in rule_id:
                #     print(rule, element)
                find = False
                jypz = ""
                for c in rule['constraints']:
                    if c['key'] == element:  # 只有交易品种才可能走这个分支
                        jypz = c['value']
                        new_jypz = ""
                        if "创业" in jypz:
                            new_jypz = "创业板"
                        else:
                            if "债" in jypz:
                                new_jypz = "债券"
                            if "股" in jypz:
                                new_jypz = "股票"
                            if "基金" in jypz or "ET" in jypz or "TF" in jypz or "LO" in jypz or "OF" in jypz:
                                new_jypz = "基金"
                            if new_jypz == "":
                                new_jypz = jypz
                        
                        if jypz != new_jypz and jypz != "基金份额":
                            c['value'] = new_jypz
                            rule['constraints'].append({"key":f"{new_jypz}品种", "operation":"is", "value":jypz})
                            vars[rule_id][f"{new_jypz}品种"] = []
                        find = True

                        if (jypz == new_jypz or jypz == "基金份额") and f"{new_jypz}品种" in preliminaries:
                            e = preliminaries[f"{new_jypz}品种"]
                            knowledge_used[f"{new_jypz}品种"] = e
                            element = f"{new_jypz}品种"
                            find = False
                        break
                if not find or jypz == "证券":
                    if jypz == "证券":
                        e = preliminaries['交易品种']
                        knowledge_used['交易品种'] = e
                    if isinstance(e, str):
                        rule['constraints'].append({"key":element, "operation":"is", "value":e})
                        vars[rule_id][element] = []
                        # 继续细化，补充e的具体品种
                        if element == "交易品种" and f"{e}品种" in preliminaries:
                            element = f"{e}品种"
                            knowledge_used[f"{e}品种"] = preliminaries[f"{e}品种"]
                            e = preliminaries[f"{e}品种"]
                    if isinstance(e, list):
                        for eidx, ei in enumerate(e):
                            new_id = f"{rule_id}.{eidx+1}"
                            new_rule = copy.deepcopy(rule)
                            if jypz == "证券":
                                for c in new_rule['constraints']:
                                    if c['key'] == element:
                                        c['value'] = ei
                            else:
                                new_rule['constraints'].append({"key":element, "operation":"is", "value":ei})
                            rules[new_id] = new_rule
                            new_var = copy.deepcopy(vars[rule_id])
                            new_var[element] = []
                            vars[new_id] = new_var
                        to_delete.append(rule_id)
            for rule_id in to_delete:
                del rules[rule_id]
                del vars[rule_id]
        if element == "交易方式":
            # 获取交易品种，得到对应的交易方式，填入
            to_delete = []
            for rule_id in list(rules.keys()):
                rule = rules[rule_id]
                # 查找交易品种
                for c in rule['constraints']:
                    if c['key'] == "交易品种":
                        jypz = c['value']
                        new_jypz = ""
                        if "创业" in jypz:
                            new_jypz = "创业板"
                        else:
                            if "债" in jypz:
                                new_jypz = "债券"
                            if "股" in jypz:
                                new_jypz = "股票"
                            if "基金" in jypz or "ET" in jypz or "TF" in jypz or "LO" in jypz or "OF" in jypz:
                                new_jypz = "基金"
                            if new_jypz == "":
                                new_jypz = jypz
                        jypz = new_jypz
                        break
                if jypz in tree:
                    tree_local = tree[jypz]
                else:
                    tree_local = construct_tree(preliminaries, jypz)
                    tree[jypz] = tree_local
                index = 1
                
                for ti in tree_local:
                    new_rule = copy.deepcopy(rule)
                    new_var = copy.deepcopy(vars[rule_id])
                    conflict = False
                    for i in range(0, len(ti), 2):
                        find_value = False
                        find_key = False
                        for c in rule['constraints']:
                            if c['value'] == ti[i+1]:
                                find_value = True
                                break
                            if c['key'] == ti[i]:
                                find_key = True
                                break
                        if find_value:  # 找到了相同的value，这个value就不用加了
                            continue
                        if find_key and c['value'] not in ti:  # 找到了key，但value不同，冲突，并且value不在ti中这个ti不继续加了
                            conflict = True
                            break
                        if c['value'] in ti:
                            for nc in new_rule['constraints']:
                                if nc['value'] == c['value']:
                                    nc['key'] = ti[ti.index(c['value'])-1]
                                    new_var[c['key']] = []
                                    break
                            
                        # 将value加入规则中
                        new_rule['constraints'].append({"key": ti[i], "operation": "is", "value": ti[i+1]})
                        new_var[ti[i]] = []
                        
                    if not conflict:
                        new_id = f"{rule_id}.{index}"
                        index += 1
                        rules[new_id] = new_rule
                        vars[new_id] = new_var
                        if rule_id not in to_delete:
                            to_delete.append(rule_id)
            for id in to_delete:
                del rules[id]
                del vars[id]
    
    for rule_id in list(rules.keys()):
        rule = rules[rule_id]
        for c in rule['constraints']:
            if c['key'] in preliminaries:
                knowledge_used[c['key']] = preliminaries[c['key']]
            if c['value'] in preliminaries:
                knowledge_used[c['value']] = preliminaries[c['value']]

    return vars, rules




def compose_same_stage(vars, rules):
    rule_to_delete = []
    for i, rule_id1 in enumerate(list(rules.keys())):
        rule1 = rules[rule_id1]
        new_rule = copy.deepcopy(rule1)
        new_id = rule_id1
        for idx, c1 in enumerate(rule1['constraints']):
            if c1['key'] == "时间" and c1['operation'] == "is":
                time_key = c1['value']
                if "阶段" in time_key:
                    time_key = time_key[:time_key.find("阶段")]
                if "时间" in time_key:
                    time_key = time_key[:time_key.find("时间")]

                for j, rule_id2 in enumerate(rules):
                    if i == j:
                        continue
                    rule2 = rules[rule_id2]
                    find = False
                    for c2 in rule2['constraints']:
                        if time_key in c2['key'] and is_key_for_time(c2['key']):
                            new_rule['constraints'][idx]['operation'] = "in"
                            new_rule['constraints'][idx]['value'] = copy.deepcopy(c2['value'])
                            new_rule['focus'] = list(set(new_rule['focus'] + rule2['focus']))
                            if rule_id2 not in new_id.split(","):
                                new_id += "," + rule_id2
                            find = True
                            break
                    if find:
                        break
        
        if new_id != rule_id1:
            rules[new_id] = new_rule
            var = copy.deepcopy(vars[rule_id1])
            vars[new_id] = var
            rule_to_delete.append(rule_id1)

    for rule_id in rule_to_delete:
        del rules[rule_id]
        del vars[rule_id]
    return vars, rules





def supply_other_rules(vars, rules, preliminaries):
    to_delete = []
    keys = list(vars.keys())
    for rule_id in keys:
        rule = rules[rule_id]
        for c in rule["constraints"]:
            if "其他" in c["value"]:  # 其他申报类型
                want = c['value'][c['value'].find("其他")+2:]
                have = []
                for rule_id1 in keys:
                    # changed FIXME
                    if rule_id == rule_id1 and rule_id != rule_id1:
                        for c0 in rules[rule_id1]["constraints"]:
                            if c0['key'] == c["key"] and c0['value'] != c["value"] and c0["value"] not in have:
                                have.append(c0["value"])
                                break
                # 取反
                if want not in preliminaries:
                    continue
                c_key = preliminaries[want]
                knowledge_used[want] = c_key
                not_have = []
                for k in c_key:
                    if k not in have:
                        not_have.append(k)
                for i, k in enumerate(not_have):
                    new_rule = copy.deepcopy(rule)
                    new_var = copy.deepcopy(vars[rule_id])
                    new_id = f"{rule_id}.{i+1}"
                    for c1 in new_rule["constraints"]:
                        if c1["key"] == c["key"]:
                            c1["value"] = k
                            break
                    rules[new_id] = new_rule
                    vars[new_id] = new_var
                to_delete.append(rule_id)
    
    for id in to_delete:
        del vars[id]
        del rules[id]


    return vars, rules




def judge_variety_same(v1, v2):
    if v1 == v2:
        return True, v1
    
    ori_v = ""
    if v1 in ["债券", "股票", "基金", "创业板"]:
        ori_v = v1
        if v2 in ["债券", "股票", "基金", "创业板"]:
            return False, ""
        else:
            v = v2
    else:
        if v2 in ["债券", "股票", "基金", "创业板"]:
            ori_v = v2
            v = v1
        else:
            return False, ""
    
    new_v = ""
    if "创业" in v:
        new_v = "创业板"
    else:
        if "债" in v:
            new_v = "债券"
        if "股" in v:
            new_v = "股票"
        if "基金" in v or "ET" in v or "TF" in v or "LO" in v or "OF" in v:
            new_v = "基金"
        if new_v == "":
            new_v = v

    if new_v == ori_v:
        if ori_v == v1:
            return True, v2
        else:
            return True, v1
    else:
        return False, ""

def same_fatherid(id1, id2, id_example):
    if "_" in id_example:
        return id1.split("_")[0] == id2.split("_")[0]
    elif "第" in id_example and "条" in id_example:
        return id1.split(".")[0] == id2.split(".")[0]
    else:
        point_count = id_example.count(".")
        return ".".join(id1.split(".")[:point_count]) == ".".join(id2.split(".")[:point_count])

def subrule_compose(vars, rules, id_example):
    # 同一rule下的subrule组合
    # 多组合
    to_delete = []
    while(1):
        keys = list(rules.keys())
        for i in range(len(keys)):
            for j in range(len(keys)):
                # 避免重复，并且要求属于同一个rule
                if j <= i:
                    continue
                if not same_fatherid(keys[i], keys[j], id_example):
                    # 如果是数量，则不跳过
                    find_num=False
                    for c in rules[keys[i]]['constraints']:
                        if is_key_for_quantity(c['key']):
                            find_num = True
                            break
                    if not find_num:
                        continue
                    find_num = False
                    for c in rules[keys[j]]['constraints']:
                        if is_key_for_quantity(c['key']):
                            find_num = True
                            break
                    if not find_num:
                        continue
                # 避免冲突
                new_rule = copy.deepcopy(rules[keys[i]])
                conflict = False
                for c in rules[keys[j]]["constraints"]:
                    # 时间
                    if is_key_for_time(c['key']):
                        conflict = True
                        break
                    # 少于...一次性申报
                    # if "一次性" in c['value']:
                    #     conflict = True
                    #     break
                    find = False
                    for c1 in new_rule["constraints"]:
                        if is_key_for_time(c1['key']):
                            conflict = True
                            break
                        # if "一次性" in c1['value']:
                        #     conflict = True
                        #     break
                        if c['key'] == c1['key'] and c['operation'] == "is":
                            if c['key'] == "交易品种":
                                find = True
                                variety_same, small_variety= judge_variety_same(c['value'], c1['value'])
                                if not variety_same:
                                    conflict = True
                                else:
                                    if c1['value']!=small_variety:
                                        c1['value'] = small_variety
                                break
                            if is_key_for_quantity(c['key']) and is_key_for_quantity(c1['key']) or is_key_for_price(c['key']) and is_key_for_price(c1['key']):
                                if c['value'] == c1['value']:
                                    find = True
                            else:
                                find = True
                                
                                if c['value'] != c1['value'] and not (c['key'] == "操作" and c1['key'] == "操作" and (c['value'] in ["买入", "申报"] and c1['value'] in ["买入", "申报"] or c['value'] in ["卖出","申报"] and c1['value'] in ["卖出","申报"])):
                                    conflict = True
                            break
                    if conflict:
                        break
                    if not find:
                        new_rule["constraints"].append(copy.deepcopy(c))
                if conflict:
                    continue
                # 合并results, focus
                if "results" not in new_rule and "results" in rules[keys[j]]:
                    new_rule["results"] = copy.deepcopy(rules[keys[j]]["results"])
                elif "results" in new_rule and "results" in rules[keys[j]]:
                    for r in rules[keys[j]]['results']:
                        find = False
                        for r1 in new_rule['results']:
                            if r['key'] == r1['key']:
                                find = True
                                break
                        if not find:
                            new_rule['results'].append(copy.deepcopy(r))
                for f in rules[keys[j]]['focus']:
                    if f not in new_rule['focus']:
                        new_rule['focus'].append(f)
                if "数量" in new_rule['focus'] and "价格" in new_rule['focus']:  # 禁止价格和数量规则组合
                    continue
                if keys[i] not in to_delete:
                    to_delete.append(keys[i])
                if keys[j] not in to_delete:
                    to_delete.append(keys[j])
                keyi_list = keys[i].split(",")
                keyj_list = keys[j].split(",")
                for kj in keyj_list:
                    if kj not in keyi_list:
                        keyi_list.append(kj)
                keyi_list = sorted(keyi_list)

                del_index = []
                for pi, xi in enumerate(keyi_list):  # 3.1.5.1, 3.1.5
                    point_num=0
                    start = 0
                    pl = xi.find(".", start)
                    while(pl!=-1 and point_num <= 2):
                        point_num += 1
                        start = pl+1
                        pl = xi.find(".", start)
                    if pl == -1:
                        rule_class1 = xi
                    else:
                        rule_class1 = xi[:pl]
                    
                    for pj, xj in enumerate(keyi_list):
                        if pj <= pi:
                            continue
                        point_num=0
                        start = 0
                        pl = xj.find(".", start)
                        while(pl!=-1 and point_num <= 2):
                            point_num += 1
                            start = pl+1
                            pl = xj.find(".", start)
                        if pl == -1:
                            rule_class2 = xj
                        else:
                            rule_class2 = xj[:pl]
                        if rule_class1 == rule_class2:
                            if len(xi) > len(xj):
                                del_index.append(pi)
                            else:
                                del_index.append(pj)
                key_list = []
                for pi, xi in enumerate(keyi_list):
                    if pi not in del_index:
                        key_list.append(xi)

                    
                new_id = ",".join(key_list)
                rules[new_id] = new_rule


                # 更新vars
                new_var = copy.deepcopy(vars[keys[i]])
                for v in list(vars[keys[j]].keys()):
                    if v not in list(new_var.keys()):
                        new_var[v] = []
                vars[new_id] = new_var

        if len(to_delete) == 0:
            break
        for id in to_delete:
            del vars[id]
            del rules[id]
        to_delete = []
    return vars, rules




def compute_other_time_in_rules(vars, rules, preliminaries):
    # 处理“交易阶段 is "除本规则规定的不接受撤销申报的时间段外，其他接受申报的时间内"”这句话
    # 输入
# '3.3.12.1.1.1': {'constraints': [{'key': '时间',
#                                    'operation': 'is',
#                                    'value': '除本规则规定的不接受撤销申报的时间段外，其他接受申报的时间内'},
#                                   {'key': '操作',
#                                    'operation': 'is',
#                                    'value': '撤销'},
#                                   {'key': '操作部分',
#                                    'operation': 'is',
#                                    'value': '未成交的申报'},
#                                   {'key': '交易市场',
#                                    'operation': 'is',
#                                    'value': '深圳证券交易所'},
#                                   {'key': '交易方式',
#                                    'operation': 'is',
#                                    'value': '匹配成交'},
#                                   {'key': '交易品种',
#                                    'operation': 'is',
#                                    'value': '债券'},
#                                   {'key': '交易方向',
#                                    'operation': 'is',
#                                    'value': '买入'}],
#                   'focus': ['订单连续性操作'],
#                   'results': [{'else': '不成功', 'key': '结果', 'value': '成功'}],
#                   'rule_class': ['3.3.12']}
    # 输出
    # 规则添加交易时间 in {[9:15-9:20],[9:30-11:30]}，删除交易阶段

    keys = list(rules.keys())
    for i in range(len(keys)):
        rule = rules[keys[i]]
        new_constraints = copy.deepcopy(rule['constraints'])
        for cnt, c in enumerate(rule['constraints']):
            if c['key'] == '交易阶段' and "除" in c['value'] and "外" in c['value'] and "其他" in c['value']:
                # 处理，添加交易时间
                sentence = c['value'].split('外')
                # preliminaries = json.load(open("preliminaries.json", "r", encoding="utf-8"))
                elements = preliminaries["单独可测试规则要素"]
                # 首先处理除...外，这中间有两个点用于匹配，一是操作“撤销”，二是结果“失败”
                # 遍历所有其他规则，寻找这两个点
                except_time = ""  # 除了这个时间段，要找的结果就是这个时间
                for j in range(len(keys)):
                    if j == i:
                        continue
                    other_rule = rules[keys[j]]
                    # 首先判断是否冲突，冲突的话下一个
                    conflict = False
                    for ic in rule['constraints']:
                        for jc in other_rule['constraints']:
                            if ic['key'] == jc['key'] and ic['key'] in elements:
                                if ic['value'] != jc['value']:
                                    conflict = True
                                break
                        if conflict:
                            break
                    if conflict:
                        continue
                    # 接下来寻找是否满足sentence[0]
                    find = False
                    for jc in other_rule['constraints']:
                        if jc['key'] == "交易操作" and '撤销' in jc['value'] and 'results' in other_rule:
                            # if "撤销" + jc['value'] in sentence[0]:  # 要的是撤销申报，而jc['value']是申报
                            #     break
                            for jr in other_rule['results']:
                                if jr['value'] == "失败":
                                    find = True
                                    break
                            if find:
                                break
                    if find:
                        for jc in other_rule['constraints']:
                            if jc['key'] == '交易时间':
                                except_time = jc['value'][1:-1]
                                break
                        break
                # 只有匹配成交才有except_time，其他都是空
                # 其他接受申报的时间内，有两个关键点，一个是操作“申报”，一个是结果“接受”
                expect_time = ""  # 本轮搜索期望找到的时间
                for j in range(len(keys)):
                    if j == i:
                        continue
                    other_rule = rules[keys[j]]
                    # 首先判断是否冲突，冲突的话下一个
                    conflict = False
                    for ic in rule['constraints']:
                        for jc in other_rule['constraints']:
                            if ic['key'] == jc['key'] and ic['key'] in elements:
                                if ic['value'] != jc['value']:
                                    conflict = True
                                break
                        if conflict:
                            break
                    if conflict:
                        continue
                    # 接下来寻找是否满足sentence[1]
                    find = False
                    for jc in other_rule['constraints']:
                        # 债券交易申报
                        if jc['key'] == "交易操作" and '申报' in jc['value'] and 'results' in other_rule:
                            for jr in other_rule['results']:
                                if jr['value'] == '成功':
                                    find = True
                                    break
                            if find:
                                break
                    if find:  # 注意，这里和上面的except_time的find不同，这里可能有多条时间
                        for jc in other_rule['constraints']:
                            if jc['key'] == '交易时间':
                                expect_time += jc['value'][1:-1] + ","
                                break
                # 现在有了期望的时间expect_time，有了排除的时间except_time，计算差
                expect_time = expect_time[:-1]
                real_time = expect_time
                if except_time != "":
                    except_begin, except_end = except_time[1:-1].split("-")
                    if len(except_begin) == 4:
                        except_begin = '0' + except_begin
                    if len(except_end) == 4:
                        except_end = '0' + except_end
                    expect_list = expect_time.split(",")
                    l = []  # 将时间段拆成一个个时间点
                    for el in expect_list:
                        l += el[1:-1].split("-")
                    # l = ['9:15', '9:25', '9:30', '11:30', '13:00', '15:30']
                    for count in range(len(l)):
                        if len(l[count]) == 4:
                            l[count] = '0' + l[count]
                    if except_end <= l[0] or except_begin >= l[-1]:
                        break  # 无影响
                    real_time_list = []
                    for count in range(0, len(l), 2):
                        if except_end <= l[count] or except_begin >= l[count+1]:
                            real_time_list.append(l[count])
                            real_time_list.append(l[count+1])
                            continue
                        # 四种情况有交集，设a为realtime，b为excepttime，
                        # 有a1<=a2, b1<=b2
                        if l[count] <= except_begin and l[count+1] <= except_end:
                            real_time_list.append(l[count])
                            real_time_list.append(except_begin)
                        # a1<=a2, b1>=b2
                        elif l[count] <= except_begin and l[count+1] >= except_end:
                            real_time_list.append(l[count])
                            real_time_list.append(except_begin)
                            real_time_list.append(except_end)
                            real_time_list.append(l[count+1])
                        # a1>=a2, b1>=b2,
                        elif l[count] >= except_begin and l[count+1] >= except_end:
                            real_time_list.append(except_end)
                            real_time_list.append(l[count+1])
                        # a1>=a2, b1<=b2
                        else:
                            ...  # do nothing
                    s = "{"
                    for count in range(0, len(real_time_list), 2):
                        s += f"[{real_time_list[count]}-{real_time_list[count+1]}],"
                    real_time = s[:-1] + '}'
                if '{' not in real_time:
                    real_time = '{' + real_time + '}'
                constraint = {"key":"交易时间", "operation":"in", "value": real_time}
                new_constraints.append(constraint)
                # 处理完成
                # 删除交易阶段
                del new_constraints[cnt]
                rules[keys[i]]["constraints"] = new_constraints

                del vars[keys[i]]["交易阶段"]
                vars[keys[i]]['交易时间'] = []
                break

    return vars, rules



def delete_then(vars, rules):
    keys = list(rules.keys())
    to_delete = []
    for rule_id in keys:
        rule = rules[rule_id]
        if 'results' not in rule:
            to_delete.append(rule_id)
    for rule_id in to_delete:
        del rules[rule_id]
        del vars[rule_id]
    return vars, rules




def post_process(vars, rules):
    # 添加操作，如果一条规则没有操作，操作为“申报”，如果存在“成交确认...”，操作为“达成交易”
    keys = list(rules.keys())
    for rule_id in keys:
        have_op = False
        value_constraint = False
        change_op = False
        rule = rules[rule_id]
        for c in rule['constraints']:
            if c['key'] == '操作':
                have_op = True
            # if is_key_for_time(c['key']) or is_key_for_quantity(c['key']) or is_key_for_price(c['key']):
            #     value_constraint = True
            if "成交确认" in c['key'] or "成交确认" in c['value'] or "有效期" in c['key']:
                change_op = True
        if not have_op:
            rule['constraints'].append({"key":"操作","operation":"is","value":"申报"})
            vars[rule_id]['操作'] = []
        if change_op:
            for c in rule['constraints']:
                if c['key'] == "操作":
                    c['value'] = "达成交易"

    # 合并同类项，这里仅合并数量和申报数量
    for rule_id in keys:
        rule = rules[rule_id]
        value = ""
        last_value = ""
        for c in rule['constraints']:
            if (c['key'] == "数量" or c['key'] == "申报数量") and c['value'] not in value:
                if "不超过" in c['value']:
                    last_value = c['value']
                else:
                    value += c['value'] + ","
        if last_value != "":
            value = value + last_value + ","
        if value.count(",")>=2:
            value = value[:-1]
        add = False
        new_rule = copy.deepcopy(rules[rule_id])
        new_rule['constraints'] = []
        new_var = {"结果":[]}
        for c in rule['constraints']:
            if c['key'] == "数量" or c['key'] == "申报数量":
                if not add:
                    new_rule['constraints'].append({"key":"申报数量","operation":"is","value":value})
                    new_var["申报数量"] = []
                    add = True
                else:
                    continue
            else:
                new_rule['constraints'].append({"key":c['key'],"operation":c['operation'],"value":c['value']})
                new_var[c['key']] = []
        rules[rule_id] = new_rule
        vars[rule_id] = new_var
    
    return vars, rules




































@DeprecationWarning
def compose_full_rules(vars, rules):
    # 全规则组合，太多了
    keys1 = list(vars.keys())

    composed_rules = {}
    for i in range(1 << len(keys1)):
        if i == 0:
            continue

        new_constraints = []
        new_results = []
        new_focus = []
        new_id = ""
        for j in range(len(keys1)):
            rule_now = rules[keys1[j]]
            if i & (1 << j):
                # 有这条规则，组合
                if new_constraints == []:
                    new_constraints = copy.deepcopy(rule_now['constraints'])
                    if "results" in rule_now:
                        new_results = copy.deepcopy(rule_now['results'])
                    new_focus = copy.deepcopy(rule_now['focus'])
                    new_id = keys1[j]
                    continue
                conflict = False
                to_add = []
                for c0 in rule_now['constraints']:
                    find = False
                    for c1 in new_constraints:
                        if c0['operation'] == 'is' and c0['key'] == c1['key']:
                            find = True
                            if c0['value'] != c1['value']:
                                conflict = True
                                break
                    if not find:
                        to_add.append(copy.deepcopy(c0))
                    if conflict:
                        break
                if not conflict:
                    new_constraints = new_constraints + to_add
                    new_id = new_id + "," + keys1[j]
                    if "results" in rule_now:
                        for r0 in rule_now['results']:
                            if r0 not in new_results:
                                new_results.append(r0)
                    for f0 in rule_now['focus']:
                        if f0 not in new_focus:
                            new_focus.append(f0)

        if new_results == []:
            t = {"constraints":new_constraints,
             "focus":new_focus}
        else:
            t = {"constraints":new_constraints,
                "results":new_results,
                "focus":new_focus}
        composed_rules[new_id] = t


    # 删除原来的组合规则，加入新的组合规则
    for key in keys1:
        del rules[key]
        del vars[key]
    for rule_id in composed_rules:
        rules[rule_id] = composed_rules[rule_id]
        var = {}
        for c in rules[rule_id]['constraints']:
            var[c['key']] = []
        vars[rule_id] = var

    # 去重
    # 去重组合规则，方法是如果一个a是另一个b的子集，去掉a
    keys = rules.keys()
    key_to_delete = []
    for i, rule_id in enumerate(keys):
        rule = rules[rule_id]
        if rule['focus'] == '交易时间':
            continue
        rule_id_list = rule_id.split(',')
        for j, rule_id1 in enumerate(keys):
            rule1 = rules[rule_id1]
            if rule1['focus'] == '交易时间' or i == j:
                continue
            rule_id_list1 = rule_id1.split(',')
            # 看是否rule_id_list1是rule_id_list的子集
            is_subset = True
            for x in rule_id_list1:
                if x not in rule_id_list:
                    is_subset = False
                    break
            if is_subset and rule_id1 not in key_to_delete:
                key_to_delete.append(rule_id1)

    for key in key_to_delete:
        del rules[key]
        del vars[key]







