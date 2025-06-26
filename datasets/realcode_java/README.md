# RealCodeJava


## Task description

**RealCodeJava** is a benchmark for evaluating the ability of language models to generate function bodies in real-world Java repositories. The benchmark focuses on realistic completions using project-level context and validates correctness through test execution.

Evaluated skills: Code completion, Context-aware generation

Contributors: Dmitry Vorobiev, Pavel Zadorozhny, Rodion Levichev, Pavel Adamenko, Aidar Valeev, Dmitry Salikhov, Dmitrii Babaev


## Motivation

This dataset tests how well models can:
- Generate function bodies based on surrounding code context;
- Integrate into existing Java projects;
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
    - `stub` [str] — stub function body (no signature);
    - `right_context` [str] — code appearing after the target function;
    - `left_context` [str] — code appearing before the target function;
    - `image_name` [str] — Docker image for running the project;
    - `build_command` [str] — command to build the project before tests;
    - `test_command` [str] — command to run the tests;
    - `file_path` [str] — path to the file containing the function;
    - `PASS_TO_PASS` [list] — tests that pass with the generated function;
    - `FAIL_TO_PASS` [list] — tests that used to fail and now pass;
    - `intent` [str] — function or method name;
    - `intent_type` [str] — element type (function, class, etc.)


### Data formatting example

