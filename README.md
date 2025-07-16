# MERA Code

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/mera-code-logo-white.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/mera-code-logo-black.svg">
    <img alt="MERA Code" src="docs/mera-code-logo-white.png" style="max-width: 100%;">
  </picture>
</p>

<p align="center">
    <a href="https://opensource.org/licenses/MIT">
    <img alt="License" src="https://img.shields.io/badge/License-MIT-yellow.svg">
    </a>
    <a href="https://github.com/MERA-Evaluation/MERA_CODE/tree/main">
    <img alt="Release" src="https://img.shields.io/badge/release-v1.0.0-blue">
    </a>

</p>

<h2 align="center">
    <p> MERA Code: A Unified Framework for Evaluating Code Generation Across Tasks.
</p>
</h2>

## 🚀 About

**MERA Code** brings together a rich collection of code-focused evaluation tasks—both private and public—under one roof. Built on top of the [Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) (v0.4.9), it enables researchers and practitioners to:

- **Compare models** on identical tasks and metrics
- **Reproduce results** with fixed prompts and few-shot settings
- **Submit** standardized ZIP archives for leaderboard integration


## 🔍 Datasets Overview

| Set         | Task Name          | Language                         | Metrics                        | Size | Prompts | Skills                                                        |
| ----------- | ------------------ | -------------------------------- | ------------------------------ | ---- | ------- | ------------------------------------------------------------- |
| **Private** | **ruCodeEval**     | Python                           | pass@k                         | 164  | 10      | Instruction Following, Code Perception, Completion, Algorithms & Data Structures |
|             | **RuCodeReviewer** | Java, Scala, Go, Python          | Judge@k, BLEU, chrF            | 689  | 10      | Instruction Following, Code Perception, Review, Simulation, Explanation, Design Patterns, Style Guides |
|             | **CodeLinterEval** | Python                           | pass@k                         | 110  | 10      | Instruction Following, Code Perception, Style Guides, Review, Editing |
| **Public**  | **ruHumanEval**    | Python                           | pass@k                         | 164  | 10      | Instruction Following, Code Perception, Completion            |
|             | **StRuCom**        | Python, Java, Go, C#, JavaScript | chrF                           | 500  | 10      | Instruction Following, Code Perception, Simulation, Documentation |
|             | **UnitTests**      | Python, Java, Go, C#, JavaScript | CodeBLEU                       | 2500 | 20      | Instruction Following, Code Perception, Synthesis, Testing, Long Context Comprehension |
|             | **CodeCorrectness**| Python, Java, Go                 | EM                             | 1361 | 11      | Instruction Following, Code Perception, Simulation, Error Classification |
|             | **RealCode**       | Python                           | pass@k                         | 802  | 10      | Instruction Following, Code Perception, Completion            |
|             | **RealCodeJava**   | Java                             | pass@k                         | 298  | 10      | Instruction Following, Code Perception, Completion            |
|             | **JavaTestGen**    | Java                             | pass@k, compile@k              | 227  | 10      | Instruction Following, Code Perception, Completion, Testing   |
|             | **YABLoCo**        | C, C++                           | pass@k, EM                     | 208  | 11      | Instruction Following, Code Perception, Completion,  Long Context Comprehension    |


## 🛠 Getting Started <a name="evaluation"></a>

First, you need to clone the MERA_CODE repository and load the submodule:

```bash
### Go to the folder where the repository will be cloned ###
mkdir mera_code
cd mera_code

### Clone & install core libs ###
git clone --recurse-submodules https://github.com/MERA-Evaluation/MERA_CODE.git
cd MERA_CODE
```

Now you choose one of two evaluation regimes depending on whether you want to get the metrics for public tasks locally or intend to use our remote scoring via website.

### Remote Scoring

**Remote Scoring** (default): quick setup for cloud-based scoring — install only core dependencies, run the evaluation, and submit resulting ZIP-archive to our website to get the score. 

> You will not get the metrics even for public datasets (for each dataset you will see "bypass" placeholder instead of actual metrics) in terminal.

<details>
<summary>
Details on Remote Scoring
</summary>

<p>> Just install only those libraries that are required to get the model's generations (answers for the queries of each task).</p>

</details>



```bash
bash scripts/install_dependencies.sh
```

<details>
<summary>
How it works inside...
</summary>

```bash
### Install lm-eval ###
cd lm-evaluation-harness
pip install -e .

### Go to MERA_CODE folder ###
cd ../
```

</details>

You may also need additional libraries for models inference or evaluation. Use lm-eval compatible libraries and their versions:

```bash
### Install additional libs for models evaluation [Optional] ###
# vLLM engine
pip install -e ".[vllm]"
# API scoring
pip install -e ".[api]"

### Run evaluation and pack logs ###
bash scripts/run_evaluation.sh \
    --model vllm \
    --model_args "pretrained=Qwen/Qwen2.5-0.5B-Instruct,tensor_parallel_size=1" \
    --output_path "./results/Qwen2.5-0.5B-Instruct"
```

