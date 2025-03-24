from typing import Dict, List

def doc_to_text(doc: dict) -> str:
    focal = doc['focal_code']
    test = doc['test_code']
    lang = doc['lang']

    prompt = f"""
Ниже приведён код фокального файла и тестового файла. Определи, является ли тест корректным.

Фокальный файл:

```{lang}

{focal}

```


Тестовый файл:

```{lang}

{test}

```

Ответь одним словом. Если тест не вызовет ошибок при запуске программы, то верни "succeed". Иначе верни "fail".
    """

    return prompt.strip()


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:
    has_outputs = doc['status'] is not None
    if has_outputs:
        gold = doc['status']
        pred = -1
        if 'failed' in results[0]:
            pred = 'failed'
        elif 'success' in results[0]:
            pred = 'success'
        acc = float(pred == gold)
        return {"acc": acc}
    if not has_outputs:
        # если ответов нет, то нули
        return {
            "acc": 0.0
        }
