#!/bin/bash

# nohup bash run_rule_extraction.sh >./output/run_rule_extraction.log &

# 模型保存目录、预测数据目录、训练数据文件、验证数据文件
output_dir=./output
predict_dir=./predict_data/rule_extraction
train_files=../data/rule_extraction_llama2_train.csv
validation_files=../data/rule_extraction_llama2_validate.csv
model_dir=./model/rule_extraction

# 如果文件不存在，创建
if [ ! -d ${output_dir} ];then  
    mkdir ${output_dir}
fi
if [ ! -d ${predict_dir} ];then  
    mkdir ${predict_dir}
fi
if [ ! -d ${model_dir} ];then  
    mkdir ${model_dir}
fi

# 训练模型
python train_lora_model.py \
    --model_name_or_path ../lora_train_llama2_model/model/Atom-7B \
    --train_files ${train_files} \
    --validation_files ${validation_files} \
    --per_device_train_batch_size 1 \
    --per_device_eval_batch_size 1 \
    --do_train \
    --do_eval \
    --use_fast_tokenizer false \
    --output_dir ${output_dir} \
    --model_dir ${model_dir} \
    --evaluation_strategy  steps \
    --max_eval_samples 800 \
    --learning_rate 1e-4 \
    --gradient_accumulation_steps 8 \
    --num_train_epochs 10 \
    --warmup_steps 400 \
    --load_in_bits 4 \
    --lora_r 8 \
    --lora_alpha 16 \
    --target_modules q_proj,k_proj,v_proj,o_proj,down_proj,gate_proj,up_proj \
    --logging_dir ${output_dir}/logs \
    --logging_strategy steps \
    --logging_steps 10 \
    --save_strategy steps \
    --preprocessing_num_workers 10 \
    --save_steps 100 \
    --eval_steps 100 \
    --save_total_limit 10 \
    --seed 42 \
    --ddp_find_unused_parameters false \
    --block_size 2048 \
    --report_to tensorboard \
    --overwrite_output_dir \
    --ignore_data_skip true \
    --bf16 \
    --gradient_checkpointing \
    --bf16_full_eval \
    --ddp_timeout 18000000 \
    --torch_dtype float16 \
    --test_output_file ${predict_dir}/predict_result_framework.txt \
    --disable_tqdm true


# 初始化一个空数组来存储所有文件的整数部分
file_numbers=()
# 这里的目录需要替换成你实际的目录
for file in $(find $model_dir -type d -name 'best_lora_model_*' | grep -oP 'best_lora_model_\K\d+'); do
    file_numbers+=("$file")
done
# 如果没有找到任何文件，则退出脚本
if [ ${#file_numbers[@]} -eq 0 ]; then
    echo "没有找到匹配的文件。"
    exit 1
fi
# 使用sort和tail找到最大的整数
max_number=$(printf "%s\n" "${file_numbers[@]}" | sort -n | tail -1)
# 构建最大的文件名
filename="best_lora_model_$max_number"





# 使用4bit加载原始模型并与lora运行时合并预测
#*******注意：这是和训练时的加载模式相同的模式********
python predict.py \
    --model_name_or_path ${model_dir}/${filename} \
    --mode 4bit-lora \
    --tokenizer_fast false \
    --eval_dataset ${validation_files} \
    --prediction_file ${predict_dir}/predict_result_4bit_load_lora.json

# 使用不量化加载原始模型并与lora运行时合并预测
python predict.py \
    --model_name_or_path ${model_dir}/${filename} \
    --mode lora \
    --tokenizer_fast false \
    --eval_dataset ${validation_files} \
    --prediction_file ${predict_dir}/predict_result_normal_load_lora.json



cd output
rm -rf checkpoint-*
cd ..





# # 合并lora模型和原始模型，原始模型4位量化
# python merge.py \
#     --adapter_model_name ${output_dir}/best_lora_model \
#     --output_name ${output_dir}/best_model_4bit \
#     --mode 4bit