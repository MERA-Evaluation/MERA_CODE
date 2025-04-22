#!/bin/bash
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
      --limit 10

n_parralel_process = 8
|   Tasks   |Version|  Filter  |n-shot|       Metric        |   |Value |   |Stderr|
|-----------|------:|----------|-----:|---------------------|---|-----:|---|-----:|
|realcode_fg|      1|evaluation|     0|pass_dry_run         |↑  |0.9966|±  |0.0020|
|           |       |evaluation|     0|pass_gen             |↑  |0.3932|±  |0.0165|
|           |       |evaluation|     0|pass_gt              |↑  |1.0000|±  |0.0000|
|           |       |evaluation|     0|pass_pass            |↑  |0.0455|±  |0.0070|
|           |       |evaluation|     0|pass_return_empty_str|↑  |0.0557|±  |0.0077|

|   Tasks   |Version|  Filter  |n-shot|       Metric        |   |Value |   |Stderr|
|-----------|------:|----------|-----:|---------------------|---|-----:|---|-----:|
|realcode_fg|      1|evaluation|     0|pass_dry_run         |↑  |0.9966|±  |0.0020|
|           |       |evaluation|     0|pass_gen             |↑  |0.3920|±  |0.0165|
|           |       |evaluation|     0|pass_gt              |↑  |1.0000|±  |0.0000|
|           |       |evaluation|     0|pass_pass            |↑  |0.0443|±  |0.0069|
|           |       |evaluation|     0|pass_return_empty_str|↑  |0.0545|±  |0.0077|