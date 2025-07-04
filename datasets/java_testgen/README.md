# JavaTestGen


## Task description

**Java TestGen** is a benchmark designed to evaluate code generation models' ability to generate Java unit tests. Tasks involve generating unit tests based on provided Java source code and repository context. Dataset contains `227` tasks.

Evaluated skills: Instruction Following, Code Perception, Completion, Testing

Contributors: Dmitry Salikhov, Pavel Zadorozhny, Pavel Adamenko, Rodion Levichev, Aidar Valeev, Dmitrii Babaev


## Motivation

This dataset assesses models' ability to generate functionally valid tests for Java programs, emphasizing:
- Understanding real-world Java code;
- Generating executable test cases;
- Handling Maven project structures and dependencies.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — string containing the task formulation for test generation;
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `class_name` [str] — name of the Java class to generate a test for;
    - `test_class_name` [str] — name of the test class to be generated;
    - `code` [str] — string containing the Java class source code;
- `outputs` [list] — one-dimensional array of strings of size n_samples, where n_samples is the number required to compute pass@k;
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — unique identifier of the example;
    - `instance_id` [str] — unique identifier of the example;
    - `repo` [str] — string containing the repository from which the Java code was taken;
    - `base_commit` [str] — string with the commit hash fixing the version of the code;
    - `image_name` [str] — string with the name of the docker image used for testing;
    - `test_command` [str] — string containing the command to run tests inside the container;
    - `fn_test` [str] — string with the path to the test file inside the project;
    - `source_code` [str] — string containing the Java class source code


### Data formatting example

```json
{
    "instruction": "Вот Java-класс \"{class_name}\".\n```java\n{code}\n```\nНапишите JUnit5 тестовый класс \"{test_class_name}\". Включите позитивные сценарии, ошибки и граничные случаи.",
    "inputs": {
        "class_name": "ReverseCommand",
        "test_class_name": "ReverseCommandTest",
        "code": "package com.github.quiram.course..."
    },
    "outputs": [
        "..."
    ],
    "meta": {
        "id": 1,
        "instance_id": "java_testgetn_1",
        "repo": "quiram/course-stream-collector",
        "base_commit": "a8628593e8e96572a1c2a33",
        "image_name": "maven",
        "test_command": "mvn test",
        "fn_test": "src/test/java/com/github/exampleTest.java",
        "source_code": "package com.github.quiram; public class Example {}"
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Вам дана реализация класса {class_name}. А вот сам код:
{code}

Ответ должен быть оформлен так:```java
<code>```Ваша задача — написать тестовый класс {test_class_name} на JUnit5 для данного класса. Покройте все сценарии, даже если в коде нет соответствующих веток. Напишите тесты для обычных, пограничных и некорректных случаев. В каждом тесте только один assert. Имена методов должны быть осмысленными. Добавьте необходимые импорты и аннотации.
```


### Dataset creation

The dataset consists of 227 tasks collected from public GitHub Java repositories. Each task contains source code, testing command, Docker environment details, and a prompt guiding test generation. Testing is performed by executing the generated tests inside a Docker container with the project setup.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `pass@1`: Pass@1 measures the proportion of problems where the model's first generated solution passes all test cases.
- `compile@1`: compile@1 is the proportion of generated code that successfully compiles without errors.
