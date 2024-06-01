import json
import torch
import random




# 数据集
class DefaultDataset:
    def __init__(self, data):
        self.datas = data

    def __len__(self):
        return len(self.datas)

    def __getitem__(self, index):
        return self.datas[index]




def read_json_for_sequence_classification(file: str, istrain: bool = False):
    id_data = []
    ds = json.load(open(file, "r", encoding="utf-8"))
    for d in ds:
        x, y = d["text"], d["type"]
        id_data.append({"text":x, "label":y})
    if istrain:
        random.shuffle(id_data)
    return id_data


class DataCollatorForSequenceClassification:
    def __init__(self, tokenizer, max_length: int = 512, padding = "max_length", truncation: bool = True):
        self.tokenizer = tokenizer
        self.padding = padding
        self.truncation = truncation
        self.max_length = max_length


    def __call__(self, batch):
        features = self.collator_fn(batch)
        return features


    def preprocess(self, item):  # 获取数据
        source = item["text"]
        target = item["label"]
        return source, target

    def collator_fn(self, batch):  # 处理函数，主要将json的list转化为tensor的inputs和labels
        results = map(self.preprocess, batch)
        inputs, targets = zip(*results)

        input_tensor = self.tokenizer(inputs,
                                      truncation=self.truncation,  # 截断
                                      padding=self.padding,  # 填充
                                      max_length=self.max_length,
                                      return_tensors="pt",  # pytorch模型 或 "tf" tensorflow模型
                                      )
        labels = [int(t) for t in targets]
        
        input_tensor["labels"] = torch.tensor(labels)

        return input_tensor