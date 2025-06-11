# Java TestGen Benchmark

## Description

**Java TestGen** is a benchmark for evaluating code java test generation.


### Dataset Details
- **Tasks**: 227 Java code generation tasks.
- **Dataset Schema** includes:
  - `instance_id`: Unique identifier.
  - `repo`: GitHub repository source.
  - `base_commit`: Commit hash for reproducibility.
  - `command`: Command to execute tests.
  - `image`: Docker image used for testing.
  - `patch`: Generated code diff by the model.

## Installation and Setup

### Prerequisites
- Docker installed and running.
- Python package installation:
  ```bash
  pip install repotest-0.3.19-py3-none-any.whl
  ```

### Evaluate Model with lm_eval

Run evaluation with the following command:

```bash
lm_eval \
  --model local-completions \
  --model_args model=Qwen/Qwen2.5-Coder-14B-Instruct,base_url=http://localhost:8187/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-Coder-14B-Instruct \
  --tasks java_testgen \
  --batch_size 8 \
  --trust_remote_code \
  --gen_kwargs max_tokens=1024 \
  --log_samples \
  --output_path data/out \
  --include_path=./code_tasks \
  --apply_chat_template
```

#### Example output metrics



### Notes
- Artifacts (cloned repositories) stored at `~/.cache/repotest`.
- Maven dependencies cached using Docker volume `maven_cache`.
- The first run may take longer due to initial Maven dependency downloads.

## License
?