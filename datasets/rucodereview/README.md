# rucodereview


## Task description

The task is to automatically generate code review comments in Russian based on code changes.
The dataset includes 699 examples of code changes (in Java, Python, Scala, and Go) paired with corresponding comments. All comments have been verified for reproducibility (ability to reconstruct context from code diffs) and relevance to the changes.

Evaluated skills: Counterfactual robustness, Static counting

Contributors: Artem Zavgorodnev, Aleksandr Medvedev, Georgiy Mkrtchyan, Ivan Kharkevich, Ilseyar Alimova, Nikolay Bushkov, Stanislav Moiseev.


## Motivation

This benchmark addresses a critical gap in evaluating multilingual code-aware LLMs. Below is a detailed rationale:
Target Models:
Multilingual LLMs capable of processing the Russian language and analyzing code syntax/semantics.
Excludes models that: Lack Russian language support or cannot interpret code diffs.
Users: Developers and researchers focused on automating code review pipelines for Russian-speaking teams.
Evaluated Capabilities:
Understanding syntactic and semantic code changes.
Generating issue-specific comments (e.g., bugs, optimizations, style violations).
Multilingual code support (Java, Python, Scala, Go).
These capabilities are critical for integrating LLMs into real-world development pipelines, where precision and compliance with standards are non-negotiable.
Dataset Design
Comments are anchored to specific code changes to eliminate reliance on external context.
Two-stage filtering (LLM + dual human review) ensures comments are self-contained and reproducible.
Validity is enforced via strict criteria: Comments must be interpretable solely from the attached code changes.
Metrics:
BLEU/ChrF: Evaluate textual alignment with the reference.
pass@k:
Measures the percentage of cases where at least one of the first k generated comments is deemed correct via LLM-as-a-Judge evaluation.
The model generates up to 10 comment variants per code change.
Each variant is validated by an LLM judge for semantic consistency with the reference comment (reference-based).
A sample is considered successful if at least one of the first k variants passes validation.
Why These Metrics?
We do not require exact replication of the reviewer’s comment.
Instead, we assess the model’s ability to generate generally high-quality comments that align with human judgment.
Critical for code review tasks, where multiple valid approaches exist to highlight issues.



## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `diff_block` [str] — A code snippet in unified diff format displaying changes (added/removed lines marked with +/-) within a specific context (e.g., a function or class);
- `outputs` [str] — The reviewer's reference comment;
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `diff_block_with_arrow` [str] — diff_block with arrows indicating the lines of a multi-line comment;
    - `end_line` [int] — The line number where the comment ends;
    - `full_diff` [str] — diff of the entire file;
    - `language` [str] — Programming language;
    - `original_end_line` [int] — The line number in the original file where the comment ends;
    - `original_start_line` [int] — The line number in the original file where the comment begins (-1 for single-line comments);
    - `start_line` [int] — The line number where the comment begins (-1 for single-line comments)


### Data formatting example

