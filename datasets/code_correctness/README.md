# CodeCorrectness


## Task description

Evaluation of the correctness of the written code for Python, Java and Go. Correctness means the absent of any errors including SyntaxError, Runtime Error etc. and the successful tests passing as well.

Evaluated skills: Instruction following, Perception (Python, Java, Go), Code correctness classification

Contributors: Elena Bruches, Ivan Bondarenko, Daniil Grebenkin, Oleg Sedukhin, Roman Derunets, Georgii Mkrtchyan, Vadim Alperovich


## Motivation

It is assumed that during the training process the model learns not only to generate the code and solve different tasks but also learns to process and analyze the code, e.g. to detect whether the code is correct, contains any errors etc. This dataset was developed to automatically evaluate such ability. Any model, which assess the code correctness, should be limited with a given context. To define whether the code is successfully executed, we collected such pairs {focal_code - test_code}, which do not contain the imports from the other files of the projects. Also we kept only the files which do not contain any assets usage, e.g. loading data from files.


## Data description

### Data fields

Each dataset question includes data in the following fields:

- `instruction` [str] — Instruction prompt template with question elements placeholders.
- `inputs` — Input data that forms the task for the model. Can include one or multiple modalities - video, audio, image, text.
    - `focal_code` [str] — Source code from the focal file;
    - `test_code` [str] — Source code from the test file;
    - `lang` [str] — Programming language of this sample;
- `outputs` [str] — Answer of the model, should be either "success" or "failed";
- `meta` — Metadata related to the test example, not used in the question (hidden from the tested model).
    - `id` [int] — Identification number of the question in the dataset.


### Data formatting example

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


### Prompts

For the task, 10 prompts were prepared and evenly distributed among the questions on the principle of "one prompt per question". The templates in curly braces in each prompt are filled in from the fields inside the `inputs` field in each question.

Prompt example:

```
Ниже приведён код фокального файла и тестового файла. Определи, является ли тест корректным.

Фокальный файл:

{lang}

{focal_code}


Тестовый файл:

{lang}

{test_code}

Ответь одним словом. Если тест не вызовет ошибок при запуске программы, то верни "success". Иначе верни "failed".
```


### Dataset creation

The dataset creation includes the following stages:

1) Automatic retrieval, parsing and processing of open-source repositories from GitHub based on the number of stars, novelty (date of the latest commits) and execution (check whether the project is built successfully and focal and test files are executed successfully);
2) The collection of dataset samples from the repositories data in the following format: focal file source code | test file source code;
3) The creation of two subsets: original (the samples contain the original test files) and generated (the samples contain the generated test cases by LLM);
4) The samples were tagged with the following features: the number of lines in test case, the number of lines in the focal file, syntax correctness, import types etc.;
5) The samples were filtered out to keep only the samples for which the task of correctness determining may be solved without additional inputs.
6) The final version of the dataset was formed from the filtered data. 


## Evaluation


### Metrics

Metrics for aggregated evaluation of responses:

- `Accuracy`: Accuracy is the proportion of correct model predictions among the total number of cases processed.
