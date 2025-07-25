# JavaTestGen


## Описание задачи

**Java TestGen** — это бенчмарк для оценки способности моделей генерировать тесты для Java-кода. Задачи заключаются в генерации unit-тестов на основе исходного Java-кода и контекста проекта. Датасет содержит `227` задач.

Тестируемые навыки моделей: Instruction Following, Code Perception, Completion, Testing

Авторы: Дмитрий Салихов, Павел Задорожный, Павел Адаменко, Родион Левичев, Айдар Валеев, Дмитрий Бабаев


## Мотивация

Датасет оценивает способность моделей:
- Понимать реальный код на Java;
- Генерировать исполняемые тесты;
- Работать с Maven-проектами и зависимостями.


## Описание датасета

### Поля данных

Каждый вопрос в датасете содержит следующие поля:

- `instruction` [str] — строка, содержащая формулировку задания по генерации теста;
- `inputs` — Вводные данные, формирующие задание для модели. Могут включать одну или несколько модальностей - видео, аудио, изображение, текст.
    - `class_name` [str] — название Java-класса, для которого требуется сгенерировать тест;
    - `test_class_name` [str] — название тестового класса, который необходимо сгенерировать;
    - `code` [str] — строка с исходным кодом Java-класса;
- `outputs` [list] — одномерный массив строк размера n_samples, где n_samples — количество требуемых сэмплов для подсчета pass@k;
- `meta` — Метаданные, относящиеся к тестовому примеру, но не используемые в вопросе (скрытые от тестируемой модели).
    - `id` [int] — уникальный идентификатор примера;
    - `instance_id` [str] — уникальный идентификатор примера;
    - `repo` [str] — строка, содержащая ссылку на репозиторий, из которого взят код;
    - `base_commit` [str] — строка с хэшем коммита, фиксирующего версию кода;
    - `image_name` [str] — строка с именем docker-образа, используемого для тестирования;
    - `test_command` [str] — строка с командой для запуска тестов внутри контейнера;
    - `fn_test` [str] — строка с путем к тестовому файлу в проекте;
    - `source_code` [str] — строка с исходным кодом Java-класса


### Пример данных

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


### Промпты

Для задачи были подготовлены 10 промптов, которые были равномерно распределены по вопросам по принципу "один вопрос – один промпт". Шаблоны в фигурных скобках в промпте заполняются из полей внутри поля `inputs` в каждом вопросе.


Пример промпта:

```
Вам дана реализация класса {class_name}. А вот сам код:
{code}

Ответ должен быть оформлен так:```java
<code>```Ваша задача — написать тестовый класс {test_class_name} на JUnit5 для данного класса. Покройте все сценарии, даже если в коде нет соответствующих веток. Напишите тесты для обычных, пограничных и некорректных случаев. В каждом тесте только один assert. Имена методов должны быть осмысленными. Добавьте необходимые импорты и аннотации.
```


### Создание датасета

Датасет состоит из 227 задач, собранных из публичных Java-репозиториев на GitHub. Для каждой задачи предоставлены исходный код, команда тестирования, параметры окружения и промпт. Оценка проводится через выполнение сгенерированных тестов в Docker-контейнере с установленным проектом.


## Оценка


### Метрики

Для агрегированной оценки ответов моделей используются следующие метрики:

- `pass@1`: Метрика pass@1 измеряет долю задач, для которых первое сгенерированное моделью решение проходит все тесты.
- `compile@1`: Метрика compile@1 показывает долю сгенерированного кода, который успешно компилируется без ошибок.
