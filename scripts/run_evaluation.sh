export CUDA_VISIBLE_DEVICES=0 
export LINTER_PATH="/home/akharitonov/.conda/envs/mera-code-yabloco/bin/flake8" 
export JUDGE_FEW_SHOT_PATH="/home/akharitonov/MERA_CODE_exp/datasets/few_shot.json" 
export JUDGE_URL="http://77.223.120.158:50000/v1/" 
export JUDGE_MODEL_NAME="/Qwen2.5-Coder-32B-Instruct" 
export MERA_FOLDER="$PWD/mera_results/deepseek-coder-1.3b-instruct" 
export MERA_MODEL_STRING="pretrained=deepseek-ai/deepseek-coder-1.3b-instruct,dtype=bfloat16,tensor_parallel_size=1,gpu_memory_utilization=0.45" 
export MERA_COMMON_SETUP="--model vllm --device cuda --batch_size=1 --predict_only --log_samples --seed 1234 --verbosity ERROR --trust_remote_code --limit 10"
bash scripts/run_benchmark.sh