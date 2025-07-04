# StRuCom


## Task description

The dataset contains structured Russian-language docstrings for functions in 5 programming languages (Python, Java, C#, Go, JavaScript). Dataset contains `500` tasks.

Key features:
- First specialized corpus for Russian-language documentation
- Combination of real GitHub data (for testing) and synthetic data from Qwen2.5-Coder-32B-Instruct (for training)
- Strict filtering for completeness and compliance with documentation standards
- All comments conform to specified formats (Python - GoogleDoc, JavaScript - JSDoc, Java - JavaDoc, C# - XML, Go - GoDoc)

Evaluated skills: Instruction Following, Code Perception, Simulation, Documentation

Contributors: Maria Dziuba, Valentin Malykh


## Motivation

### Target Models and Limitations
Designed for evaluating models supporting structured documentation generation (DeepSeek-Coder, Qwen2.5-Coder)

Not suitable for:
- Unstructured comment generation
- Code summarization
- Code explanation

### Users and Result Interpretation
Primary users:
- NLP developers and researchers working on automated documentation tools

Results allow to:
- Assess models' ability to generate technically accurate comments compliant with documentation standards

### Metrics:
- chrF evaluates similarity between generated and reference texts using character n-grams, considering morphology, spelling and grammatical endings - particularly crucial for Russian due to its morphological complexity


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `function` [str] — The function to generate a structured comment for.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `language` [str] — The programming language in which the function is written.


### Data formatting example

```json
{
    "instruction": "Напиши русскоязычную документацию к функции.\n\nФункция:\n{function}",
    "inputs": {
        "function": "private void button15_Click(object sender, EventArgs e)\n        {\n            label12.Text = \"\";\n\n            richTextBox1.Clear();\n            richTextBox2.Clear();\n            textBox1.Clear();\n            textBox2.Clear();\n            textBox4.Clear();\n        }"
    },
    "outputs": "/// <summary>\n/// Обработчик события нажатия на кнопку button15.\n/// При вызове этой функции происходит очистка текста в различных элементах управления формы:\n/// - Удаляется текст из метки label12.\n/// - Очищается содержимое многострочного текстового поля richTextBox1.\n/// - Очищается содержимое многострочного текстового поля richTextBox2.\n/// - Очищается текстовое поле textBox1.\n/// - Очищается текстовое поле textBox2.\n/// - Очищается текстовое поле textBox4.\n/// </summary>\n/// <param name=\"sender\">Объект, который вызвал событие (в данном случае, кнопка button15).</param>\n/// <param name=\"e\">Параметры события, содержащие дополнительную информацию о событии.</param>",
    "meta": {
        "id": 1,
        "language": "csharp"
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Напиши русскоязычную документацию к функции.

Функция:
{function}
```


### Dataset creation

### Stage 1: Data Collection
- Crawling Russian-language GitHub repositories with permissive/no licenses, language identification via Lingua
- Function extraction using function_parser and Code-Text

### Stage 2: Synthetic Data
- Qwen2.5-Coder-32B-Instruct model used for synthetic data generation

### Stage 3: Cleaning and Standardization
- Strict structural filtering (requiring complete coverage of all documented code elements)
- Style standardization of all comments
- Length filtering (250-1000 characters)


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `chrF`: Metric evaluating character n-gram matches with reference text, suitable for Russian morphology and spelling accuracy
