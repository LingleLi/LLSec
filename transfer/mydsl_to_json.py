from specification_generation.rule_assembly import is_key_for_quantity

def mydsl_to_json(s):
    test_scenarioes = []
    scenario = {}
    for line in s.split("\n"):
        line = line.strip().replace("或其整数倍", "或者其整数倍")  # 数量的特殊处理
        if line == "" and scenario != {}:
            test_scenarioes.append(scenario)
            scenario = {}
            continue
        if line.find("if") == 0 or line.find("then") == 0:
            words = line.split(" ")
            for i in range(1, len(words), 4):
                if words[i] not in scenario:
                    scenario[words[i]] = words[i+2][1:-1]
                else:
                    if is_key_for_quantity(words[i]):
                        scenario[words[i]] = scenario[words[i]] + "," + words[i+2][1:-1]
                        continue
                    j = 2
                    while words[i] + str(j) in scenario:
                        j += 1
                    scenario[words[i] + str(j)] = words[i+2][1:-1]
        elif line.find("rule") == 0:
            scenario['id'] = line.split(" ")[1]
        elif line.find("focus") == 0:
            scenario['测试关注点'] = line.split(" ")[1]
    return test_scenarioes