```json
{
    "instruction": "Ты - проверяющий код (ревьювер). Твоя задача — анализировать изменения в коде и предлагать улучшения. Укажи на проблемные места и предложи способы их исправления или улучшения. \n\nИспользуй максимум 10 комментариев. Форматируй ответ следующим образом:\n\nКомментарий 1: <твой комментарий>\nКомментарий 2: <твой комментарий>\nКомментарий 3: <твой комментарий>\nКомментарий 4: <твой комментарий>\nКомментарий 5: <твой комментарий>\nКомментарий 6: <твой комментарий>\nКомментарий 7: <твой комментарий>\nКомментарий 8: <твой комментарий>\nКомментарий 9: <твой комментарий>\nКомментарий 10: <твой комментарий>\n\nInput data:\nCode changes: {diff_block}\nAnswer:",
    "inputs": {
        "diff_block": "def check_user_credentials(username: str, password: str) -> bool:    \n    conn = sqlite3.connect('users.db')\n    cursor = conn.cursor()\n\n-   query = \"SELECT * FROM users\"\n+   query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n    cursor.execute(query)\n+   result = cursor.fetchall()\n    result = cursor.fetchone()\n+   conn.commit()\n    conn.close()\n-   return False\n+   return result is not None\n"
    },
    "outputs": "Не надо так делать никогда. Это же классика. Подстановка username и password через ф-строку позволяет юзеру внедрить произвольный sql-код, и он удалит тебе всю бд.",
    "meta": {
        "id": 1,
        "diff_block_with_arrow": "def check_user_credentials(username: str, password: str) -> bool:    \n    conn = sqlite3.connect('users.db')\n    cursor = conn.cursor()\n\n-   query = \"SELECT * FROM users\"\n+   query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"        <----------\n    cursor.execute(query)\n+   result = cursor.fetchall()\n    result = cursor.fetchone()\n+   conn.commit()\n    conn.close()\n-   return False\n+   return result is not None\n",
        "end_line": 6,
        "full_diff": "@@ -1,12 +1,16 @@\nimport sqlite3\n\ndef check_user_credentials(username: str, password: str) -> bool:    \n    conn = sqlite3.connect('users.db')\n    cursor = conn.cursor()\n\n-   query = \"SELECT * FROM users\"\n+   query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n    cursor.execute(query)\n+   result = cursor.fetchall()\n    result = cursor.fetchone()\n+   conn.commit()\n    conn.close()\n-   return False\n+   return result is not None\n\n+print(check_user_credentials(\"petrof.a\", \"12345678\"))\n",
        "language": "Python",
        "original_end_line": 6,
        "original_start_line": -1,
        "start_line": -1
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Ты - проверяющий код (ревьювер). Твоя задача — анализировать изменения в коде и предлагать улучшения. Укажи на проблемные места и предложи способы их исправления или улучшения. 

Используй максимум 10 комментариев. Форматируй ответ следующим образом:

Комментарий 1: <твой комментарий>
Комментарий 2: <твой комментарий>
Комментарий 3: <твой комментарий>
Комментарий 4: <твой комментарий>
Комментарий 5: <твой комментарий>
Комментарий 6: <твой комментарий>
Комментарий 7: <твой комментарий>
Комментарий 8: <твой комментарий>
Комментарий 9: <твой комментарий>
Комментарий 10: <твой комментарий>

Input data:
Code changes: {diff_block}
Answer:
```


### Dataset creation

The research analyzed repositories created in the BackEnd Academy during 2024. Key stages included:
1. Data Collection: Pull request comments, commit messages, and code line annotations were extracted via the GitHub API.
2. Code Segmentation: Language-specific parsers (AST for Java/Scala, go/parser for Go, Python’s ast) identified logical code blocks (classes, functions).
3. Dataset Filtering:
   - Removed comments targeting non-relevant programming language files (50 samples excluded).
   - GPT-4o classification into reproducible/non-reproducible: Assessed whether a comment’s context could be inferred solely from code changes.
   - Human review of 1300 samples pre-labeled as "reproducible": 699 samples approved.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `bleu`: BLEU (Bilingual Evaluation Understudy) is a metric for automatically evaluating the quality of machine-translated text by comparing n-gram matches between the candidate translation and reference translations, incorporating precision and a brevity penalty.
- `chrf`: chrF (Character n-gram F-score) is a metric for evaluating machine translation quality, based on the F-score that measures character n-gram matches between the candidate and reference translations, combining precision and recall.
- `pass@1`: The proportion of examples where the first comment generated by the model was judged correct by the LLM-as-a-Judge.
- `pass@5`: The proportion of examples where at least one of the first 5 comments generated by the model was judged correct by the LLM-as-a-Judge.
- `pass@10`: The proportion of examples where at least one of the first 10 comments generated by the model was judged correct by the LLM-as-a-Judge.
