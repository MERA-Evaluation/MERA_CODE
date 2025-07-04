# RealCodeJava


## Описание задачи

**RealCodeJava** — это бенчмарк для оценки способности моделей дописывать тело функции в реальных Java-проектах. Задачи построены на основе настоящих репозиториев и валидируются через выполнение юнит-тестов.

Тестируемые навыки моделей: Code completion, Context-aware generation

Авторы: Дмитрий Воробьев, Павел Задорожный, Родион Левичев, Павел Адаменко, Айдар Валеев, Дмитрий Салихов, Дмитрий Бабаев


## Мотивация

Датасет проверяет, насколько хорошо модели:
- Дополняют тело функции по контексту (`left_context`, `right_context`);
- Интегрируются в существующий проект без нарушения логики;
- Проходят реальные тесты после вставки тела.
Основная метрика — `pass@k`, оценивающая успешное выполнение тестов в Docker-среде.


## Описание датасета

### Поля данных

Каждый вопрос в датасете содержит следующие поля:

- `instruction` [str] — строка, содержащая формулировку задания по генерации тела функции;
- `inputs` — Вводные данные, формирующие задание для модели. Могут включать одну или несколько модальностей - видео, аудио, изображение, текст.
    - `left_context` [str] — код перед функцией, включая импорты и классы;
- `outputs` [str] — одномерный массив строк размера n_samples, где n_samples — количество требуемых сэмплов для подсчета pass@k;
- `meta` — Метаданные, относящиеся к тестовому примеру, но не используемые в вопросе (скрытые от тестируемой модели).
    - `id` [int] — уникальный идентификатор примера;
    - `repo` [str] — имя GitHub-репозитория, из которого извлечена задача;
    - `base_commit` [str] — хэш коммита, зафиксировавшего состояние репозитория;
    - `gt` [str] — тело функции-истины без сигнатуры;
    - `stub` [str] — тело функции-заглушки без сигнатуры;
    - `right_context` [str] — код после функции, включая другие функции и классы;
    - `left_context` [str] — код перед функцией, включая импорты и классы;
    - `image_name` [str] — Docker-образ, в котором выполняется проект;
    - `build_command` [str] — команда для сборки проекта перед тестами;
    - `test_command` [str] — команда запуска тестов;
    - `file_path` [str] — путь до файла, в котором находится функция;
    - `PASS_TO_PASS` [list] — список тестов, которые успешно проходят;
    - `FAIL_TO_PASS` [list] — список тестов, которые перестали падать;
    - `intent` [str] — название функции или метода;
    - `intent_type` [str] — тип элемента (function, class и т.д.)


### Пример данных

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


### Промпты

Для задачи были подготовлены 10 промптов, которые были равномерно распределены по вопросам по принципу "один вопрос – один промпт". Шаблоны в фигурных скобках в промпте заполняются из полей внутри поля `inputs` в каждом вопросе.


Пример промпта:

```
Есть контекст задачи:
{left_context}

Напишите содержимое последней функции после заголовка с аргументами. В ответе ожидается только тело одной функции. Не добавляйте в ответ новые функции и классы, старайтесь использовать те, что уже есть в контексте, или импортированы в самом начале. Соблюдайте отступы в коде и форматирование как в примере. Ответ оформите так: 
```java
поместите сюда содержимое вашего ответа
```

```


### Создание датасета

Бенчмарк построен на основе 27 GitHub-репозиториев, созданных в 2024-2025 гг. Для каждой задачи извлекается функция, ее контекст и проверяется прохождение изначальных тестов при генерации нового тела. Все примеры валидны и воспроизводимы.


## Оценка


### Метрики

Для агрегированной оценки ответов моделей используются следующие метрики:

- `pass@1`: доля задач, в которых хотя бы одна генерация прошла все тесты
- `pass_oracle@1`: доля задач, в которых ground truth решение проходит все тесты (верхняя граница)
- `pass_stub_pass@1`: доля задач, в которых заглушка (stub) прошла хотя бы один тест
- `pass_dry_run@1`: доля задач, где хотя бы одна генерация прошла тесты в режиме dry-run (без использования ground truth)
- `execution_success`: доля задач, в которых проект успешно собрался и тесты запустились без сбоев
- `num_samples`: общее количество задач в датасете
