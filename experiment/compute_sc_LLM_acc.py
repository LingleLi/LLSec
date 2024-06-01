import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoModelForCausalLM, HfArgumentParser, set_seed, BitsAndBytesConfig
from peft import PeftConfig, PeftModel
import json
import os

def generate_sc_test_result_mengzi(eval_dataset, model_path, test_result_file):
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=3)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    datas = json.load(open(eval_dataset, "r", encoding="utf-8"))
    inputs, labels = [], []
    for data in datas:
        inputs.append(data['text'])
        labels.append(data['type'])

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model.to(device)
    y_hats = []
    for input in inputs:
        input = [input]
        input = tokenizer(input, max_length=512, padding="max_length", truncation=True, return_tensors="pt")
        input_ids = input.input_ids.to(device)
        logits = model(input_ids=input_ids).logits
        _, outputs = torch.max(logits, dim=1)
        outputs = outputs.cpu().numpy()
        y_hats.extend(outputs)
    
    for i, data in enumerate(datas):
        data['predict_type'] = str(y_hats[i])
        if "label" in data:
            del data['label']
        if "id" in data:
            del data['id']

    json.dump(datas, open(test_result_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)



def compute_acc_mengzi(test_result_file, acc_file):
    datas = json.load(open(test_result_file, "r", encoding="utf-8"))
    correct, total = 0, len(datas)
    not_correct_texts = []
    for i, data in enumerate(datas):
        if data['predict_type'] == data['type']:
            correct += 1
        else:
            not_correct_texts.append(data['text'])
    with open(acc_file, "w", encoding="utf-8") as f:
        f.write("Ours mengzi:\n{} are correct with a total of {}\nacc: {:.4f}\n\n\n".format(correct, total, correct / total))
        print("Ours mengzi:\n{} are correct with a total of {}\nacc: {:.4f}".format(correct, total, correct / total))
        # f.write("not correct ids: \n{}".format('\n'.join(not_correct_texts)))

def generate_sc_test_result_llama2_lora(eval_dataset, model_path, test_result_file):
    # load model
    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_use_double_quant=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
    peft_config = PeftConfig.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(peft_config.base_model_name_or_path, device_map='cuda:0' if torch.cuda.is_available() else 'auto', torch_dtype=torch.float16, trust_remote_code=True, use_flash_attention_2=True, quantization_config=bnb_config)
    model = PeftModel.from_pretrained(model, model_path, device_map="cuda:0" if torch.cuda.is_available() else "auto")
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(peft_config.base_model_name_or_path)
    
    # load dataset
    inputs, targets = [], []
    with open(eval_dataset, "r", encoding="utf-8") as f:
        lines = f.readlines()
    i, t = "", ""
    stage = 0
    for line in lines[1:]:
        line = line.replace("\"", "")
        if "<s>" in line:
            if "</s>" in line:
                i += line.split("Assistant:")[0] + "Assistant:"
                t += line.split("Assistant:")[1].replace(" ", "")
                stage = 2
            else:
                i += line
                stage = 1
        elif "</s>" in line:
            t += line
            inputs.append(i)
            targets.append(t)
            i, t = "", ""
            stage = 0
        elif stage == 1:
            i += line
        elif stage == 2:
            t += line
    
    # predict
    predictions = []
    for index in range(len(inputs)):
        # print(f"### {index}")
        i = inputs[index]
        t = targets[index]
        input_ids = tokenizer([i], return_tensors="pt", add_special_tokens=False).input_ids
        input_ids = input_ids.to("cuda:0" if torch.cuda.is_available() else "cpu")
        generate_ids = model.generate(input_ids=input_ids)
        predict_text = tokenizer.batch_decode(generate_ids, skip_special_tokens=True)[0]
        predictions.append({
            "prompt": i,
            "answer": t,
            "prediction": predict_text
        })
        # print(json.dumps({"prompt":i,"answer":t,"prediction":predict_text}, indent=4, ensure_ascii=False))
        # print("\n\n")
    json.dump(predictions, open(test_result_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)


def generate_sc_test_result_llama2_fine_tune(eval_dataset, model_path, test_result_file):
    # load model
    model = AutoModelForCausalLM.from_pretrained(model_path, device_map='cuda:0' if torch.cuda.is_available() else 'auto', torch_dtype=torch.float16, trust_remote_code=True, use_flash_attention_2=True)
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    # load dataset
    inputs, targets = [], []
    with open(eval_dataset, "r", encoding="utf-8") as f:
        lines = f.readlines()
    i, t = "", ""
    stage = 0
    for line in lines[1:]:
        line = line.replace("\"", "")
        if "<s>" in line:
            if "</s>" in line:
                i += line.split("Assistant:")[0] + "Assistant:"
                t += line.split("Assistant:")[1].replace(" ", "")
                stage = 2
            else:
                i += line
                stage = 1
        elif "</s>" in line:
            t += line
            inputs.append(i)
            targets.append(t)
            i, t = "", ""
            stage = 0
        elif stage == 1:
            i += line
        elif stage == 2:
            t += line
    
    # predict
    predictions = []
    for index in range(len(inputs)):
        # print(f"### {index}")
        i = inputs[index]
        t = targets[index]
        input_ids = tokenizer([i], return_tensors="pt", add_special_tokens=False).input_ids
        input_ids = input_ids.to("cuda:0" if torch.cuda.is_available() else "cpu")
        generate_ids = model.generate(input_ids=input_ids)
        predict_text = tokenizer.batch_decode(generate_ids, skip_special_tokens=True)[0]
        predictions.append({
            "prompt": i,
            "answer": t,
            "prediction": predict_text
        })
        # print(json.dumps({"prompt":i,"answer":t,"prediction":predict_text}, indent=4, ensure_ascii=False))
        # print("\n\n")
    json.dump(predictions, open(test_result_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)




def compute_acc_llama2(test_result_file, acc_file):
    predictions = json.load(open(test_result_file, "r", encoding="utf-8"))
    # compute acc
    correct, total = 0, len(predictions)
    for i, data in enumerate(predictions):
        real_label = data['answer'].split("\n")[0].strip()
        predict_label = data['prediction'].split("Assistant:")[-1].strip()
        if real_label == predict_label:
            correct += 1
    with open(acc_file, "a", encoding="utf-8") as f:
        if "lora" in test_result_file:
            f.write("Ours llama2 lora:\n{} are correct with a total of {}\nacc: {:.4f}\n\n\n".format(correct, total, correct / total))
            print("Ours llama2 lora:\n{} are correct with a total of {}\nacc: {:.4f}".format(correct, total, correct / total))
        else:
            f.write("Ours llama2 fine-tune:\n{} are correct with a total of {}\nacc: {:.4f}\n\n\n".format(correct, total, correct / total))
            print("Ours llama2 fine-tune:\n{} are correct with a total of {}\nacc: {:.4f}".format(correct, total, correct / total))





def compute_llm_acc(real_file, predict_dir, acc_file):
    f = open(acc_file, "w", encoding="utf-8")
    for predict_file in sorted(os.listdir(predict_dir)):
        if "predict_result" not in predict_file:
            continue
        predict_datas = json.load(open(predict_dir + predict_file, "r", encoding="utf-8"))
        real_datas = json.load(open(real_file, "r", encoding="utf-8"))
        correct, total = 0, len(real_datas)
        not_correct_texts = []
        # real_0_pred_1, real_0_pred_2, real_1_pred_0, real_1_pred_2, real_2_pred_0, real_2_pred_1 = 0, 0, 0, 0, 0, 0
        wrong = [0 for _ in range(6)]
        for i, data in enumerate(real_datas):
            if data['type'] == predict_datas[i]['type']:
                correct += 1
            else:
                not_correct_texts.append(f"{data['text']}, predict_type: {predict_datas[i]['type']}, real_type: {data['type']}")
                if data['type'] == "0" and predict_datas[i]['type'] == "1":
                    wrong[0] += 1
                elif data['type'] == "0" and predict_datas[i]['type'] == "2":
                    wrong[1] += 1
                elif data['type'] == "1" and predict_datas[i]['type'] == "0":
                    wrong[2] += 1
                elif data['type'] == "1" and predict_datas[i]['type'] == "2":
                    wrong[3] += 1
                elif data['type'] == "2" and predict_datas[i]['type'] == "0":
                    wrong[4] += 1
                elif data['type'] == "2" and predict_datas[i]['type'] == "1":
                    wrong[5] += 1
        f.write(f"file {predict_file}, acc: {correct / total}\n\n")
        print(f"file {predict_file}, acc: {correct / total}")
        # f.write("not correct ids: \n{}\n\n".format('\n'.join(not_correct_texts)))
        f.write(f"real_0_pred_1: {wrong[0]}\nreal_0_pred_2: {wrong[1]}\nreal_1_pred_0: {wrong[2]}\nreal_1_pred_2: {wrong[3]}\nreal_2_pred_0: {wrong[4]}\nreal_2_pred_1: {wrong[5]}\n\n\n\n")
        print(f"real_0_pred_1: {wrong[0]}\nreal_0_pred_2: {wrong[1]}\nreal_1_pred_0: {wrong[2]}\nreal_1_pred_2: {wrong[3]}\nreal_2_pred_0: {wrong[4]}\nreal_2_pred_1: {wrong[5]}")
    f.close()





if __name__ == "__main__":
    # ours mengzi
    generate_sc_test_result_mengzi("rule_filtering_data/dataset/rule_filtering_validate.json", "../train_rule_filtering_model/model/mengzi_rule_filtering", "rule_filtering_data/ours_result/ours_test_result_mengzi.json")
    compute_acc_mengzi("rule_filtering_data/ours_result/ours_test_result_mengzi.json", "rule_filtering_data/ours_result/ours_acc.txt")

    # ours llama2 lora
    generate_sc_test_result_llama2_lora("rule_filtering_data/dataset/rule_filtering_llama2_validate.csv", "../lora_train_llama2_model/model/rule_filtering/llama2_rule_filtering_lora", "rule_filtering_data/ours_result/ours_test_result_llama2_lora.json")
    compute_acc_llama2("rule_filtering_data/ours_result/ours_test_result_llama2_lora.json", "rule_filtering_data/ours_result/ours_acc.txt")
    
    # ours llama2 fine tune
    generate_sc_test_result_llama2_fine_tune("rule_filtering_data/dataset/rule_filtering_llama2_validate.csv", "../fine_tune_llama2_model/model/rule_filtering/llama2_rule_filtering_fine_tune", "rule_filtering_data/ours_result/ours_test_result_llama2_fine-tune.json")
    compute_acc_llama2("rule_filtering_data/ours_result/ours_test_result_llama2_fine-tune.json", "rule_filtering_data/ours_result/ours_acc.txt")


    # GLM-4
    compute_llm_acc("rule_filtering_data/dataset/rule_filtering_validate.json", "rule_filtering_data/chatglm_result/", "rule_filtering_data/chatglm_result/chatglm_acc.txt")

    # # GPT-4
    compute_llm_acc("rule_filtering_data/dataset/rule_filtering_validate.json", "rule_filtering_data/chatgpt_result/", "rule_filtering_data/chatgpt_result/chatgpt_acc.txt")