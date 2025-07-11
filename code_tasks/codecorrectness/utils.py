from typing import Dict, List


def doc_to_text(doc: dict) -> str:
    inputs = doc["inputs"]
    focal_code = inputs["focal_code"]
    test_code = inputs["test_code"]
    lang = inputs["lang"]

    prompt = doc["instruction"].format(
        focal_code=focal_code, test_code=test_code, lang=lang
    )

    return prompt.strip()


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:
    has_outputs = doc["outputs"] is not None
    if has_outputs:
        gold = doc["outputs"]
        pred = -1
        if "failed" in results[0] and "success" in results[0]:
            pred = -1
        elif "failed" in results[0]:
            pred = "failed"
        elif "success" in results[0]:
            pred = "success"
        acc = float(pred == gold)
        return {"acc": acc}
    if not has_outputs:
        # если ответов нет, то нули
        return {"acc": 0.0}
