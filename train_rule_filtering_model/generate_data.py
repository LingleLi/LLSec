import json
import os
import random
import jieba
import synonyms

# 读取一个目录，按照句号分割，生成sequence_classification文件



# 将所有的数据按照9：1分成训练集和测试集
def integrate_data(in_dir: str, train_file: str, validate_file: str):
    all_rules = []
    for file in os.listdir(in_dir):
        if "finish" in file:
            rules = json.load(open(in_dir + file, "r", encoding="utf-8"))
            all_rules += rules
    random.shuffle(all_rules)
    rule_num = len(all_rules)
    train_data, validate_data = all_rules[:int(rule_num/10*9)], all_rules[int(rule_num/10*9):]
    print(f"原始数据：训练集有数据{len(train_data)}条，验证集有数据{len(validate_data)}条。")
    json.dump(train_data, open(train_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(validate_data, open(validate_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)



def get_synonyms(word):
    return synonyms.nearby(word)[0]


# 同义词替换
# 替换一个语句中的n个单词为其同义词
def synonym_replacement_sc(words, n, stop_words):
    new_words = words.copy()
    random_word_list = list(set([word for word in words if word not in stop_words]))     
    random.shuffle(random_word_list)
    num_replaced = 0  
    for random_word in random_word_list:          
        synonyms = get_synonyms(random_word)
        if len(synonyms) >= 1:
            synonym = random.choice(synonyms)   
            new_words = [synonym if word == random_word else word for word in new_words]   
            num_replaced += 1
        if num_replaced >= n: 
            break

    sentence = ' '.join(new_words)
    new_words = sentence.split(' ')

    return new_words


# 随机插入
# 随机在语句中插入n个词
def random_insertion_sc(words, n):
    new_words = words.copy()
    for _ in range(n):
        add_word_sc(new_words)
    return new_words

def add_word_sc(new_words):
    synonyms = []
    counter = 0    
    while len(synonyms) < 1:
        random_word = new_words[random.randint(0, len(new_words)-1)]
        synonyms = get_synonyms(random_word)
        counter += 1
        if counter >= 10:
            return
    random_synonym = random.choice(synonyms)
    random_idx = random.randint(0, len(new_words)-1)
    new_words.insert(random_idx, random_synonym)


# Random swap
# Randomly swap two words in the sentence n times
def random_swap_sc(words, n):
    new_words = words.copy()
    for _ in range(n):
        new_words = swap_word_sc(new_words)
    return new_words

def swap_word_sc(new_words):
    random_idx_1 = random.randint(0, len(new_words)-1)
    random_idx_2 = random_idx_1
    counter = 0
    while random_idx_2 == random_idx_1:
        random_idx_2 = random.randint(0, len(new_words)-1)
        counter += 1
        if counter > 3:
            return new_words
    new_words[random_idx_1], new_words[random_idx_2] = new_words[random_idx_2], new_words[random_idx_1] 
    return new_words


# 随机删除
# 以概率p删除语句中的词
def random_deletion_sc(words, p):

    if len(words) == 1:
        return words

    new_words = []
    for word in words:
        r = random.uniform(0, 1)
        if r > p:
            new_words.append(word)

    if len(new_words) == 0:
        rand_int = random.randint(0, len(words)-1)
        return [words[rand_int]]

    return new_words



#EDA函数
def eda_sc(sentence, alpha_sr=0.1, alpha_ri=0.1, alpha_rs=0.1, p_rd=0.1, num_aug=9):
    seg_list = jieba.cut(sentence)
    seg_list = " ".join(seg_list)
    words = list(seg_list.split())
    num_words = len(words)

    augmented_sentences = []
    num_new_per_technique = int(num_aug/4)+1
    n_sr = max(1, int(alpha_sr * num_words))
    n_ri = max(1, int(alpha_ri * num_words))
    n_rs = max(1, int(alpha_rs * num_words))

    f = open('stopwords/hit_stopwords.txt')
    stop_words = list()
    for stop_word in f.readlines():
        stop_words.append(stop_word[:-1])

    
    #同义词替换sr
    for _ in range(num_new_per_technique):
        a_words = synonym_replacement_sc(words, n_sr, stop_words)
        augmented_sentences.append(''.join(a_words))

    #随机插入ri
    for _ in range(num_new_per_technique):
        a_words = random_insertion_sc(words, n_ri)
        augmented_sentences.append(''.join(a_words))
    
    #随机交换rs
    for _ in range(num_new_per_technique):
        a_words = random_swap_sc(words, n_rs)
        augmented_sentences.append(''.join(a_words))

   
    #随机删除rd
    for _ in range(num_new_per_technique):
        a_words = random_deletion_sc(words, p_rd)
        augmented_sentences.append(''.join(a_words))


    if num_aug >= 1:
        augmented_sentences = augmented_sentences[:num_aug]
    else:
        keep_prob = num_aug / len(augmented_sentences)
        augmented_sentences = [s for s in augmented_sentences if random.uniform(0, 1) < keep_prob]

    augmented_sentences.append(sentence)

    return augmented_sentences


# 数据增强
def data_augment_eda_for_sc(input_file, output_file, num_aug):
    augmented_data = []
    datas = json.load(open(input_file, "r", encoding="utf-8"))
    for data in datas:
        texts = eda_sc(sentence=data["text"], num_aug=num_aug)
        id = data["id"] if "id" in data else ""
        augmented_data.append(data)
        rule_type = data["type"]
        for i, text in enumerate(texts):
            if id != "":
                new_id = f"{id}.augment_eda{i}"
                augmented_data.append({"text":text, "type":rule_type, "id":new_id})
            else:
                augmented_data.append({"text":text, "type":rule_type})
    json.dump(augmented_data, open(output_file, "w", encoding="utf-8"), ensure_ascii=False, indent=4)



if __name__ == "__main__":

    # 9:1分割训练集验证集
    integrate_data("../data/business_rules/json_for_rule_filtering/", "../data/rule_filtering_train_base.json", "../data/rule_filtering_validate.json")

    # 数据增强训练集
    data_augment_eda_for_sc("../data/rule_filtering_train_base.json", "../data/rule_filtering_train_augmented.json", num_aug=9)