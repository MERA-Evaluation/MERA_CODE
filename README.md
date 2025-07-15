# MERA_CODE

<p align="center">
  <picture>
    <img alt="MERA" src="docs/mera-code-logo.svg" style="max-width: 100%;">
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

**Code-Tasks Benchmark** brings together a rich collection of code-focused evaluation tasks—both private and public—under one roof. Built on top of the [Language Model Evaluation Harness](https://github.com/EleutherAI/lm-evaluation-harness) (v0.4.8), it enables researchers and practitioners to:

- **Compare models** on identical tasks and metrics
- **Reproduce results** with fixed prompts and few-shot settings
- **Submit** standardized ZIP archives for leaderboard integration


## 🔍 Dataset Overview

| Set         | Task Name          | Language                         | Metrics                        | Size | Prompts | Skills                                                        |
| ----------- | ------------------ | -------------------------------- | ------------------------------ | ---- | ------- | ------------------------------------------------------------- |
| **Private** | **rucodeeval**     | Python                           | pass@k                         | 164  | 10      | Instruction Following, Code Perception, Completion, Algorithms & Data Structures |
|             | **rucodereviewer** | Java, Scala, Go, Python          | Judge@k, BLEU, chrF            | 689  | 10      | Instruction Following, Code Perception, Review, Simulation, Explanation, Design Patterns, Style Guides |
|             | **codelintereval** | Python                           | pass@k                         | 110  | 10      | Instruction Following, Code Perception, Style Guides, Review, Editing |
| **Public**  | **ruhumaneval**    | Python                           | pass@k                         | 164  | 10      | Instruction Following, Code Perception, Completion            |
|             | **strucom**        | Python, Java, Go, C#, JavaScript | chrF                           | 500  | 10      | Instruction Following, Code Perception, Simulation, Documentation |
|             | **unittests**      | Python, Java, Go, C#, JavaScript | CodeBLEU                       | 2500 | 20      | Instruction Following, Code Perception, Synthesis, Testing, Long Context Comprehension |
|             | **codecorrectness**| Python, Java, Go                 | EM                             | 1361 | 11      | Instruction Following, Code Perception, Simulation, Error Classification |
|             | **realcode**       | Python                           | pass@k                         | 802  | 10      | Instruction Following, Code Perception, Completion            |
|             | **realcodejava**   | Java                             | pass@k                         | 298  | 10      | Instruction Following, Code Perception, Completion            |
|             | **javatestgen**    | Java                             | pass@k, compile@k              | 227  | 10      | Instruction Following, Code Perception, Completion, Testing   |
|             | **yabloco**        | C, C++                           | pass@k, EM                     | 208  | 11      | Instruction Following, Code Perception, Completion,  Long Context Comprehension    |


## 🛠 Getting Started

 
There are two evaluation regimes:
1. **Remote Scoring**(default): quick setup for cloud-based scoring — install only core dependencies, run the evaluation, and submit resulting ZIP-archive to our website to get the score. 
2. **Local Scoring**(optional): full setup for on-premise evaluation — install extra dependencies with metrics and runing Docker containers. Available only for Public sets. Make sure you have a stable internet connection, enough disk space, and CPU resources.


```bash
### Go to the folder where the repository will be cloned ###
mkdir mera_code
cd mera_code

### Clone & install core libs ###
git clone --recurse-submodules https://github.com/MERA-Evaluation/MERA_CODE.git
cd MERA_CODE/lm-evaluation-harness
pip install -e .

### Install additional libs for models evaluation [Optional] ###
# vLLM engine
pip install -e ".[vllm]"
# API scoring
pip install -e ".[api]"

### Go to MERA_CODE folder ###
cd ../

### Install libs for Local Scoring only usage [Optional] ###
# Install code_bleu metric for UnitTests
git clone https://github.com/Pstva/code_bleu.git
cd code_bleu
pip install -e .
# Install metrics for YABLoCo
cd ..
mkdir workspace
cd workspace
git clone -b mera_code https://github.com/yabloco-codegen/yabloco-benchmark
# Install metrics for RealCode, RealCodeJava, JavaTestGen
cd ..
<code to install repotest>

### Run evaluation and pack logs ###
bash scripts/run_evaluation.py
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
├── lm-evaluation-harness/          # Submodule (codebase)
└── scripts/                        # Helpers: add tasks, run evaluations, scoring
```


## 🤝 Contributing

We welcome issues, feature requests, and pull requests! Please read [the documentation](docs/) for our guidelines.



## 📝 License

Distributed under the MIT License. See LICENSE for details.

