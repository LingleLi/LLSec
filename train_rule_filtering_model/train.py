from transformers import AutoModelForSequenceClassification, AutoTokenizer, Trainer, TrainingArguments
from train_rule_filtering_model.data_loader import DefaultDataset, DataCollatorForSequenceClassification, read_json_for_sequence_classification
from train_rule_filtering_model.arg_parser import arg_parser
import torch
import time
from train_rule_filtering_model.try_gpu import try_gpu


def train_model(training_args: dict):
    model_path = training_args["model"]
    train_dataset = training_args["train_dataset"]
    validate_dataset = training_args["validate_dataset"]

    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=3)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    train_dataset = DefaultDataset(read_json_for_sequence_classification(train_dataset, istrain=True))
    validate_dataset = DefaultDataset(read_json_for_sequence_classification(validate_dataset))
    collator = DataCollatorForSequenceClassification(tokenizer, max_length=training_args["sentence_max_length"])

    saved_path = training_args["output_dir"]
    training_args = TrainingArguments(
        num_train_epochs=training_args["num_train_epochs"],
        per_device_train_batch_size=training_args["per_device_train_batch_size"],
        per_device_eval_batch_size=training_args["per_device_eval_batch_size"],
        logging_steps=training_args["logging_step"],
        evaluation_strategy=training_args["evaluation_strategy"],
        eval_steps=training_args["eval_steps"],
        load_best_model_at_end=training_args["load_best_model_at_end"],
        learning_rate=training_args["learning_rate"],
        output_dir=training_args["output_dir"],
        save_total_limit=training_args["save_total_limit"],
        lr_scheduler_type=training_args["lr_scheduler_type"],
        gradient_accumulation_steps=training_args["gradient_accumulation_steps"],
        dataloader_num_workers=training_args["dataloader_num_workers"],
        remove_unused_columns=training_args["remove_unused_columns"],
        save_strategy=training_args["save_strategy"],
        disable_tqdm=training_args["disable_tqdm"],
        weight_decay=training_args["weight_decay"]
    )
    trainer = Trainer(model, training_args, collator, train_dataset, validate_dataset, tokenizer)
    trainer.train()

    saved_path = f"{saved_path}/best_{int(time.time())}"
    trainer.save_model(saved_path)
    return saved_path


def eval_model(training_args: dict, model_path: str, output_filename: str):

    validate_dataset = training_args["validate_dataset"]
    model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=3)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    def preprocess(items):
        inputs, labels = [], []
        for item in items:
            inputs.append(item["text"])
            labels.append(int(item["label"]))
        return inputs, labels

    validate_dataset = read_json_for_sequence_classification(validate_dataset)
    inputs, labels = preprocess(validate_dataset)

    def predict(model, tokenizer, inputs, batch_size=8):
        model.eval()
        device = try_gpu()
        model = model.to(device)
        hats = []  # batch_size, 1
        for start in range(0, len(inputs), batch_size):
            batch = inputs[start:start+batch_size]
            batch = tokenizer(batch, max_length=training_args["sentence_max_length"], padding="max_length", truncation=True, return_tensors="pt")
            input_ids = batch.input_ids.to(device)
            logits = model(input_ids=input_ids).logits  # (8, 2)
            _, outputs = torch.max(logits, dim=1)
            outputs = outputs.cpu().numpy()  # (8)
            hats.extend(outputs)
        return hats

    hats = predict(model, tokenizer, inputs)
    
    with open(output_filename, "w+", encoding="utf-8") as f:
        f.write("预测结果：\n")
        correct = 0
        for i, data in enumerate(validate_dataset):
            f.write(f"id: {i}\ntext: {inputs[i]}\nseq hat: {hats[i]}\nseq real: {labels[i]}\n")
            f.write("----------------------------------------------------\n\n")
            if(hats[i] == labels[i]):
                correct += 1
        f.write(f"统计结果：\n测试集数据数量：{len(validate_dataset)}，预测正确数量：{correct}，正确率：{float(correct) / float(len(validate_dataset))}")
        f.write("\n\n\n\n\n\n\n\n\n\n")



if __name__ == "__main__":
    training_args = arg_parser()
    model = training_args["model"]
    saved_path = train_model(training_args)
    # saved_path = "model/mengzi_rule_filtering"
    eval_model(training_args, saved_path, "./predict_data/"+saved_path.split("/")[-1]+"_test_result.txt")