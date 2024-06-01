import os
import json
from nltk.translate.bleu_score import sentence_bleu
from nltk import edit_distance
from sklearn.metrics import f1_score, recall_score, precision_score
import lora_train_llama2_model.predict as lora_predict
import fine_tune_llama2_model.predict as fine_tune_predict
from train_rule_extraction_model.train import eval_model


def read_OBI_to_rule(texts, labels):
    """
    读取模型输出的OBI文件，将其转化为key-value对的形式，存放在stack中。
    """
    stack = []  # 按顺序记录所有的label及其对应text为{label:text}
    last_label = "O"
    operator_count = 0
    for i, label in enumerate(labels.split(" ")):
        if label == "O":  # O->O, B->O, I->O
            if last_label != "O":  # B->O, I->O
                b = i
                # 记录到stack中
                # stack.append({last_label: texts[a:b]})
                stack.append({last_label:texts[a:b]})
            last_label = label
        else:
            l_content = label[2:]
            if "B" == label[0]:  # O->B，I->B，B->B
                # 处理旧标签
                if last_label != "O":
                    b = i
                    # 记录到stack中
                    # stack.append({last_label: texts[a:b]})
                    stack.append({last_label:texts[a:b]})
                # 记录新标签
                a = i
                last_label = l_content
            else:  # 如果是... -> I
                ...
    return stack



def generate_tc_test_result_mengzi(eval_dataset, model_path, test_result_file, class_dict, training_args):

    eval_model(eval_dataset, class_dict, model_path, test_result_file, training_args)



