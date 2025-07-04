from typing import Dict, List


def doc_to_text(doc):
    return doc["instruction"].format(**doc["inputs"]).strip()


def process_results(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    metrics = results[0]
    if isinstance(metrics, dict):
        return {
            "pass@1": metrics.get("pass@1", 0.0),
            "exact_match": metrics.get("exact_match", 0.0),
        }
    return {
        "pass@1": 0.0,
        "exact_match": 0.0
    }
