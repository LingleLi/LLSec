import json

def gpt_output_to_input(s):
    rules = []
    rule = {}
    for line in s.split("\n"):
        line = line.strip()
        if line == "":
            continue
        if line.find("id") == 0:
            if rule != {}:
                rules.append(rule)
                rule = {}
        k, v = line.split(":")[0].strip(), ":".join([a.strip() for a in line.split(":")[1:]])
        if k in rule:
            index = 2
            while k + str(index) in rule:
                index += 1
            k = k + str(index)
            rule[k] = v
        else:
            rule[k] = v
    if rule != {}:
        rules.append(rule)
    return rules


if __name__ == "__main__":
    inputs = open("rules_cache/chatgpt_output.txt", "r", encoding="utf-8").read()
    rules = gpt_output_to_input(inputs)
    json.dump(rules, open("rules_cache/input.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)