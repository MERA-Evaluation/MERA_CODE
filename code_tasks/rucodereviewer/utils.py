from typing import Any, Dict


def doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = doc["instruction"].format(**doc["inputs"])

    return prompt


def process_results(doc: Dict[str, Any], results: list[Dict[str, float]]) -> Dict[str, float]:
    if "bleu" in results[0] and "chrf" in results[0] and "pass@" in results[0]:
        return results[0]
    return {
        "bleu": 0.0,
        "chrf": 0.0,
        "pass@1": 0.0,
        "pass@5": 0.0,
        "pass@10": 0.0
    }
