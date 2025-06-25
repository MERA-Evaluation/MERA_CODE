# RealCodeJava

## Требования (python)
```
repotest >= 0.4.3
```

## Настройка окружения
```bash
conda create -p ~/conda_env/repotest python=3.12 pip
conda install conda-forge::openjdk=22 conda-forge::maven

# Пока так
git clone <[repotest]>
pip install -e repotest

git clone <[MERA_CODE]>
cd MERA_CODE
git submodule init
git submodule update
pip install -e lm-evaluation-harness

git config --global user.email "your_average_joe@gmail.com"
git config --global user.name "Joe"
```


### Пример запуска замеров
```bash
export HF_TOKEN="INSERT_YOUR_TOKEN"

# Иначе падает в конце из-за большого числа обращений к файловой системе
ulimit -n 65000

python -m lm_eval \
    --model local-completions \
    --model_args model=Qwen/Qwen2.5-Coder-14B-Instruct,base_url=http://localhost:8001/v1/completions,num_concurrent=32,max_retries=3,tokenized_requests=True,max_length=16384,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-14B-Instruct \
    --tasks realcode_java \
    --batch_size 32 \
    --output_path /path/to/outputs/realcode_java \
    --trust_remote_code \
    --log_samples \
    --include_path=/path/to/MERA_CODE/code_tasks \
    --apply_chat_template
```

А модель для замеров сервится, например, так
```bash
CUDA_VISIBLE_DEVICES=1 vllm serve Qwen/Qwen2.5-Coder-14B-Instruct \
  --seed=42 \
  --port=8001 \
  --max-model-len 16384 \
  --enable-prefix \
  --gpu-memory-utilization 0.9
```