import json
import os

def expert_result_to_testcase(s):
    s = s.replace(" ", "").replace("、", ".")
    lines = [si.strip() for si in s.split("\n")]
    casestr = ""
    testcases = []
    begin = False
    for line in lines:
        if line == "":
            continue
        if line == "{":
            casestr += line
            begin = True
        if line == "}":
            casestr = casestr[:-1] + line
            testcases.append(json.loads(casestr))
            casestr = ""
            begin = False
        if line != "{" and line != "}" and begin:
            ss = line.split(":")
            ss = [ss[0], ":".join(ss[1:])]
            for i, si in enumerate(ss):
                if si[0] != "\"":
                    ss[i] = "\"" + si
                if si[-1] != "\"":
                    ss[i] = ss[i] + "\""
            casestr += ":".join(ss) + ","
    return testcases


def postprocess(testcases):
    for testcase in testcases:
        have_op = False
        for key in list(testcase.keys()):
            if key == "操作":
                have_op = True
            if key == "交易方式":
                if testcase[key][-2:] == "方式":
                    testcase[key] = testcase[key][:-2]
                if testcase[key][-2:] != "交易" and testcase[key][-2:] != "成交":
                    testcase[key] = testcase[key] + "交易"
            if key == "交易市场":
                if "深圳" in testcase[key]:
                    testcase[key] = "深圳证券交易所"
                elif "上海" in testcase[key]:
                    testcase[key] = "上海证券交易所"
            if key == "结果":
                if "无效" in testcase[key] or "失败" in testcase[key]:
                    testcase[key] = "不成功"
        if not have_op:
            testcase["操作"] = "申报"
    
    return testcases

if __name__ == "__main__":
    for file in os.listdir("exp1_data/expert_result"):
        if "expert" in file and ".txt" in file:
            print(f"处理{file}")
            s = open(f"exp1_data/expert_result/{file}", "r", encoding="utf-8").read()
            testcases = expert_result_to_testcase(s)
            testcases = postprocess(testcases)
            json.dump(testcases, open(f"exp1_data/expert_result/{file.split('.')[0]}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    
    for file in os.listdir("exp2_data/expert_result"):
        if "expert" in file and ".txt" in file:
            print(f"处理{file}")
            s = open(f"exp2_data/expert_result/{file}", "r", encoding="utf-8").read()
            testcases = expert_result_to_testcase(s)
            testcases = postprocess(testcases)
            json.dump(testcases, open(f"exp2_data/expert_result/{file.split('.')[0]}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)