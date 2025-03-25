# YABLoCo: Yet Another Benchmark for Long Context Code Generation

## Description

**YABLoCo** is a benchmark designed to evaluate the code generation capabilities of language models in large real-world 
GitHub repositories in C/c++. The evaluation process assesses the functional correctness of generated code by 
running repository-specific tests. The models are asked to generate function bodies given context, 
signature and doc comment. The default `oracle` context contains functions that are called from inside the function 
bodies to generate.

### Key Features
- **Large context**: contains large repositories from 200K to 2,000K LoC,
- **C/C++**: aims function body generation in large repositories in C and C++,
- **Execution-Based Evaluation**: runs independent docker containers to evaluate generated samples,
- **Real-World Repositories**: `bullet3` (C++), `llvm-project` (C++), `openssl` (C), `redis` (C).

### Dataset Details
- **Tasks**: 218 functions to generate
- **Context**:
  - `oracle`: the callees of the functions
- **Ground Truth**: The correct implementation of the function or method (not accessible to the model), while it may deviate from the original code due to macros filtering.
- **Evaluation Metric**: `pass@k` — Compares the number of passed tests between generated and ground-truth code.

## License
MIT License

---

## Installation and Setup

Before running the evaluation, ensure that your environment is set up correctly.

### Prerequisites
- Python 3.9 or higher,
- Docker,
- A running instance of the VLLM server.

### Installing lm-eval with API Support
   ```bash
   pip install lm-eval[api]
   ```
  or
   ```bash
   pip install -e ."[api]"
   ```

### Download Dataset and Setup Environments

```bash
cd MERA_CODE/workspace
git clone -b mera_code https://github.com/yabloco-codegen/yabloco-benchmark
```

This will download the data and evaluation code under the `workspace` directory in `MERA_CODE`.

### How to Evaluate

Run the following command to evaluate your model:

```bash
lm_eval \
  --model local-completions \
  --model_args model=Qwen2.5-32B-Instruct,base_url=http://localhost:6002/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=8192,max_gen_toks=2048,tokenizer=Qwen/Qwen2.5-32B-Instruct \
  --tasks yabloco_oracle \
  --batch_size 8 \
  --trust_remote_code \
  --gen_kwargs max_tokens=2048 \
  --log_samples \
  --output_path data/out \
  --include_path=./code_tasks
```
