import json
import os

def to_inputs(s):
    inputs = []
    rule = {}
    last_id = ""
    id_index = 1
    for line in s.split("\n")[1:]:
        if line.strip() == "":
            if rule != {}:
                inputs.append(rule)
                rule = {}
            continue
        line = line.replace(" ", "")
        key, value = line.split(":")[0], ":".join(line.split(":")[1:])
        if key == "id":
            if value == last_id:
                last_id = value
                value = f"{value}.{id_index}"
                id_index += 1
            else:
                id_index = 1
                last_id = value
                value = f"{value}.{id_index}"
                id_index += 1
            
        if key in rule:
            i = 2
            while f"{key}{i}" in rule:
                i += 1
            rule[f"{key}{i}"] = value
        else:
            rule[key] = value
    if rule != {}:
        inputs.append(rule)
    return inputs


if __name__ == "__main__":
    for file in os.listdir("exp1_data/our_inputs"):
        if ".txt" in file:
            s = open("exp1_data/our_inputs/" + file, "r", encoding="utf-8").read()
            inputs = to_inputs(s)
            dataset = file.split("_")[0]
            json.dump(inputs, open(f"exp1_data/our_inputs/{dataset}_input.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    
    for file in os.listdir("exp2_data/our_inputs"):
        if ".txt" in file:
            s = open("exp2_data/our_inputs/" + file, "r", encoding="utf-8").read()
            inputs = to_inputs(s)
            dataset = file.split("_")[0]
            json.dump(inputs, open(f"exp2_data/our_inputs/{dataset}_input.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    
    for file in os.listdir("exp4_data/our_inputs"):
        if ".txt" in file and "pre" not in file:
            s = open("exp4_data/our_inputs/" + file, "r", encoding="utf-8").read()
            inputs = to_inputs(s)
            dataset = file.split("_")[0]
            json.dump(inputs, open(f"exp4_data/our_inputs/{dataset}_input.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)