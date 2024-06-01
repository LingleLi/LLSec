import json
import os
import random
import jieba
import synonyms
from nlpcda import Ner
import shutil
import cn2an

# 读取一个目录，按照id分割，生成token classification文件


def read_OBI_to_rule(texts, labels):
    """
    读取模型输出的OBI文件，将其转化为key-value对的形式，存放在stack中。同时记录句子中的；和。并记录在sentence_separate_1和sentence_separate_2中

    :param texts: 一段自然语言
    :param labels: texts对应的标签序列，以空格分隔的字符串形式呈现
    :return stack: 按照出现顺序记录text-label对的数组
    :return sentence_separate_1: 记录；之后的下一个{label:text}在stack中的位置
    :return sentence_separate_2: 记录。之后的下一个{label:text}在stack中的位置
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


# 将所有的数据按照9：1分成训练集和测试集
def integrate_data(in_dir: str, train_file: str, validate_file: str, seq_dir: str):
    all_rules = []
    for file in os.listdir(in_dir):
        if "finish" in file:
            rules = json.load(open(in_dir + file, "r", encoding="utf-8"))
            all_rules += rules
    random.shuffle(all_rules)
    rule_num = len(all_rules)
    train_data = all_rules[:int(rule_num/10*9)]


    datas = json.load(open("../data/business_rules/json_for_rule_filtering/finish_深圳证券交易所债券交易规则.json", "r", encoding="utf-8"))
    new_datas = []
    for data in datas:
        if data['type'] == "1":
            del data['type']
            new_datas.append(data)
    datas = new_datas

    labels = json.load(open("../data/business_rules/json_for_rule_extraction/finish_深圳证券交易所债券交易规则.json", "r", encoding="utf-8"))
    for data in datas:
        for lb in labels:
            if data['text'] in lb['text']:
                begin = lb['text'].find(data['text'])
                end = begin + len(data['text'])
                data['label'] = " ".join(lb['label'].split(" ")[begin:end])
    validate_data = datas

    print(f"原始数据：训练集有数据{len(train_data)}条，验证集有数据{len(validate_data)}条。")
    json.dump(train_data, open(train_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(validate_data, open(validate_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)



def preprocess(input_file, output_dir):
    data = json.load(open(input_file, "r", encoding="utf-8"))
    for index, rule in enumerate(data):
        out_fp = open(output_dir + f"data{index}.txt", "w", encoding="utf-8")
        labels = rule["label"].split(" ")
        for i, text in enumerate(rule["text"]):
            label = labels[i]
            out_fp.write(f"{text}\t{label}\n")
        out_fp.close()


def nlpcda_method(origin_file, input_dir, output_file, augument_size):
    ner = Ner(ner_dir_name=input_dir,
            ignore_tag_list=['O'],
            # 不增强的标签有：结合规则、or、op、系统
            data_augument_tag_list=["key", "时间", "数量", "价格", "交易方式", "交易品种", "操作人", "操作", "操作部分", "结果", "状态","事件", "value"],
            augument_size=augument_size, seed=0)
    
    rules = json.load(open(origin_file, "r", encoding="utf-8"))
    new_rules = []
    def_id = 100
    for i, file in enumerate(os.listdir(input_dir)):
        data_sentence_arrs, data_label_arrs = ner.augment(file_name=input_dir + file)
        # 3条增强后的句子、标签 数据，len(data_sentence_arrs)==3
        # 你可以写文件输出函数，用于写出，作为后续训练等
        if "id" not in rules[i]:
            rules[i]["id"] = f"第{cn2an.an2cn(def_id)}条"
            def_id += 1
        origin_id = rules[i]["id"]
        for j, text in enumerate(data_sentence_arrs):
            label = data_label_arrs[j]
            new_id = origin_id + f".augment{j}"
            rule = {
                "id": new_id,
                "text": "".join(text),
                "label": " ".join(label)
            }
            new_rules.append(rule)
    rules += new_rules
    json.dump(rules, open(output_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)

def data_augment_nlpcda(input_file, output_file, augument_size=10):
    cache_dir = "../data/unaugment_data_cache/"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
    os.mkdir(cache_dir)
    preprocess(input_file, cache_dir)
    nlpcda_method(input_file, cache_dir, output_file, augument_size)
    shutil.rmtree(cache_dir)




########################################################################
# 同义词替换
# 替换一个语句中的n个单词为其同义词
########################################################################
def synonym_replacement_tc(words, label, stop_words, n):
    new_words = words.copy()
    new_label = []
    random_word_list = list(set([word for word in words if word not in stop_words]))     
    random.shuffle(random_word_list)
    num_replaced = 0  
    for random_word in random_word_list:
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(synonyms)
            # 替换，如果word和随机选出的词一样，替换为同义词，否则不变
            # 新增步骤：依据同义词修改label
            new_words_after = []
            i = 0
            for word in new_words:
                if word == random_word:
                    new_words_after.append(synonym)
                    l = label[i]
                    if l == "O":
                        new_label += ["O"] * len(synonym)
                    else:
                        cnt = l[2:]
                        new_label.append(l)
                        new_label += ["I-" + cnt] * (len(synonym)-1)
                    i = i + len(word)
                else:
                    new_words_after.append(word)
                    new_label += label[i:i+len(word)]
                    i = i + len(word)
            num_replaced += 1
            label = new_label
            new_label = []
            new_words = new_words_after
            new_words_after = []
        if num_replaced >= n: 
            break
    
    return new_words, label

def get_synonyms(word):
    return synonyms.nearby(word)[0]


########################################################################
# 随机插入
# 随机在语句中插入n个词
########################################################################
def random_insertion_tc(words, label, n):
    new_words = words.copy()
    for _ in range(n):
        label = add_word_tc(new_words, label)
    return new_words, label

def add_word_tc(new_words, label):
    synonyms = []
    counter = 0    
    while len(synonyms) < 1:
        index = random.randint(0, len(new_words)-1)
        random_word = new_words[index]
        i = 0
        for j in range(index):
            i += len(new_words[j])
        corr_label = label[i]
        synonyms = get_synonyms(random_word)
        counter += 1
        if counter >= 10:
            return label
    random_synonym = random.choice(synonyms)
    if corr_label == "O":
        cr = ["O"] * len(random_synonym)
    else:
        cr = [corr_label]
        cr += ["I-" + corr_label[2:]] * (len(random_synonym) - 1)
    random_idx = random.randint(0, len(new_words)-1)
    new_words.insert(random_idx, random_synonym)
    i = 0
    for j in range(random_idx):
        i += len(new_words[j])
    label = label[:i] + cr + label[i:]
    return label


########################################################################
# Random swap
# Randomly swap two words in the sentence n times
########################################################################

def random_swap_tc(words,label, n):
    new_words = words.copy()
    for _ in range(n):
        new_words, label = swap_word_tc(new_words, label)
    return new_words, label

def swap_word_tc(new_words, label):
    random_idx_1 = random.randint(0, len(new_words)-1)
    random_idx_2 = random_idx_1
    counter = 0
    while random_idx_2 == random_idx_1:
        random_idx_2 = random.randint(0, len(new_words)-1)
        counter += 1
        if counter > 3:
            return new_words, label
    s1, s2, len1, len2 = 0, 0, len(new_words[random_idx_1]), len(new_words[random_idx_2])
    for j in range(random_idx_1):
        s1 += len(new_words[j])
    for j in range(random_idx_2):
        s2 += len(new_words[j])
    lab1, lab2 = label[s1:s1+len1], label[s2:s2+len2]
    if s1 > s2:
        a, b, c = label[:s2], label[s2+len2:s1], label[s1+len1:]
    else:
        a, b, c = label[:s1], label[s1+len1:s2], label[s2+len2:]
    new_words[random_idx_1], new_words[random_idx_2] = new_words[random_idx_2], new_words[random_idx_1] 
    label = a + lab2 + b + lab1 + c

    return new_words, label


########################################################################
# 随机删除
# 以概率p删除语句中的词
########################################################################
def random_deletion_tc(words, label, p):

    if len(words) == 1:
        return words, label

    new_words = []
    new_label = []
    i = 0
    for word in words:
        r = random.uniform(0, 1)
        if r > p:
            new_words.append(word)
            new_label += label[i:i + len(word)]
            i += len(word)

    if len(new_words) == 0:
        rand_int = random.randint(0, len(words)-1)
        i = 0
        for j in range(rand_int):
            i += len(words[j])
        return [words[rand_int]], label[i:i+len(words[rand_int])]


    return new_words, new_label


########################################################################
#EDA函数
########################################################################
def eda_tc(sentence, label, stop_words, alpha_sr=0.1, alpha_ri=0.1, alpha_rs=0.1, p_rd=0.1, num_aug=20):
    seg_list = jieba.cut(sentence)
    label_cp = label
    seg_list = " ".join(seg_list)
    words = list(seg_list.split())
    # 需要依据标注修正分词 完成
    i = 0
    last = ""
    last_word = ""
    label = label.split(" ")
    new_words = []
    for word in words:
        for index, alpha in enumerate(word):
            l = label[i]
            if i == 0:
                last = l
                i += 1
                last_word += alpha
                continue
            # 只需要处理2种情况，1是在词word的中间断开，2是连接两个word
            if l != last:  # B->I, B->O, O->B, I->O, I->B (O->I不存在)
                if last[0] == "B" and l[0] == "I" and last[2:] == l[2:]:  # B->I
                    # 同标签
                    last = l
                    i += 1
                    last_word += alpha
                else:
                    # 换标签
                    if index > 0:  # 情况1
                        new_words.append(last_word)
                        last_word = ""
                    last_word += alpha
                    last = l
                    i += 1
            else:  # I->I, O->O, B->B
                if last[0] == "B" and l[0] == "B":
                    # 换标签
                    if index > 0:  # 情况1
                        new_words.append(last_word)
                        last_word = ""
                    last_word += alpha
                    last = l
                    i += 1
                else:
                    # 同标签
                    last = l
                    i += 1
                    last_word += alpha
        if (i == len(label) - 1) or (i < len(label)-1 and (label[i][0] == "O" or label[i][0] == "B")):  # 分词正确
            new_words.append(last_word)
            last_word = ""
    new_words.append(last_word)

    words = new_words
    num_words = len(words)

    augmented_sentences = []
    augmented_labels = []
    num_new_per_technique = int(num_aug/4)+1
    n_sr = max(1, int(alpha_sr * num_words))
    n_ri = max(1, int(alpha_ri * num_words))
    n_rs = max(1, int(alpha_rs * num_words))
    
    #同义词替换sr
    for _ in range(num_new_per_technique):
        a_words, a_label = synonym_replacement_tc(words, label.copy(), stop_words, n_sr)
        augmented_sentences.append(''.join(a_words))
        augmented_labels.append(" ".join(a_label))
        # print(len("".join(a_words)), len(a_label))

    #随机插入ri
    for _ in range(num_new_per_technique):
        a_words, a_label = random_insertion_tc(words, label.copy(), n_ri)
        augmented_sentences.append(''.join(a_words))
        augmented_labels.append(" ".join(a_label))
        # print(len("".join(a_words)), len(a_label))
    
    #随机交换rs
    for _ in range(num_new_per_technique):
        a_words, a_label = random_swap_tc(words, label.copy(), n_rs)
        augmented_sentences.append(''.join(a_words))
        augmented_labels.append(" ".join(a_label))
        # print(len("".join(a_words)), len(a_label))

   
    # #随机删除rd
    for _ in range(num_new_per_technique):
        a_words, a_label = random_deletion_tc(words, label.copy(), p_rd)
        augmented_sentences.append(''.join(a_words))
        augmented_labels.append(" ".join(a_label))
        # print(len("".join(a_words)), len(a_label))
    

    augmented_sentences.append(sentence)
    augmented_labels.append(label_cp)


    return augmented_sentences, augmented_labels


def data_augment_eda_for_tc(input_file, output_file, num_aug):
    #停用词列表，默认使用哈工大停用词表
    f = open('stopwords/hit_stopwords.txt')
    stop_words = list()
    for stop_word in f.readlines():
        stop_words.append(stop_word[:-1])
    
    augmented_data = []
    datas = json.load(open(input_file, "r", encoding="utf-8"))
    for data in datas:
        texts, labels = eda_tc(sentence=data["text"], label=data["label"], stop_words=stop_words, num_aug=num_aug)
        id = data["id"] if "id" in data else ""
        augmented_data.append(data)
        for i, text in enumerate(texts):
            label = labels[i]
            if id != "":
                new_id = f"{id}.augment_eda{i}"
                augmented_data.append({"text":text, "label":label, "id":new_id})
            else:
                augmented_data.append({"text":text, "label":label})
    datas = json.load(open(output_file, "r", encoding="utf-8"))
    datas += augmented_data
    json.dump(datas, open(output_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)





if __name__ == "__main__":

    # 9:1分割训练集验证集
    integrate_data("../data/business_rules/json_for_rule_extraction/", "../data/rule_extraction_train_base.json", "../data/rule_extraction_validate.json", "../data/business_rules/json_for_rule_filtering/")

    # 数据增强训练集
    data_augment_nlpcda("../data/rule_extraction_train_base.json", "../data/rule_extraction_train_augmented.json", augument_size=20)
    data_augment_eda_for_tc("../data/rule_extraction_train_base.json", "../data/rule_extraction_train_augmented.json", num_aug=9)