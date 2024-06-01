#!/bin/bash

# run command: nohup ./train_model.sh >./output/train_model.log &

python train.py --output_dir ./output --split \  --disable_tqdm True --model ./model/mengzi-bert-base-fin --num_train_epochs 20 --lr_scheduler_type constant --weight_decay 0.002 --train_dataset ../data/rule_extraction_train_augmented.json --validate_dataset ../data/rule_extraction_validate.json --learning_rate 3e-5

python train.py --output_dir ./output --split \  --disable_tqdm True --model ./model/mengzi-bert-base-fin --num_train_epochs 20 --lr_scheduler_type linear --weight_decay 0.002 --train_dataset ../data/rule_extraction_train_augmented.json --validate_dataset ../data/rule_extraction_validate.json --learning_rate 3e-5

python train.py --output_dir ./output --split \  --disable_tqdm True --model ./model/mengzi-bert-base-fin --num_train_epochs 20 --lr_scheduler_type cosine --weight_decay 0.002 --train_dataset ../data/rule_extraction_train_augmented.json --validate_dataset ../data/rule_extraction_validate.json --learning_rate 3e-5

cd output
rm -rf checkpoint-*
cd ..
