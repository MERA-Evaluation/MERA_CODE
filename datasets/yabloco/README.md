# YABLoCo


## Task description

Long context code generation on C/C++ at function level

Evaluated skills: C/C++, Long context, Code generation, Instruction following

Contributors: Aidar Valeev, Roman Garaev, Vadim Lomshakov, Irina Piontkovskaya, Vladimir Ivanov, Israel Adewuyi


## Motivation

YABLoCo is a long context code generation benchmark featuring a test set of 208 functions selected from four large repositories with
thousands of functions. The dataset contains metadata of functions, contexts of the functions with different levels of dependencies,
docstrings, functions bodies, and call graphs for each repository. The benchmark aims at function body generation in large repositories
from 200K to 2,000K LoC in C and C++, two languages not covered by previous benchmarks. While the benchmark generally allows custom
retrieval across repositories, the provided version proposes oracle context -- functions extracted from call graph that generated code
should depend on. Given oracle context, docstring and function signature, model generates correspondin function body, which then gets
evaluated on repository tests. Model should understand code from provided context and docstring summary and compose a function method
that implements the required functionality. Evaluation presents results in two metrics: pass@1, measuring functionality correctness,
and exact match, which indicates overfitting in case of high values.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `language` [str] — Programming language to write code in (C/C++).
    - `signature` [str] — Function signature.
    - `docstring` [str] — Function docstring comment.
    - `context` [str] — Oracle context -- functions extracted from call graph that the original code calls.
- `outputs` [str] — The correct answer to the question.
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.
    - `original_id` [str] — Function identifier in call-graph.
    - `repository` [str] — Repository.
    - `fname` [str] — Function name.
    - `file` [str] — Original file path.
    - `calls_num` [int] — Number of times target function is called.
    - `dep_num` [int] — Number of dependencies called in function body.
    - `same_file` [int] — Number of same-file dependencies called in function body.
    - `same_package` [int] — Number of same-package dependencies called in function body.
    - `project` [int] — Number of project-level dependencies called in function body.
    - `stdlib` [int] — Number of stdlib dependencies called in function body.
    - `external_binaries` [int] — Number of dependencies from external binaries called in function body.
    - `code_length` [int] — Ground truth code length.
    - `pos` [int] — Code position in the original file.
    - `last_commit` [str] — Date of last commit related to the function body.
    - `test_cov_hits` [int] — Number of test coverage hits.


### Data formatting example

```json
{
    "instruction": "Напиши функцию на языке {language} с сигнатурой {signature} и следующим описанием: {docstring}. Используй следующий контекст:\n\n{context}",
    "inputs": {
        "language": "C",
        "context": "// File name: openssl/crypto/ui/ui_lib.c\n// Comment: \nvoid *(*UI_method_get_data_duplicator(const UI_METHOD *method)) (UI *, void *)\n{\n    if (method != NULL)\n        return method->ui_duplicate_data;\n    return NULL;\n}",
        "signature": "void *UI_add_user_data(UI *ui, void *user_data)",
        "docstring": " The following function is used to store a pointer to user-specific data.\nAny previous such pointer will be returned and replaced.\nFor callback purposes, this function makes a lot more sense than using\nex_data, since the latter requires that different parts of OpenSSL or\napplications share the same ex_data index.\nNote that the UI_OpenSSL() method completely ignores the user data. Other\nmethods may not, however."
    },
    "outputs": "void *UI_add_user_data(UI *ui, void *user_data)\n{\n    void *old_data = ui->user_data;\n\n    if ((ui->flags & UI_FLAG_DUPL_DATA) != 0) {\n        ui->meth->ui_destroy_data(ui, old_data);\n        old_data = NULL;\n    }\n    ui->user_data = user_data;\n    ui->flags &= ~UI_FLAG_DUPL_DATA;\n    return old_data;\n}",
    "meta": {
        "id": 230,
        "original_id": "1AA5FDA0028F60DA",
        "repository": "openssl",
        "fname": "UI_add_user_data",
        "file": "openssl/crypto/ui/ui_lib.c",
        "calls_num": 5,
        "dep_num": 2,
        "same_file": 1,
        "same_package": 1,
        "project": 0,
        "stdlib": 0,
        "external_binaries": 0,
        "code_length": 11,
        "pos": 371,
        "last_commit": "31.05.2017",
        "test_cov_hits": 401
    }
}
```


### Prompts

For the task, 11 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Сгенерируй функцию на языке программирования {language}. Сигнатура функции: {signature}. Описание функции: {docstring}. Используй следующий контекст:

{context}
```


### Dataset creation

Largest most-starred selected GitHub repositories included llvm-project, bullet3, openssl and redis. The limited number of repositories is due
to high costs of including more repositories, specifically, building and compiling projects, implementing Dockerfiles, running tests and 
computing test coverage. From each of the selected repositories, we extracted all functions along with their function calls, last commit date,
docstring comment, code and comment length, and test hits. The function calls were then assigned to one of the following five categories: 'none',
'stdlib', 'file', 'package', 'project'. Specifically, 'stdlib' for system calls, 'file' and 'package' for calls inside the same file and package,
correspondingly, and 'project' for functions with project-level calls. If a function had no dependencies, it went into the 'none' category. We
filtered out the functions that had excessively short or long implementations, or no test hits or comments. Then, we detected and removed near
code duplicates. After that, we sorted the remaining set of functions in every context category according to the last commit date and test hits
preferring the latest and most covered. The repositories functions were sampled automatically disregarding the docstring quality. Therefore, we
manually evaluated the docstring quality. In addition to the data collection and cleaning, we generated a call graph for each repository. The
graph contained all functions with unique IDs, their callers, and callee functions as well as metadata such as length, path to file, position
in file, docstring, date of the last modification, number of test hits, and a category.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `Pass@1`: Pass@1 is the average success rate across all processed cases, where a given case is considered successful (score 1) if the first generated solution passes all unit tests, and unsuccessful (score 0) otherwise.
- `Exact match`: Exact match is the average of scores for all processed cases, where a given case score is 1 if the predicted string is the exact same as its reference string, and is 0 otherwise.
