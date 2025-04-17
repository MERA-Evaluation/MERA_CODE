#!/usr/bin/bash
cd /data/adam/git/MERA_CODE
source activate lm_eval
lm_eval --model local-completions \
      --model_args model=/home/jovyan/adamenko/models/gigacode_chat_pro_v1.4_32b_coder,base_url=http://localhost:6021/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-32B-Instruct \
      --tasks realcode_rt \
      --batch_size 16 \
      --trust_remote_code \
      --gen_kwargs max_tokens=1024 \
      --log_samples \
      --output_path data/realcode_rt \
      --include_path=./code_tasks \
      --apply_chat_template \
      --verbosity DEBUG \
      --limit 5
# lm_eval --model local-completions \
# --model_args model=/home/jovyan/adamenko/models/gigacode_chat_pro_v1.4_32b_coder,base_url=http://localhost:6021/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-32B-Instruct \
# --tasks realcode \
# --batch_size 16 \   
# --trust_remote_code \
# --gen_kwargs max_tokens=1024 \
# --log_samples \
# --output_path data/realcode_rt \
# --include_path=./code_tasks \
# --apply_chat_template \
# --limit 2