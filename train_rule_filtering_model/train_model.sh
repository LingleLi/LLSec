#!/bin/bash

# run command: nohup ./train_model.sh >./output/train_model.log &

python train.py --output_dir model/ --disable_tqdm True --model model/mengzi-bert-base-fin/ --num_train_epochs 50 --lr_scheduler_type constant --weight_decay 0.001 --train_dataset ../data/rule_filtering_train_augmented.json --validate_dataset ../data/rule_filtering_validate.json

python train.py --output_dir model/ --disable_tqdm True --model model/mengzi-bert-base-fin/ --num_train_epochs 50 --lr_scheduler_type linear --weight_decay 0.001 --train_dataset ../data/rule_filtering_train_augmented.json --validate_dataset ../data/rule_filtering_validate.json

python train.py --output_dir model/ --disable_tqdm True --model model/mengzi-bert-base-fin/ --num_train_epochs 50 --lr_scheduler_type cosine --weight_decay 0.001 --train_dataset ../data/rule_filtering_train_augmented.json --validate_dataset ../data/rule_filtering_validate.json

cd output
rm -rf checkpoint-*
cd ..