from typing import Dict, List


INSTRUCTION = ("Даны два кода: фокальный и тест. Определи, скомпилируется ли тест. "
               "Верни failed, если не скомпилируется, и success, если скомпилируется.\n{inputs}")


def doc_to_text(doc: dict) -> str:
    focal = doc['focal_code']
    test = doc['test_code']
    inputs = f'{focal}\n{test}'
    prompt = INSTRUCTION.format(inputs=inputs)

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
