export CUDA_VISIBLE_DEVICES=0 
export LINTER_PATH="/home/akharitonov/.conda/envs/mera-code-yabloco/bin/flake8" 
export JUDGE_FEW_SHOT_PATH="/home/akharitonov/MERA_CODE_exp/datasets/few_shot.json" 
export JUDGE_URL="http://77.223.120.158:50000/v1" 
export JUDGE_MODEL_NAME="qwen-coder-32b"
export MODEL_URL="http://0.0.0.0:8000/v1"
export MODEL_NAME="Qwen/Qwen2.5-Coder-0.5B-Instruct" 
export MERA_FOLDER="$PWD/mera_results/$MODEL_NAME" 
export MERA_MODEL_STRING="model=$MODEL_NAME,base_url=$MODEL_URL/completions,num_concurrent=1000,max_retries=3,tokenized_requests=True,tokenizer=Qwen/Qwen2.5-Coder-0.5B-Instruct" 
export MERA_COMMON_SETUP="--model local-completions --predict_only --log_samples --seed 1234 --verbosity ERROR --trust_remote_code --apply_chat_template"
bash scripts/run_benchmark.sh