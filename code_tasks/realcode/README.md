# RealCode Benchmark

## Description

**RealCode** is a benchmark designed to evaluate the code generation capabilities of language models in real-world GitHub repositories. The evaluation process assesses the functional correctness of generated code by running repository-specific tests. RealCode Eval allows researchers and practitioners to gauge how well their models can complete code snippets based on real repository contexts, including function signatures, docstrings, and surrounding code.


## Homepage
[Visit Homepage](https://mera.a-ai.ru)

## License
MIT License

---

## Installation and Setup

Before running the evaluation, ensure that your environment is set up correctly.

### Prerequisites
- Python 3.9 or higher.
- [Conda](https://docs.conda.io/en/latest/) for managing environments.
- A running instance of the VLLM server.
- Install the `repotest` package:
  [Github](ssh://git@gitlab.ai.cloud.ru:2222/rnd-core-team/plp/repotest.git)

### Installing lm-eval with API Support
   ```bash
   pip install lm-eval[api]
   ```
  or
   ```bash
   pip install -e ."[api]"
   ```

### Using an Existing Dataset

To use an existing dataset, update the `realcode.yaml` configuration file located in `code_tasks/realcode/`. Below are the parameters you need to modify.

#### Parameters to Update

1. **`filter_list`**: This section defines the evaluation process. Key parameters include:

   - `working_dir`: Directory for evaluation.
   - `generations_output_filepath`: Path for generated code output.
   - `metrics_output_filepath`: Path for evaluation metrics output.
   - `html_output_filepath`: Path for HTML report output.
   - `mode`: Evaluation mode (e.g., `docker`).
   - `n_jobs`: Number of parallel jobs for evaluation.
   - `gen_columns`: Columns containing generated code (e.g., `["gen"]`).

   Example:
   ```yaml
   filter_list:
     - name: "evaluation"
       filter:
         - function: extract_from_tag
         - function: scoring
           working_dir: working_dir
           generations_output_filepath: ./workspace/data/generations_rt.json
           metrics_output_filepath: ./workspace/data/metrics_rt.json
           html_output_filepath: ./workspace/data/metrics_rt.html
           mode: docker
           n_jobs: 5
           gen_columns: ["gen"]
           raise_exception: true
           n_jobs_build: 5
           enable_full_logs: false
         - function: "take_first"
   ```

### How to Evaluate

1. Evaluate in FG (Function Generation) Mode

Run the following command to evaluate your model in Function Generation mode:

```bash
lm_eval \
  --model local-completions \
  --model_args model=Qwen2.5-32B-Instruct,base_url=http://localhost:8000/v1/completions,num_concurrent=1000,max_retries=3,tokenized_requests=True,max_length=10000,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-32B-Instruct,timeout=1000 \
  --tasks realcode \
  --batch_size auto \
  --trust_remote_code \
  --gen_kwargs max_tokens=1024 \
  --log_samples \
  --output_path data/out \
  --include_path=./code_tasks \
  --apply_chat_template
```

or in chat mode:

```bash
lm_eval --model local-chat-completions \
      --model_args model=Qwen/Qwen2.5-Coder-32B-Instruct,base_url=http://localhost:8000/v1/chat/completions,num_concurrent=1000,max_retries=3,max_length=10000,max_gen_toks=1024,timeout=1000 \
      --tasks realcode \
      --batch_size auto \
      --trust_remote_code \
      --gen_kwargs max_tokens=1024 \
      --log_samples \
      --output_path data/out \
      --include_path=./code_tasks \
      --apply_chat_template
```



