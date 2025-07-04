# CodeCorrectness


## Описание задачи

Оценка корректности написанного кода для языков Python, Java, Go. Под корректностью кода подразумевается отсутствие любых ошибок, включая SyntaxError, RuntimeError и др., а также успешное прохождение тестов. Датасет содержит `1361` задачу.

Тестируемые навыки моделей: Instruction Following, Code Perception, Simulation, Error Classification

Авторы: Елена Бручес, Иван Бондаренко, Даниил Гребёнкин, Олег Седухин, Роман Дерунец, Георгий Мкртчян, Вадим Альперович, Николай Бушков, Станислав Моисеев


## Мотивация

Предполагается, что в процессе обучения модель не только учится писать код и решать различные задачи, но также учится и анализировать код, например, является ли код корректным, содержит ли ошибки и т.д. Данный датасет был разработан для автоматической оценки этой способности моделей. Для модели, выполняющей оценку успешности кода, необходимо ограничить контекст. Чтобы понять, является ли код успешно выполнимым, мы собрали такие пары {focal_code - test_code}, которые не содержат импортов из других файлов проектов, а также в данных парах не используются assets (например, загрузка данных из файлов).


## Описание датасета

### Поля данных

Каждый вопрос в датасете содержит следующие поля:

- `instruction` [str] — Промпт-инструкция для модели, содержащая шаблон для вставки элементов вопроса.
- `inputs` — Вводные данные, формирующие задание для модели. Могут включать одну или несколько модальностей - видео, аудио, изображение, текст.
    - `focal_code` [str] — Исходный код фокального файла;
    - `test_code` [str] — Исходный код тестового файла;
    - `lang` [str] — Язык программирования данного примера;
- `outputs` [str] — Ответ модели, должен быть success или failed;
- `meta` — Метаданные, относящиеся к тестовому примеру, но не используемые в вопросе (скрытые от тестируемой модели).
    - `id` [int] — Номер-идентификатор вопроса в датасете.


### Пример данных

