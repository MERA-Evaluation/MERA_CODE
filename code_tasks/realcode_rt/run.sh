#!/bin/bash
cd ../..;
lm_eval --model local-completions \
      --model_args model=/home/jovyan/adamenko/models/gigacode_chat_pro_v1.4_32b_coder,base_url=http://localhost:6021/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-32B-Instruct \
      --tasks realcode_rt \
      --batch_size 16 \
      --trust_remote_code \
      --gen_kwargs max_tokens=1024 \
      --log_samples \
      --output_path data/realcode_rt \
      --include_path=./code_tasks \
      --verbosity DEBUG \
      --limit 1000

# ### Вопросы:
# Наверное стоит перенести этот файл явно в эту папку ?:
# repotest.manager.realcode_python_task_manager.TaskManagerRealcode 
# > обсудили, нет, не стоит

# ### Замеры docker
# ### model=/home/jovyan/adamenko/models/gigacode_chat_pro_v1.4_32b_coder,base_url=http://localhost:6021/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-32B-Instruct,trust_remote_code=True), gen_kwargs: (max_tokens=1024)

# |   Tasks   |Version|  Filter  |n-shot|       Metric        |   | Value  |   |Stderr|
# |-----------|------:|----------|-----:|---------------------|---|-------:|---|------|
# |realcode_rt|      1|evaluation|     0|num_of_samples       |↑  |880.0000|±  |   N/A|
# |           |       |evaluation|     0|pass_dry_run         |↑  |  0.9932|±  |0.0028|
# |           |       |evaluation|     0|pass_gen             |↑  |  0.4455|±  |0.0168|
# |           |       |evaluation|     0|pass_gt              |↑  |  0.9966|±  |0.0020|
# |           |       |evaluation|     0|pass_return_empty_str|↑  |  0.0545|±  |0     |

# ### Замеры conda
# ### model=/home/jovyan/adamenko/models/gigacode_chat_pro_v1.4_32b_coder,base_url=http://localhost:6021/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-32B-Instruct,trust_remote_code=True), gen_kwargs: (max_tokens=1024)
# |   Tasks   |Version|  Filter  |n-shot|       Metric        |   | Value  |   |Stderr|
# |-----------|------:|----------|-----:|---------------------|---|-------:|---|------|
# |realcode_rt|      1|evaluation|     0|num_of_samples       |↑  |880.0000|±  |   N/A|
# |           |       |evaluation|     0|pass_dry_run         |↑  |  0.9841|±  |0.0042|
# |           |       |evaluation|     0|pass_gen             |↑  |  0.4455|±  |0.0168|
# |           |       |evaluation|     0|pass_gt              |↑  |  0.9966|±  |0.0020|
# |           |       |evaluation|     0|pass_return_empty_str|↑  |  0.0648|±  |0.0083|
# |           |       |evaluation|     0|pass_return_pass     |↑  |  0.0568|±  |0.0078|
# |           |       |evaluation|     0|status               |↑  |  0.9966|±  |0.0020|