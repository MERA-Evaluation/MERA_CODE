# RealCode Eval Benchmark

## Description

**RealCode Eval** is a benchmark designed to evaluate the code generation capabilities of language models in real-world GitHub repositories. The evaluation process assesses the functional correctness of generated code by running repository-specific tests. RealCode Eval allows researchers and practitioners to gauge how well their models can complete code snippets based on real repository contexts, including function signatures, docstrings, and surrounding code.

### Key Features
- **Context-Aware Code Generation**: Tasks include generating function bodies or class methods using the function signature, docstring, and surrounding code context.
- **Execution-Based Evaluation**: Model-generated code is evaluated by running the corresponding repository tests to ensure correctness.
- **Real-World Datasets**: Built from 154 Python GitHub repositories created in 2024 to minimize data contamination for popular Code LLMs.
- **Ground Truth Accuracy**: Original repository code ensures a baseline accuracy of 1.0.

### Dataset Details
- **Tasks**: 1000 tasks involving code generation in Python repositories.
- **Input Context**:
  - `left_context`: Code preceding the target function or method.
  - `right_context`: Code following the target function or method.
- **Ground Truth (gt)**: The actual implementation of the function or method (not accessible to the model).
- **Evaluation Metric**: `pass@k` — Compares the number of passed tests between generated and ground-truth code.

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
- Install the RealCode Eval package:
  ```bash
  pip install 'RealCode_eval[build,test] @ git+https://github.com/NLP-Core-Team/RealCode_eval.git@v3_pip_package'
  ```
  or
  ```bash
  pip install 'RealCode_eval[build,test] @ git+ssh://git@gitlab.ai.cloud.ru:2222/rnd-core-team/plp/RealCode_eval.git@v3_pip_package'
  ```

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
cd MERA_CODE
```

```bash
realcode-download-data --workspace-path "workspace" && \
realcode-build-envs --workspace-path "workspace" --num-jobs 8  && \
realcode-run-tests --workspace-path "workspace"
```

This will install the dataset and set up environments under the `workspace` directory in `MERA_CODE`.

### Using an Existing Dataset

To use an existing dataset, update the `realcode_fg.yaml` and `realcode_sg.yaml` configuration files located in `code_tasks/realcode/`. Below are the parameters you need to modify.

#### Parameters to Update

1. **`dataset_kwargs`**: 
  
   Example:
   ```yaml
   dataset_kwargs:
     data_files: 
       test: /path/to/your/data/realcode_v3/realcode_v3_FG.json
   ```

2. **`filter_list`**: 
  
   Example:
   ```yaml
   filter_list:
     - name: "evaluation"
       filter:
         - function: extract_from_tag
         - function: scoring
           dataset_root: /path/to/your/data/realcode_v3/
   ```

### How to Evaluate

1. Evaluate in FG (Function Generation) Mode

Run the following command to evaluate your model in Function Generation mode:

```bash
lm_eval \
  --model local-completions \
  --model_args model=Qwen2.5-32B-Instruct,base_url=http://localhost:6002/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-32B-Instruct \
  --tasks realcode_fg \
  --batch_size 8 \
  --trust_remote_code \
  --gen_kwargs max_tokens=1024 \
  --log_samples \
  --output_path data/out -w \
  --include_path=./code_tasks
```

2. Evaluate in SG (Snippet Generation) Mode

For Snippet Generation mode, use the following:

```bash
lm_eval \
  --model local-completions \
  --model_args model=Qwen2.5-32B-Instruct,base_url=http://localhost:6002/v1/completions,num_concurrent=1,max_retries=3,tokenized_requests=True,max_length=2048,max_gen_toks=1024,tokenizer=Qwen/Qwen2.5-32B-Instruct \
  --tasks realcode_sg \
  --batch_size 8 \
  --trust_remote_code \
  --gen_kwargs max_tokens=1024 \
  --log_samples \
  --output_path data/out -w \
  --include_path=./code_tasks
```

#### Example Results

Example configuration:
- length=2048
- max_gen_toks=1024
- model=Qwen2.5-32B-Instruct
                                                                                                                                              
| Tasks | Version |   Filter   | n-shot |         Metric         |   | Value | ± | Stderr |
|-------|--------:|------------|-------:|------------------------|---|-------|---|-------:|
| FG    |       1 | evaluation |      0 | compilation_error_rate | ↓ | 0.046 | ± | 0.0066 |
|       |         | evaluation |      0 | exact_match            | ↑ | 0.116 | ± | 0.0101 |
|       |         | evaluation |      0 | pass@1                 | ↑ | 0.389 | ± | 0.0154 |

| Tasks | Version |   Filter   | n-shot |         Metric         |   | Value | ± | Stderr |
|-------|--------:|------------|-------:|------------------------|---|-------|---|-------:|
| SG    |       1 | evaluation |      0 | compilation_error_rate | ↓ | 0.408 | ± | 0.0155 |
|       |         | evaluation |      0 | exact_match            | ↑ | 0.059 | ± | 0.0075 |
|       |         | evaluation |      0 | pass@1                 | ↑ | 0.232 | ± | 0.0134 |

