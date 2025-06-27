# CodeLinterEval


## Task description

The aim of benchmark is identifying the capabilities of models for generating and correcting code based on linter errors.

Tested skills: Instruction following, Perception(Python), Code changing

Authors: Vikulov Vladimir, Bykov Anton, Piktovnikov Kirill


## Мотивация

The aim of benchmark is identifying the capabilities of models for generating and correcting code based on linter errors.
The dataset is focused on:
- Code-generating models (e.g. Codex, CodeLlama, StarCoder, GPT-4) that can correct code based on linter errors.
- Models that specialize in refactoring and code correction (e.g. DeepSeek-R1, CodeT5).
- Multimodal models, if they can work with code and text instructions.
Not suitable for:
- Models without code understanding (e.g. purely text LLMs without additional training on code).
- Models that do not support Python.
- Models fine-tuned to solve the FIM (Fill-in-the-middle) problem.

The evaluation results may be useful for:
- Developers of tools for automatic code refactoring (e.g. IDE plugins);
- Researchers in the field of code generation and correction;
- Engineers evaluating the quality of code generation models.

The benchmark results will show how well the model copes with fixing code based on linter errors, which means that the model
can be useful for:
- automatic code fixing,
- improving code quality in IDEs,
- teaching beginners to write "clean" code.
If the model does not cope well, it means that it either does not understand linter errors, or does not know how to apply fixes correctly.

The benchmark evaluates:
1. Understanding linter errors - the ability to correctly interpret messages like E111, E231, etc.
2. Correct code refactoring - the ability to make corrections while preserving the logic of the program.
3. Following the code style (PEP 8) - correct indents, spaces, formatting.
4. Contextual understanding of the code - the model should not break the logic when fixing the style. Linter errors are a common occurrence in development, and automatic correction saves time.
If the model cannot correct simple style errors, it is unlikely to cope with more complex refactoring tasks.

The dataset contains:
code – source code with errors;
feedback – list of errors with description from the linter;
instruction – explicit instruction to correct the code based on feedback;
canonical_code – reference code
Explicit indication of errors allows us to evaluate the model's ability to correct code according to the linter, rather than "guess" errors.
The canonical solution (canonical_code) provides a clear ground truth for evaluation.
The instruction explicitly specifies the task so that the model does not deviate from the goal.

If the model corrects the code according to the feedback and the linter does not detect errors after checking the generation results, then the result is correct.
If errors persist or new ones appear, the model does not solve the problem.

The metric is pass@k, determined based on the success of the linter check relative to the total size of the dataset.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `code` [str] — source code with errors
    - `feedback` [str] — list of errors with description from the linter.
- `outputs` [int] — one-dimensional array of strings of size n_samples, where n_samples is the number of samples required to calculate the pass@k metric.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model)
    - `id` [int] — Identification number of the question in the dataset.
    - `canonical_code` — canonical solution to the task (code without linter errors/warnings)

### Data formatting example

```json
{
	"inputs": {
		"code": "import re\n\ndef find_literals(text, pattern):\n  match = re.search(pattern, text)\n  s = match.start()\n  e = match.end()\n  return (match.re.pattern, s, e)",
		"feedback": "E302: expected 2 blank lines, found 1 in 3 line\nE111: indentation is not a multiple of 4 in 4 line\nE111: indentation is not a multiple of 4 in 5 line\nE111: indentation is not a multiple of 4 in 6 line\nE111: indentation is not a multiple of 4 in 7 line\nW292: no newline at end of file in 7 line\n"
	},
	"instruction":  "Перепиши код с учетом ошибок полученных от линтера. Ошибки указывают на критические слабые места: потенциальные баги, уязвимости безопасности и нарушения принципов чистого кода. Исправь ВСЕ указанные ошибки без исключений, сохрани исходную логику программы, строго соблюдай PEP-8 для Python, не добавляй комментарии и объяснения. \nЗамечания линтера:\n{feedback}\n\nКод:\n{code}\nПриведите ответ в формате, соответствующем шаблону для ответа:\n```python\n<code> ```",
	"meta": {
		"canonical_code": "\nimport re\n\n\ndef search_regex(pattern, string):\n    match = re.search(pattern, string)\n    if match:\n        return match.group(), match.start(), match.end()\n    else:\n        return None\n",
		"id": 5
	},
	"outputs": [
		1,
		1,
		1,
		1,
		1,
		1,
		1,
		1,
		1,
		1
	]
},
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the inputs field in each question.


Prompt example:

```
Перепиши код с учетом ошибок полученных от линтера. Ошибки указывают на критические слабые места: потенциальные баги, уязвимости безопасности и нарушения принципов чистого кода. Исправь ВСЕ указанные ошибки без исключений, сохрани исходную логику программы, строго соблюдай PEP-8 для Python, не добавляй комментарии и объяснения. \nЗамечания линтера:\n{feedback}\n\nКод:\n{code}\nПриведите ответ в формате, соответствующем шаблону для ответа:\n```python\n<code> ```
```


### Dataset creation

To create a high-quality dataset, where the model should correct the code based on linter errors, it is necessary: ​​
1. A subset of the mbpp dataset was selected as the initial dataset.
2. For each code example, the flake8 linter was run to detect errors.
3. Only those examples that had at least 1 error were included in the final dataset.
4. To obtain canonical solutions, the code was manually corrected by experts and re-checked by the linter.
5. The results of the linter check are saved as lines with the error code and its description from the linter and saved in the feedback field
(i.e., "E111 indentation is not a multiple of four, E231 missing whitespace after ','")


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `pass@k`: The pass@k metric measures the proportion of test cases that a program passes out of the total number of test cases.