def generate_tc_test_result_llama2(eval_dataset, model_path, test_result_file):
    if "lora" in model_path:
        model, tokenizer = lora_predict.get_trained_model_and_tokenizer(model_path, "4bit-lora", False)
        inputs, targets = lora_predict.get_datas(eval_dataset)
        predictions = lora_predict.generate_prediction(model, tokenizer, inputs, targets)
        json.dump(predictions, open(test_result_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    else:
        model, tokenizer = fine_tune_predict.get_trained_model_and_tokenizer(model_path, "base", False)
        inputs, targets = fine_tune_predict.get_datas(eval_dataset)
        predictions = fine_tune_predict.generate_prediction(model, tokenizer, inputs, targets)
        json.dump(predictions, open(test_result_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)


@DeprecationWarning
def compute_acc_llm_deprecated(results):
    bleu_score = 0
    p, r, f = 0, 0, 0
    for index, result in enumerate(results):
        answer = result['answer'].replace(" ", "").replace("\n", "").split("</s>")[0].replace("：", ":")
        prediction = result['prediction'].split("Assistant:")[-1].replace(" ", "").replace("\n", "").split("</s>")[0].replace("：", ":")
        answer, prediction = list(answer), list(prediction)
        
        if len(answer) == 0:
            score = 1.0
        else:
            score = sentence_bleu([answer], prediction)
        bleu_score += score
    
        # 将prediction, answer转换为BIO格式
        text = result['prompt'].replace("：", ":").split("\n")[1][4:]
        new_prediction, new_answer = ["O"] * len(text), ["O"] * len(text)
        prediction, answer = "".join(prediction), "".join(answer)

        pos = -1
        for i, lb in enumerate(prediction.split(",")):
            if ":" not in lb:
                continue
            a, b = lb.split(":")[0], ":".join(lb.split(":")[1:])
            pos = text.find(b, pos+1)
            if pos == -1:
                continue
            new_prediction[pos:pos+len(b)] = ["B-" + a] + ["I-" + a] * (len(b)-1)
        pos = -1
        for i, lb in enumerate(answer.split(",")):
            a, b = lb.split(":")[0], ":".join(lb.split(":")[1:])
            pos = text.find(b, pos+1)
            if pos == -1:
                continue
            new_answer[pos:pos+len(b)] = ["B-" + a] + ["I-" + a] * (len(b)-1)
        

        if len(answer) == 0:
            p += 1.0
            r += 1.0
            f += 1.0
        else:
            pi, ri, fi = precision_score(new_answer, new_prediction, average="micro"), recall_score(new_answer, new_prediction, average="micro"), f1_score(new_answer, new_prediction, average="micro")
            p += pi
            r += ri
            f += fi
    return round(bleu_score / float(len(results)), 4), round(p / float(len(results)), 4), round(r / float(len(results)), 4), round(f / float(len(results)), 4)



def compute_acc_llm_ours(results):
    # 比较两个字符串的相似度
    bleu, precision, recall, f1 = 0, 0, 0, 0
    for result in results:
        answer = result['answer'].replace(" ", "").replace("\n", "").split("</s>")[0].replace("：", ":")
        prediction = result['prediction'].split("Assistant:")[-1].replace(" ", "").replace("\n", "").split("</s>")[0].replace("：", ":")
        answer, prediction = list(answer), list(prediction)
        
        # 计算blue
        if len(answer) == 0:
            score = 1.0
        else:
            score = sentence_bleu([answer], prediction)
        bleu += score

        answer_list, prediction_list = "".join(answer).split(","), "".join(prediction).split(",")
        pi = 0
        for p in prediction_list:
            if p in answer_list:
                pi += 1
        pi = pi / len(answer_list)
        precision += pi

        ri = 0
        for a in answer_list:
            if a in prediction_list:
                ri += 1
        ri = ri / len(prediction_list)
        recall += ri

        fi = 0
        if pi + ri > 0:
            fi = 2 * pi * ri / (pi + ri)
        f1 += fi
    
    return round(bleu / float(len(results)), 4), round(precision / float(len(results)), 4), round(recall / float(len(results)), 4), round(f1 / float(len(results)), 4)



def compute_acc_mengzi(s):
    datas = []
    text, answer, prediction = "", "", ""
    for line in s.split("\n"):
        if "text" in line:
            text = line[6:]
        if "ir hat" in line:
            prediction = line[8:]
        elif "ir real" in line:
            answer = line[9:]
            prediction = read_OBI_to_rule(text, prediction)
            answer = read_OBI_to_rule(text, answer)
            p = ""
            for pi in prediction:
                key = list(pi.keys())[0]
                value = pi[key]
                p += f"{key}:{value},"
            prediction = p[:-1]
            a = ""
            for ai in answer:
                key = list(ai.keys())[0]
                value = ai[key]
                a += f"{key}:{value},"
            answer = a[:-1]
            datas.append({"prediction":p, "answer":a})
    return compute_acc_llm_ours(datas)



def compute_acc_llm(results, labels):
    for i, result in enumerate(results):
        result['prediction'] = result['label']
        del result['label']
        stack = read_OBI_to_rule(result['text'], labels[i]['label'])
        s = ""
        for si in stack:
            key = list(si.keys())[0]
            value = si[key]
            s += f"{key}:{value},"
        result['answer'] = s[:-1]
    
    bleu, precision, recall, f1 = 0, 0, 0, 0
    threshold = 0.99
    for result in results:
        prediction, answer = result['prediction'], result['answer']
        answer, prediction = list(answer), list(prediction)
        
        # 计算blue
        if len(answer) == 0:
            score = 1.0
        else:
            score = sentence_bleu([answer], prediction)
        bleu += score

        answer_list, prediction_list = "".join(answer).split(","), "".join(prediction).split(",")
        pi = 0
        for p in prediction_list:
            for a in answer_list:
                if len(a) == 0 or len(p) == 0:
                    continue
                if p in a or a in p or edit_distance(p, a) / len(a) < threshold:
                    pi += 1
                    break
        pi = pi / len(answer_list)
        precision += pi

        cover = [0 for _ in range(len(prediction_list))]
        for a in answer_list:
            for idx, p in enumerate(prediction_list):
                if len(a) == 0 or len(p) == 0:
                    continue
                if p in a or a in p or edit_distance(p, a) / len(a) < threshold:
                    cover[idx] = 1
                    break
        ri = sum(cover) / len(prediction_list)
        recall += ri

        fi = 0
        if pi + ri > 0:
            fi = 2 * pi * ri / (pi + ri)
        f1 += fi
    
    return round(bleu / float(len(results)), 4), round(precision / float(len(results)), 4), round(recall / float(len(results)), 4), round(f1 / float(len(results)), 4)



if __name__ == "__main__":
    f = open("rule_extraction_data/ours_result/ours_acc.txt", "w", encoding="utf-8")

    # mengzi执行规则抽取并进行效果评估
    generate_tc_test_result_mengzi("./rule_extraction_data/dataset/rule_extraction_validate.json", "../train_rule_extraction_model/model/mengzi_rule_extraction", "./rule_extraction_data/ours_result/ours_test_result_mengzi.txt", "../data/tc_data.dict", {"split": " ", "sentence_max_length": 512})
    s = open("./rule_extraction_data/ours_result/ours_test_result_mengzi.txt", "r", encoding="utf-8").read()
    bleu, precision, recall, f1_score = compute_acc_mengzi(s)
    f.write(f"模型mengzi, 预测文件ours_test_result_mengzi.txt: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}\n\n\n")
    print(f"模型mengzi, 预测文件ours_test_result_mengzi.txt: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}")



    # llama2使用lora模型执行规则抽取
    # generate_tc_test_result_llama2("rule_extraction_data/dataset/rule_extraction_llama2_validate.csv", "../lora_train_llama2_model/model/rule_extraction/llama2_rule_extraction_lora", "rule_extraction_data/ours_result/ours_test_result_llama2_lora.json")
    # # llama2使用fine-tune模型执行规则抽取
    # generate_tc_test_result_llama2("rule_extraction_data/dataset/rule_extraction_llama2_validate.csv", "../fine_tune_llama2_model/model/rule_extraction/llama2_rule_extraction_fine_tune", "rule_extraction_data/ours_result/ours_test_result_llama2_fine-tune.json")
    # llama2效果评估
    for file in sorted(os.listdir("rule_extraction_data/ours_result/")):
        if "test_result" not in file or ".json" not in file:
            continue
        datas = json.load(open(f"rule_extraction_data/ours_result/{file}", "r", encoding="utf-8"))
        bleu, precision, recall, f1_score = compute_acc_llm_ours(datas)
        if "lora" in file:
            f.write(f"模型llama2_lora, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}\n\n\n")
            print(f"模型llama2_lora, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}")
        else:
            f.write(f"模型llama2_fine-tune, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}\n\n\n")
            print(f"模型llama2_fine-tune, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}")
    f.close()


    # 对chatgpt和chatglm效果进行评估
    f = open("rule_extraction_data/chatglm_result/chatglm_acc.txt", "w", encoding="utf-8")
    labels = json.load(open("rule_extraction_data/dataset/rule_extraction_validate.json", "r", encoding="utf-8"))
    for file in sorted(os.listdir("rule_extraction_data/chatglm_result/")):
        if "shot.json" not in file:
            continue
        datas = json.load(open(f"rule_extraction_data/chatglm_result/{file}", "r", encoding="utf-8"))
        bleu, precision, recall, f1_score = compute_acc_llm(datas, labels)
        f.write(f"模型chatglm, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}\n\n\n")
        print(f"模型chatglm, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}")
    f.close()

    f = open("rule_extraction_data/chatgpt_result/chatgpt_acc.txt", "w", encoding="utf-8")
    for file in sorted(os.listdir("rule_extraction_data/chatgpt_result/")):
        if "shot.json" not in file:
            continue
        datas = json.load(open(f"rule_extraction_data/chatgpt_result/{file}", "r", encoding="utf-8"))
        bleu, precision, recall, f1_score = compute_acc_llm(datas, labels)
        f.write(f"模型chatgpt, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}\n\n\n")
        print(f"模型chatgpt, 预测文件{file}: bleu: {bleu}, precision: {precision}, recall: {recall}, F1 score: {f1_score}")
    f.close()
