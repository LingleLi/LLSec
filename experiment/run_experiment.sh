#!/bin/bash

# run command: nohup bash run_experiment.sh >run_experiment.log &

# case study
python case_study.py

# experiment 1
python generate_specification_exp1.py
python compute_function_and_accuracy_exp1.py

# experiment 2
python compute_sc_LLM_acc.py
python compute_tc_LLM_acc.py
python draw_figure.py

# experiment 3
python generate_specification_exp3.py
python compute_function_and_accuracy_exp3.py

# experiment 4
python generate_specification_exp4.py
python compute_function_and_accuracy_exp4.py