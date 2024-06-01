from specification_generation.main import main
import time
import os


def generate_specification():
    for file in sorted(os.listdir("exp1_data/our_inputs/")):
        if "input.json" in file:

            # if "data2" not in file:
            #     continue
            print(f"处理文件{file}")
            filename = file[:5]
            begin_time = time.time()

            main(input_file="exp1_data/our_inputs/" + file, output_file="exp1_data/our_outputs/" + filename + "_output.json", relation_file = "exp1_data/our_outputs/" + filename + "_relation.json", setting_file="exp1_data/our_inputs/" + filename + "_setting.json", explicit_relation_file="exp1_data/our_outputs/" + filename + "_explicit_relation.json" ,implicit_relation_file="exp1_data/our_outputs/" + filename + "_implicit_relation.json")

            time_consume = time.time() - begin_time
            print(f"《{filename}》总共消耗时间: {time_consume}")



if __name__ == "__main__":
    generate_specification()