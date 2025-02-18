from typing import Dict, List


INSTRUCTION = ("Даны два кода: фокальный и тест. Определи, скомпилируется ли тест. "
               "Верни 0, если не скомпилируется, и 1, если скомпилируется.\n{inputs}")


def doc_to_text(doc: dict) -> str:
    focal = doc['focal']
    test = doc['test']
    inputs = f'{focal}\n{test}'
    prompt = INSTRUCTION.format(inputs=inputs)

    return prompt.strip()


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:
    has_outputs = doc['label'] is not None
    if has_outputs:
        gold = doc['label']
        pred = -1
        if '1' in results[0]:
            pred = 1
        elif '0' in results[0]:
            pred = 0
        # метрика для данного сэмпла и ответа модели на него
        acc = float(pred == gold)
        # сохранение в словарь общей accuracy, а также запись 0 или 1 в acc.domain
        return {"acc": acc}
    if not has_outputs:
        # если ответов нет, то нули
        return {
            "acc": 0.0
        }