### Local Scoring

**Local Scoring** (optional): full setup for on-premise evaluation — install extra dependencies with metrics and runing Docker containers. Available only for Public sets. 

> Make sure you have a stable internet connection, enough disk space, and CPU resources.

<details>
<summary>
Details on Local Scoring
</summary>

<p>> Evaluation of RealCode, RealCodeJava, JavaTestGen assumes running hundreds of docker containers. Each one assumes to get one CPU to function correctly. YABLoCo also requires lots of resources and time. </p>

<p>> If you are running the evaluation from inside the Docker container the integrity of the local scoring is not guaranteed (and [this is also not recommended at all](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/)). </p>

<p>> Even without Docker-in-Docker issue, being short in resources means that although you would get the metrics, they would definitely be lower than those computed in the environment that fits the scoring in terms of resources.</p>

</details>



```bash
bash scripts/install_dependencies.sh --local_scoring
```

<details>
<summary>
How it works inside...
</summary>

```bash
# Install code_bleu metric for UnitTests
git clone https://github.com/Pstva/code_bleu.git
cd code_bleu
pip install -e .

# Install metrics for YABLoCo
cd ..
mkdir workspace
cd workspace
git clone -b mera_code https://github.com/yabloco-codegen/yabloco-benchmark
```

</details>

Now get to the evaluations but with flag `--compute_metrics` that enables local metrics computation. 

```bash
### Run evaluation and pack logs ###
bash scripts/run_evaluation.sh \
    --model hf \
    --model_args "pretrained=Qwen/Qwen2.5-0.5B-Instruct,dtype=bfloat16" \
    --compute_metrics \
    --output_path "./results/Qwen2.5-0.5B-Instruct"
```

More details on `run_evaluation.sh` usage may be obtained by:
```bash
bash scripts/run_evaluation.sh --help
```

## 📁 Repository Structure

```text
MERA_CODE/
├── code_tasks/                     # Code for each task
├── datasets/                       # Task descriptions, metadata, readme
├── docs/                           # Additional documentation and design notes
    ├── templates                   # Templates of tasks readme
    ├── dataset_contribution.md     # How to add a new dataset into MERA Code
    ├── dataset_criteria.md         # Creteria to add new dataset into MERA Code
    ├── dataset_formatting.md       # Dataset formatting requirements
    ├── dataset_hf.md               # How to add new datasets on MERA HuggingFace page
    ├── dataset_review.md           # General dataset requirements
    ├── model_scoring.md            # How to use lm-eval to evaluate the LMs
    ├── task_codebase.md            # How to add a new task into codebase
    ├── MERA_code_tax.png           # Taxonomy of coding skills
├── lm-evaluation-harness/          # Submodule (codebase)
└── scripts/                        # Helpers: add tasks, run evaluations, scoring
```


## 💪 How to Join the Leaderboard

Follow these steps to see your model on the leaderboard:

1. **Run Remote Scoring**  
   Evaluate the benchmark in **Remote Scoring** regime (see [“🛠 Getting Started”](#evaluation) above). You may run **Local Scoring** but will have to wait twice for submission scoring.
   > You’ll end up with a logs folder **and** a ready-to-submit zip archive like `Qwen2.5-0.5B-Instruct_submission.zip`.

2. **Submit on the website**  
   Head over to [Create Submission](https://dev.score.mlrnd.ru/en/code/submits/create), upload the archive, and move on to the form.

3. **Fill in Model Details**  
   Provide accurate info about the model and evaluation. These details are crucial for reproducibility—if something’s missing, admins may ping you (or your submission might be rejected).

4. **Wait for Scoring** ⏳  
   Scoring usually wraps up in **~2 hours**. There is a progress bar to track the scoring process. 
   > Keep in mind that if you submit more than one archive, they are scored sequentially one after another (not in parallel).

5. **Publish your result**  
   Once scoring finishes, click **“Submit for moderation”**. After approval, your model goes **Public** and appears on the [Leaderboard](https://dev.score.mlrnd.ru/en/code/leaderboard).  

Good luck, and happy benchmarking! 🎉


## 🤝 Contributing

We are interested in improvement of MERA Code and inviting the community to contribute to the development of new complex tasks and the project’s codebase. 

### Steps to Add a New Task:  
0) Develop a dataset (on the contributor’s side; see [task requirements](docs/dataset_review.md))  
1) Convert the dataset to MERA format ([guide](docs/dataset_formatting.md))  
2) Upload the dataset to 🤗HF Hub ([guide](docs/dataset_hf.md))  
3) Submit the dataset for MERA organizer review ([guide](docs/dataset_hf.md))  
4) Write evaluation code using lm-harness ([guide](docs/task_codebase.md))  
5) Benchmark state-of-the-art baseline models on the dataset 
6) Final moderation and your dataset is officially added!
   
## 📝 License

Distributed under the MIT License. See LICENSE for details.