```json
{
    "instruction": "Ниже приведён код фокального файла и тестового файла. Определи, является ли тест корректным.\n\nФокальный файл:\n\n{lang}\n\n{focal_code}\n\n\nТестовый файл:\n\n{lang}\n\n{test_code}\n\nОтветь одним словом. Если тест не вызовет ошибок при запуске программы, то верни \"succeed\". Иначе верни \"fail\".",
    "inputs": {
        "focal_code": "import functools\\nimport time\\nfrom collections import OrderedDict\\nfrom typing import Any, Callable, Generic, Iterable, Iterator, Tuple, TypeVar\\n\\nT = TypeVar(\\\"T\\\")\\n\\n\\nclass Cache(Generic[T]):\\n    \\\"\\\"\\\"In-memory LRU cache implementation.\\\"\\\"\\\"\\n\\n    def __init__(self, max_size: int = 500):\\n        self._bag: OrderedDict[Any, Any] = OrderedDict()\\n        self._max_size = -1\\n        self.max_size = max_size\\n\\n    @property\\n    def max_size(self) -> int:\\n        return self._max_size\\n\\n    @max_size.setter\\n    def max_size(self, value: int) -> None:\\n        assert value > 0\\n        self._max_size = int(value)\\n\\n    @property\\n    def is_empty(self) -> bool:\\n        return len(self._bag) == 0\\n\\n    def values(self) -> Iterable[T]:\\n        for _, value in self:\\n            yield value\\n\\n    def keys(self) -> Iterable[Any]:\\n        for key, _ in self:\\n            yield key\\n\\n    def __repr__(self) -> str:\\n        return f\\\"<Cache {len(self)} at {id(self)}>\\\"\\n\\n    def __len__(self) -> int:\\n        return len(self._bag)\\n\\n    def get(self, key, default=None) -> T:\\n        try:\\n            return self[key]\\n        except KeyError:\\n            return default\\n\\n    def set(self, key, value) -> None:\\n        self[key] = value\\n\\n    def _check_size(self):\\n        while len(self._bag) > self.max_size:\\n            self._bag.popitem(last=False)\\n\\n    def __getitem__(self, key) -> T:\\n        value = self._bag[key]\\n        self._bag.move_to_end(key, last=True)\\n        return value\\n\\n    def __setitem__(self, key, value: T) -> None:\\n        if key in self._bag:\\n            self._bag[key] = value\\n            self._bag.move_to_end(key, last=True)\\n        else:\\n            self._bag[key] = value\\n            self._check_size()\\n\\n    def __delitem__(self, key) -> None:\\n        del self._bag[key]\\n\\n    def __contains__(self, key) -> bool:\\n        return key in self._bag\\n\\n    def __iter__(self) -> Iterator[Tuple[Any, T]]:\\n        return iter(self._bag.items())\\n\\n    def clear(self) -> None:\\n        self._bag.clear()\\n\\n\\nclass CachedItem(Generic[T]):\\n    \\\"\\\"\\\"Container for cached items with update timestamp.\\\"\\\"\\\"\\n\\n    __slots__ = (\\\"_value\\\", \\\"_time\\\")\\n\\n    def __init__(self, value: T):\\n        self._value = value\\n        self._time = time.time()\\n\\n    @property\\n    def value(self) -> T:\\n        return self._value\\n\\n    @value.setter\\n    def value(self, value: T):\\n        self._value = value\\n        self._time = time.time()\\n\\n    @property\\n    def time(self) -> float:\\n        return self._time\\n\\n\\nclass ExpiringCache(Cache[T]):\\n    \\\"\\\"\\\"A cache whose items can expire by a given function.\\\"\\\"\\\"\\n\\n    def __init__(\\n        self, expiration_policy: Callable[[CachedItem[T]], bool], max_size: int = 500\\n    ):\\n        super().__init__(max_size)\\n        assert expiration_policy is not None\\n        self.expiration_policy = expiration_policy\\n\\n    @property\\n    def full(self) -> bool:\\n        return self.max_size <= len(self._bag)\\n\\n    def expired(self, item: CachedItem) -> bool:\\n        return self.expiration_policy(item)\\n\\n    def _remove_expired_items(self):\\n        for key, item in list(self._bag.items()):\\n            if self.expired(item):\\n                del self[key]\\n\\n    def _check_size(self):\\n        if self.full:\\n            self._remove_expired_items()\\n        super()._check_size()\\n\\n    def __getitem__(self, key) -> Any:\\n        item = self._bag[key]\\n        if self.expired(item):\\n            del self._bag[key]\\n            raise KeyError(key)\\n\\n        self._bag.move_to_end(key, last=True)\\n        return item.value\\n\\n    def __setitem__(self, key, value: T) -> None:\\n        if key in self._bag:\\n            self._bag[key].value = value\\n            self._bag.move_to_end(key, last=True)\\n        else:\\n            self._bag[key] = CachedItem(value)\\n            self._check_size()\\n\\n    @classmethod\\n    def with_max_age(cls, max_age: float, max_size: int = 500):\\n        \\\"\\\"\\\"\\n        Returns an instance of ExpiringCache whose items are invalidated\\n        when they were set more than a given number of seconds ago.\\n        \\\"\\\"\\\"\\n        return cls(lambda item: time.time() - item.time > max_age, max_size)\\n\\n    def __contains__(self, key) -> bool:\\n        if key not in self._bag:\\n            return False\\n        # remove if expired\\n        try:\\n            self[key]\\n        except KeyError:\\n            return False\\n        return True\\n\\n    def __iter__(self) -> Iterator[Tuple[Any, T]]:\\n        \\\"\\\"\\\"Iterates through cached items, discarding and removing expired ones.\\\"\\\"\\\"\\n        for key, item in list(self._bag.items()):\\n            if self.expired(item):\\n                del self[key]\\n            else:\\n                yield (key, item.value)\\n\\n\\ndef lazy(max_seconds: int = 1, cache=None):\\n    \\\"\\\"\\\"\\n    Wraps a function so that it is called up to once\\n    every max_seconds, by input arguments.\\n    Results are stored in a cache, by default a LRU cache of max size 500.\\n\\n    To have a cache without size limit, use a dictionary: @lazy(1, {})\\n    \\\"\\\"\\\"\\n    assert max_seconds > 0\\n    if cache is None:\\n        cache = Cache(500)\\n\\n    def lazy_decorator(fn):\\n        setattr(fn, \\\"cache\\\", cache)\\n\\n        @functools.wraps(fn)\\n        def wrapper(*args):\\n            now = time.time()\\n            try:\\n                value, updated_at = cache[args]\\n                if now - updated_at > max_seconds:\\n                    raise AttributeError\\n            except (KeyError, AttributeError):\\n                value = fn(*args)\\n                cache[args] = (value, now)\\n            return value\\n\\n        return wrapper\\n\\n    return lazy_decorator\\n",
        "test_code": "import time\\n\\nimport pytest\\n\\nfrom essentials.caching import Cache, ExpiringCache, lazy\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\n\\ndef test_expiration_policy_with_max_age():\\n    cache = ExpiringCache.with_max_age(0.1)\\n    cache[\\\"foo\\\"] = \\\"Foo\\\"\\n\\n    time.sleep(0.2)\\n\\n    assert cache.get(\\\"foo\\\") is None\\n\\n    cache[\\\"foo\\\"] = \\\"Foo\\\"\\n\\n    time.sleep(0.2)\\n\\n    assert \\\"foo\\\" not in cache\\n",
        "lang": "Python"
    },
    "outputs": "success",
    "meta": {
        "id": 1
    }
}
```


### Промпты

Для задачи были подготовлены 11 промптов, которые были равномерно распределены по вопросам по принципу "один вопрос – один промпт". Шаблоны в фигурных скобках в промпте заполняются из полей внутри поля `inputs` в каждом вопросе.


Пример промпта:

```
Вот код из фокального файла на языке {lang}:

{focal_code}

Проверь, корректен ли тест для этого кода:

{test_code}

Дай короткий ответ: если тест пройдет без ошибок, скажи "success", иначе — "failed".
```


### Создание датасета

Создание датасета состояло из нескольких этапов:

1) Автоматический поиск, парсинг и обработка открытых репозиториев GitHub по критериям популярности (количество "звездочек"), актуальности (даты последних коммитов) и компилируемости (проверка на успешность сборки проекта и компиляции тестов/фокальных файлов);
2) Формирование сэмплов датасета из данных (тестовых и фокальных файлов) репозитория в следующем формате: код фокального файла | код тест-кейса; 
3) Далее были сформированы 2 сабсета: original (исходные тест-кейсы), generated (сгенерированные LLM тест-кейсы); 
4) Для данных, полученных в этих сабсетах, было выполнено тэгирование, где каждый тэг представлял собой какую-то характеристику тест-кейса или фокального файла (количество строк в тест-кейсе, количество строк в фокальном файле, синтаксическая корректность, наличие импортов определенных видов и т.п.); 
5) Данные датасета были отфильтрованы по этим тэгам так, чтобы LLM могла решить задачу определения корректности тест-кейса по инпуту;
6) Из отфильтрованных данных была сформирована конечная версия датасета.


## Оценка


### Метрики

Для агрегированной оценки ответов моделей используются следующие метрики:

- `Exact Match`: Метрика вычисляет долю точно совпавших с ответом предсказаний модели среди всех обработанных вопросов.