```json
{
    "instruction": "Контекст:\n```java\n{left_context}\n```\nТребуется: только тело функции. Строго соблюдай отступы. Не добавляй лишнего текста.",
    "inputs": {
        "left_context": "package org.algorithmtools.ca4j.utils;\n\nimport com.alibaba.fastjson.JSONArray;\nimport com.alibaba.fastjson.JSONObject;\nimport org.algorithmtools.ca4j.enumtype.IndicatorStatType;\nimport org.algorithmtools.ca4j.pojo.IndicatorDivisionSeries;\nimport org.algorithmtools.ca4j.pojo.IndicatorSeries;\n\nimport java.util.ArrayList;\nimport java.util.List;\nimport java.util.stream.Collectors;\n\npublic class IndicatorSeriesUtil {\n\n    public static List<IndicatorSeries> transferFromArray(double[] array){\n"
    },
    "outputs": "        List<IndicatorSeries> list = new ArrayList<IndicatorSeries>();\n        for (int i = 0; i < array.length; i++) {\n            list.add(i, new IndicatorSeries(i, array[i], String.valueOf(i)));\n        }\n        return list;\n    }",
    "meta": {
        "id": 26,
        "repo": "algorithm-tools/CausalAnalysis",
        "base_commit": "1b714e0f22ac2259154be581065a2d4ccdfdd4ba",
        "gt": "        List<IndicatorSeries> list = new ArrayList<IndicatorSeries>();\n        for (int i = 0; i < array.length; i++) {\n            list.add(i, new IndicatorSeries(i, array[i], String.valueOf(i)));\n        }\n        return list;\n    }",
        "stub": "        return List.of();\n    }",
        "right_context": "\n\n    public static double[] transferToArray(List<IndicatorSeries> series){\n        double[] resultArray = new double[series.size()];\n        for (int i = 0; i < series.size(); i++) {\n            resultArray[i] = series.get(i).getValue();\n        }\n        return resultArray;\n    }\n\n    public static IndicatorDivisionSeries transferFromJson(String jsonString){\n        JSONObject jsonData = JSONObject.parseObject(jsonString);\n        JSONArray currentDenominatorList = jsonData.getJSONArray(\"currentDenominatorList\");\n        JSONArray currentNumeratorList = jsonData.getJSONArray(\"currentNumeratorList\");\n        JSONArray comparisonNumeratorList = jsonData.getJSONArray(\"comparisonNumeratorList\");\n        JSONArray comparisonDenominatorList = jsonData.getJSONArray(\"comparisonDenominatorList\");\n        String indicator = jsonData.getString(\"indicator\");\n        String indicatorName = jsonData.getString(\"indicatorName\");\n        String statType = jsonData.getString(\"statType\");\n\n        IndicatorDivisionSeries series = new IndicatorDivisionSeries(indicator, indicatorName, IndicatorStatType.valueOf(statType));\n        series.setCurrentNumeratorList(transferFromJsonArray(currentNumeratorList));\n        series.setCurrentDenominatorList(transferFromJsonArray(currentDenominatorList));\n        series.setComparisonNumeratorList(transferFromJsonArray(comparisonNumeratorList));\n        series.setComparisonDenominatorList(transferFromJsonArray(comparisonDenominatorList));\n\n        return series;\n    }\n\n    public static List<IndicatorSeries> transferFromJsonArray(JSONArray jsonArray){\n        return jsonArray.stream().map(v -> {\n            JSONObject data = (JSONObject) v;\n            return new IndicatorSeries(data.getLong(\"time\"), data.getDoubleValue(\"value\"), data.getString(\"logicalIndex\"));\n        }).collect(Collectors.toList());\n    }\n\n}",
        "left_context": "package org.algorithmtools.ca4j.utils;\n\nimport com.alibaba.fastjson.JSONArray;\nimport com.alibaba.fastjson.JSONObject;\nimport org.algorithmtools.ca4j.enumtype.IndicatorStatType;\nimport org.algorithmtools.ca4j.pojo.IndicatorDivisionSeries;\nimport org.algorithmtools.ca4j.pojo.IndicatorSeries;\n\nimport java.util.ArrayList;\nimport java.util.List;\nimport java.util.stream.Collectors;\n\npublic class IndicatorSeriesUtil {\n\n    public static List<IndicatorSeries> transferFromArray(double[] array){\n",
        "image_name": "maven:3.9.9-eclipse-temurin-23-alpine",
        "build_command": "",
        "test_command": "mvn test",
        "file_path": "src/main/java/org/algorithmtools/ca4j/utils/IndicatorSeriesUtil.java",
        "PASS_TO_PASS": [
            "org.algorithmtools.ca4j.calculator.TestCalculator::testContributionMultiplyCalculator",
            "org.algorithmtools.ca4j.calculator.TestCalculator::testContributionDivisionCalculator",
            "org.algorithmtools.ca4j.calculator.TestCalculator::testContributionPlusCalculator",
            "org.algorithmtools.ca4j.calculator.TestCalculator::testContributionDivisionCalculator_forZero",
            "org.algorithmtools.ca4j.calculator.TestCalculator::testJSDivergence",
            "org.algorithmtools.ca4j.calculator.TestCalculator::test"
        ],
        "FAIL_TO_PASS": [],
        "intent": "transferFromArray[function]",
        "intent_type": "function"
    }
}
```


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Есть контекст задачи:
{left_context}

Последняя функция в контексте имеет только сигнатуру и открытую скобку {. Требуется написать содержимое этой функции, завершив его закрывающей скобкой }. Не добавляйте в ответ другие функции и классы. Придерживайтесь отступов и форматирования, как в контексте. Ответ оформите так: 
```java
<code>
```
Ваш ответ будет добавлен к контексту. Получившийся Java код должен успешно пройти компиляцию и unit тесты.
```


### Dataset creation

The benchmark is built from 27 public Java GitHub repositories created in 2024-2025. For each sample, a function is extracted along with its surrounding code (`left_context`, `right_context`) and evaluated based on whether the generated body passes original unit tests. All examples come from real repositories and are reproducibly executable.


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `pass@1`: fraction of tasks where at least one generation passes all tests
- `pass_oracle@1`: fraction of tasks where the ground truth solution passes all tests (oracle upper bound)
- `pass_stub_pass@1`: fraction of tasks where stub function body passed at least one test
- `pass_dry_run@1`: fraction of tasks where at least one generation passes in dry-run mode (without using ground truth)
- `execution_success`: fraction of tasks where the project built and tests executed without failure
- `num_samples`: total number of tasks in the dataset
