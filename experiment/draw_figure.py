import matplotlib.pyplot as plt
import matplotlib as mpl

zhfont = mpl.font_manager.FontProperties(fname='./rules_cache/chinese.simhei.ttf')
plt.rcParams['axes.unicode_minus'] = False



def draw_rule_filtering_figure():
    methods = ['Mengzi', 'Llama2', 'GPT-4', 'GLM-4']

    y = []
    ours_f = open("rule_filtering_data/ours_result/ours_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in ours_f:
        if "acc" in line:
            y.append(float(line.split(" ")[1]))
    chatgpt_f = open("rule_filtering_data/chatgpt_result/chatgpt_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in chatgpt_f:
        if "acc" in line:
            y.append(float(line.split(" ")[-1]))
    y = y[:-3] + [y[-2], y[-3], y[-1]]
    chatglm_f = open("rule_filtering_data/chatglm_result/chatglm_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in chatglm_f:
        if "acc" in line:
            y.append(float(line.split(" ")[-1]))
    # 10 366 5
    y = y[:-3] + [y[-2], y[-3], y[-1]]
    y = [yi * 100 for yi in y]

    plt.figure(figsize=(8,5))
    bar_width = 0.2
    x = [0,0.7,1.65,2.7]

    # fine-tuning
    plt.bar([x[0], x[1]+bar_width/2+0.05], [y[0], y[2]], bar_width, align='center', color="#4A8DB9", label='fine-tuning', hatch="*")
    # lora
    plt.bar([x[1]-bar_width/2-0.05], y[1], bar_width, align='center', color="#13254C", label='lora', hatch="XX")
    # few shot
    plt.bar([x[2]-bar_width-0.1, x[3]-bar_width-0.1], [y[3],y[6]], bar_width, align='center', color="#E9D781", label='5-shot', alpha=0.8, hatch="//")
    plt.bar([x[2], x[3]], [y[4],y[7]], bar_width, align='center', color="#F0BB40", label='10-shot', hatch="\\")
    plt.bar([x[2]+bar_width+0.1, x[3]+bar_width+0.1], [y[5],y[8]], bar_width, align='center', color="#F08218", label='doc-shot')

    for a, b in zip([x[0], x[1]-bar_width/2-0.1, x[1]+bar_width/2+0.1, x[2]-bar_width-0.15, x[2], x[2]+bar_width+0.1, x[3]-bar_width-0.15, x[3], x[3]+bar_width+0.1], y):
        plt.text(a, b+1, round(b, 2), ha='center', va='bottom', fontsize=15, color='black', rotation=0)


    plt.xlabel('方法', fontsize=20, fontproperties=zhfont)
    plt.ylabel('准确率(%)', fontsize=20, fontproperties=zhfont)
    plt.xticks(x, methods, fontsize=20)
    plt.yticks([0, 20, 40, 60, 80, 100], fontsize=20)
    plt.ylim(0, 120)
    plt.legend(fontsize=15, loc='upper right', ncol=2, borderaxespad=0.1, handletextpad=0.1, columnspacing=0.1, labelspacing=0.1)
    plt.tight_layout()
    plt.savefig("rule_filtering_data/figure_6a.png")


def draw_rule_extraction_figure():
    methods = ['Mengzi', 'Llama2', 'GPT-4', 'GLM-4']

    y = []
    ours_f = open("rule_extraction_data/ours_result/ours_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in ours_f:
        if "precision" in line:
            y.append(float(line.split(" ")[5][:-1]))
    t=y[2]
    y[2]=y[1]
    y[1]=t

    chatgpt_f = open("rule_extraction_data/chatgpt_result/chatgpt_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in chatgpt_f:
        if "precision" in line:
            y.append(float(line.split(" ")[5][:-1]))
    y = y[:-3] + [y[-2], y[-3], y[-1]]
    chatglm_f = open("rule_extraction_data/chatglm_result/chatglm_acc.txt", "r", encoding="utf-8").read().split("\n")
    for line in chatglm_f:
        if "precision" in line:
            y.append(float(line.split(" ")[5][:-1]))
    # 10 366 5
    y = y[:-3] + [y[-2], y[-3], y[-1]]
    y = [yi * 100 for yi in y]

    plt.figure(figsize=(8,5))
    bar_width = 0.2
    x = [0,0.7,1.65,2.7]

    # fine-tuning
    plt.bar([x[0], x[1]+bar_width/2+0.05], [y[0], y[2]], bar_width, align='center', color="#4A8DB9", label='fine-tuning', hatch="*")
    # lora
    plt.bar([x[1]-bar_width/2-0.05], y[1], bar_width, align='center', color="#13254C", label='lora', hatch="XX")
    # few shot
    plt.bar([x[2]-bar_width-0.1, x[3]-bar_width-0.1], [y[3],y[6]], bar_width, align='center', color="#E9D781", label='5-shot', alpha=0.8, hatch="//")
    plt.bar([x[2], x[3]], [y[4],y[7]], bar_width, align='center', color="#F0BB40", label='10-shot', hatch="\\")
    plt.bar([x[2]+bar_width+0.1, x[3]+bar_width+0.1], [y[5],y[8]], bar_width, align='center', color="#F08218", label='doc-shot')

    for a, b in zip([x[0], x[1]-bar_width/2-0.05, x[1]+bar_width/2+0.05, x[2]-bar_width-0.1, x[2], x[2]+bar_width+0.1, x[3]-bar_width-0.1, x[3], x[3]+bar_width+0.1], y):
        plt.text(a, b+1, round(b, 2), ha='center', va='bottom', fontsize=15, color='black', rotation=0)


    plt.xlabel('方法', fontsize=20, fontproperties=zhfont)
    plt.ylabel('准确率(%)', fontsize=20, fontproperties=zhfont)
    plt.xticks(x, methods, fontsize=20)
    plt.yticks([0, 20, 40, 60, 80, 100], fontsize=20)
    plt.ylim(0, 135)
    plt.legend(fontsize=15, loc='upper right', ncol=2, borderaxespad=0.1, handletextpad=0.1, columnspacing=0.1, labelspacing=0.1)
    plt.tight_layout()
    plt.savefig("rule_extraction_data/figure_6b.png")



if __name__ == "__main__":
    draw_rule_filtering_figure()
    draw_rule_extraction_figure()