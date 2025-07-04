from typing import List, Dict, Any


def doc_to_text_java_testgen(doc: Dict[str, Any]) -> str:
    return doc["instruction"].format(**doc["inputs"])


def process_results_java_testgen(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    if isinstance(results[0], dict):
        metrics = results[0]['evaluation']
        return {
            "pass@1": float(metrics["parser"]["success"]),
            "compile@1": float(metrics["parser"]["compiled"]),
        }
    else:
        return {
            "pass@1": 0.0,
            "compile@1": 0.0,
        }
