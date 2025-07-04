# RealCode


## Task description

**RealCode** is a benchmark for evaluating the ability of language models to generate function bodies in real-world Python repositories. The benchmark focuses on realistic completions using project-level context and validates correctness through test execution.

Evaluated skills: Code completion, Context-aware generation

Contributors: Pavel Zadorozhny, Rodion Levichev, Pavel Adamenko, Aidar Valeev, Dmitrii Babaev, Denis Kokosinskiy


## Motivation

This dataset tests how well models can:
- Generate function bodies based on surrounding code context;
- Integrate into existing Python projects;
- Pass real unit tests after insertion.
The main evaluation metric is `pass@k`, computed via execution of repository-specific tests inside Docker containers.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — string containing the task formulation for function body generation;
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `left_context` [str] — code appearing before the target function;
- `outputs` [str] — one-dimensional array of strings of size n_samples, where n_samples is the number required to compute pass@k;
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — unique identifier of the example;
    - `repo` [str] — GitHub repository name the task is taken from;
    - `base_commit` [str] — commit hash fixing the repo state;
    - `gt` [str] — ground truth function body (no signature);
    - `right_context` [str] — code appearing after the target function;
    - `left_context` [str] — code appearing before the target function;
    - `image_name` [str] — Docker image for running the project;
    - `build_command` [str] — command to build the project before tests;
    - `test_command` [str] — command to run the tests;
    - `fn` [str] — path to the file containing the function;
    - `PASS_TO_PASS` [list] — tests that pass with the generated function;
    - `FAIL_TO_PASS` [list] — tests that used to fail and now pass;
    - `intent` [str] — function or method name;
    - `intent_type` [str] — element type (function, class, etc.)


### Data formatting example

```json
{
    "instruction": "Контекст:\n```python\n{left_context}\n```\nТребуется: только тело функции. Строго соблюдай отступы Python. Не добавляй лишнего текста.",
    "inputs": {
        "left_context": "from slack_sdk import WebClient\n\nclass SlackProgressBar:\n    def __init__(self, token: str, total: int):"
    },
    "outputs": "        self._client = WebClient(token=token)\n        self._total = total",
    "meta": {
        "id": 1,
        "repo": "mlizzi/slack-progress-bar",
        "base_commit": "d2d6d955fb8a0423ab89c1bac6c4f70101e6b8af",
        "gt": "        self._client = WebClient(token=token)\n        self._total = total",
        "right_context": "    def update(self, value: int) -> None:\n        pass",
        "left_context": "from slack_sdk import WebClient\n\nclass SlackProgressBar:\n    def __init__(self, token: str, total: int):",
        "image_name": "python:3.11.11-slim-bookworm",
        "build_command": "pip install .; pip install pytest; pip install pytest-json-report;",
        "test_command": "pytest tests --json-report --json-report-file=report_pytest.json",
        "fn": "slack_progress_bar/slack_progress_bar.py",
        "PASS_TO_PASS": [
            "tests/test_slack_progress_bar.py::test_slack_progress_bar"
        ],
        "FAIL_TO_PASS": [],
        "intent": "__init__[function]",
        "intent_type": "function"
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Ответ оформите так: ```python
<code>```Контекст:
{left_context}
Требуется: продолжить только тело одной функции. Строго соблюдайте отступы Python. Не добавляйте лишнего текста и не пишите другие функции. Ваша генерация будет вставлена сразу после контекста и запущена тестами.
```


### Dataset creation

The benchmark is built from 95 public Python GitHub repositories created in 2024. There are 802 tasks in total: for each sample, a function is extracted along with its surrounding code (`left_context`) and evaluated based on whether the generated body passes original unit tests. All examples come from real repositories and are reproducibly executable.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `pass@1`: fraction of tasks where at least one generation passes all tests
- `pass_oracle@1`: fraction of tasks where the ground truth solution passes all tests (oracle upper bound)
- `pass_stub_pass@1`: fraction of tasks where a `return pass` stub passed at least one test
- `pass_stub_empty_str@1`: fraction of tasks where a `return ""` stub passed at least one test
- `pass_dry_run@1`: fraction of tasks where at least one generation passes in dry-run mode (without using ground truth)
- `execution_success`: fraction of tasks where the project built and tests executed without failure
- `num_samples`: total number of tasks in the dataset
