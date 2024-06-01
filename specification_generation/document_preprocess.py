import json
import pdfplumber


def is_id(str):
    # 判断一句话是否是id开头
    str = str.split(" ")[0]
    if str[0]=="第" and "条" in str:
        return True
    if "." not in str:
        return False
    ids = str.split(".")
    for id in ids:
        if not id.isdigit():
            return False
    return True

def read_pdf_to_txt(pdf_file):
    """
    读取并解析pdf文件，将其转化为按照id划分的一个个句子
    pdf_file: 要读取的pdf文件
    ts: 一个字符串，按照id划分的句子之间以"\\n"区分
    """
    s = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            s += f"{page.extract_text()}\n"
    ts = ""
    for i, line in enumerate(s.split("\n")):
        # 什么时候换行呢？
        # 如果是标题、附件等，换行；如果是一个规则的开始（遇到id），则换行
        line = line.strip().replace("：", ":").replace("︰", ":")
        if line[0:2] == "附件":
            if len(line) == 2:
                ts += "\n" + line + "\n"
                continue
            elif line.replace(" ","")[2] == ":" or line.replace(" ","")[2].isdigit():
                ts += "\n" + line.replace(" ","") + "\n"
                continue
        if line == "":
            continue
        if "修订）" == line[-3:]:
            ts += line + "\n"
            continue
        if line[0] == "第" and " " in line and ("章" in line or "节" in line):  # 章节标题
            ts += "\n" + line + "\n"
        elif is_id(line) and ts[-1] == "。":  # 遇到1.1.1这样的
            ts += "\n" + line
        elif line[0] == "—" and line[-1] == "—":
            continue
        else:
            ts += line

    return ts



def read_txt_to_json(txt_data):
    '''
    将txt_data按句划分，写成sci的json格式
    txt_data: 输入数据
    data: 返回的sci数据
    '''
    data = []
    # with open(txt_file, "r", encoding="utf-8") as f:
    #     lines = f.readlines()
    lines = txt_data.split("\n")
    for line in lines:
        if line.strip() == "":
            continue
        line = line.strip().replace("：", ":").replace("︰", ":")
        id = line.split(" ")[0]
        if is_id(id):
            text = "".join(line.split(" ")[1:])
            text = text.replace("。", "。\n")
            texts = text.split("\n")
            for index, text in enumerate(texts):
                if text.strip() != "":
                    d = {"text": text.strip(), "label": "", "type": "", "id": f"{id}_{index}"}
                    data.append(d)
        else:
            text = line.replace("。", "。\n")
            texts = text.split("\n")
            for index, text in enumerate(texts):
                if text.strip() != "":
                    d = {"text": text.strip(), "label": "", "type": ""}
                    data.append(d)
    
    return data




def get_market_variety(s, knowledge):
    market, market_num, variety, variety_num = "", 0, "", 0
    for key in knowledge:
        if key == "交易市场":
            values = knowledge[key]
            for value in values:
                value_count = s.count(value)
                if value_count > market_num:
                    market_num = value_count
                    market = value
        elif key == "交易品种":
            values = knowledge[key]
            for value in values:
                value_count = "\n".join(s.split("\n")[:5]).count(value)
                if value_count > variety_num:
                    variety_num = value_count
                    variety = value
    
    if market_num == 0:
        if "\n".join(s.split("\n")).count("深圳") > "\n".join(s.split("\n")).count("上海"):
            market = "深圳证券交易所"
        elif "\n".join(s.split("\n")).count("深圳") < "\n".join(s.split("\n")).count("上海"):
            market = "上海证券交易所"
        else:
            if "\n".join(s.split("\n")).count("深交所") > "\n".join(s.split("\n")).count("上交所"):
                market = "深圳证券交易所"
            elif "\n".join(s.split("\n")).count("深交所") < "\n".join(s.split("\n")).count("上交所"):
                market = "上海证券交易所"
            else:
                market = "证券交易所"
    if variety_num == 0:
        variety = "证券"
    return {"交易市场": market, "交易品种": variety}


def preprocess(nl_file = None, nl_data = None, knowledge = "../data/knowledge.json"):
    '''
    将自然语言文档（pdf格式）或自然语言输入转化为rule filtering input的格式
    nl_file: pdf格式的自然语言文档
    nl_data: 数组，每个数组元素为一条规则
    sci: 返回转化好的rule filtering input数据
    '''
    know = json.load(open(knowledge, "r", encoding="utf-8"))
    if nl_file is not None and len(nl_file) >= 5 and nl_file[-4:] == ".pdf":
        txt_data = read_pdf_to_txt(nl_file)
        sci = read_txt_to_json(txt_data)
        market_variety = get_market_variety(txt_data, know)
    elif nl_data is not None:
        sci = read_txt_to_json(nl_data)
        market_variety = get_market_variety(nl_data, know)
    else:
        raise ValueError("未指定输入文件或输入文字")

    return sci, market_variety


if __name__ == "__main__":
    sci, market_variety = preprocess(nl_file="rules_cache/深圳证券交易所债券交易规则.pdf")
    json.dump(sci, open("rules_cache/sci.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)
    json.dump(market_variety, open("rules_cache/setting.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4)