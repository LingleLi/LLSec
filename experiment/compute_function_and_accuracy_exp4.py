from experiment.compute_function_and_accuracy_exp1 import compute_acc_ours, compute_acc_llm


def exp4():
    summary_f = open('exp4_data/table6.csv', 'w', encoding="utf-8")
    
    ours_num, ours_acc = compute_acc_ours(our_dir="exp4_data/our_outputs", specification_dir="exp4_data/specification")
    # ours_num = [579, 2497, 368, 537, 3062]
    # ours_acc = [0.8295093795093794, 0.7668083900226759, 0.7767195767195765, 0.8160074773711137, 0.7984335839598997]

    llm_num, llm_acc = compute_acc_llm(llm_dir="exp4_data/llm_result", specification_dir="exp4_data/specification")

    # llm_num = {'glm4': [56, 76, 62, 36, 52], 'gpt4': [48, 30, 27, 20, 25]}
    # llm_acc = {'glm4': [0.689303751803752, 0.6985260770975056, 0.6291005291005293, 0.6072281254099436, 0.6920426065162912], 'gpt4': [0.7315115440115445, 0.7211734693877553, 0.6302380952380952, 0.6666863439590712, 0.684022556390978]}

    summary_f.write("数据集,数据集特征,,,,,GPT-4,,GLM-4,,LLSec,\n")
    summary_f.write(",数据集名称,来源,#规则,#DF,#依赖关系,#DF,FPI(%),#DF,FPI(%),#DF,FPI(%)\n")
    
    summary_f.write(f"1,纽约证券交易所股票交易规则,《纽约交易所规则》,10,44,7,{llm_num['gpt4'][0]},{round(llm_acc['gpt4'][0]*100, 2)},{llm_num['glm4'][0]},{round(llm_acc['glm4'][0]*100, 2)},{ours_num[0]},{round(ours_acc[0]*100, 2)}\n")
    summary_f.write(f"2,纽约证券交易所交易和结算规则,《纽约交易所规则》,9,28,4,{llm_num['gpt4'][1]},{round(llm_acc['gpt4'][1]*100, 2)},{llm_num['glm4'][1]},{round(llm_acc['glm4'][1]*100, 2)},{ours_num[1]},{round(ours_acc[1]*100, 2)}\n")
    summary_f.write(f"3,东京证券交易所股票经营规定,《东京证券交易所经营规定》,12,30,6,{llm_num['gpt4'][2]},{round(llm_acc['gpt4'][2]*100, 2)},{llm_num['glm4'][2]},{round(llm_acc['glm4'][2]*100, 2)},{ours_num[2]},{round(ours_acc[2]*100, 2)}\n")
    summary_f.write(f"4,东京证券交易所债券经营规定,《东京证券交易所经营规定》,9,22,5,{llm_num['gpt4'][3]},{round(llm_acc['gpt4'][3]*100, 2)},{llm_num['glm4'][3]},{round(llm_acc['glm4'][3]*100, 2)},{ours_num[3]},{round(ours_acc[3]*100, 2)}\n")
    summary_f.write(f"5,香港交易所交易机制,《香港交易所交易机制》,12,38,5,{llm_num['gpt4'][4]},{round(llm_acc['gpt4'][4]*100, 2)},{llm_num['glm4'][4]},{round(llm_acc['glm4'][4]*100, 2)},{ours_num[4]},{round(ours_acc[4]*100, 2)}\n")


if __name__ == "__main__":
    exp4()