from datetime import datetime
from typing import Any, Dict, List, Optional


def doc_to_text_realcode_java(doc: Dict[str, Any]) -> str:
    """
    Extracts foreground text from a document.

    Parameters
    ----------
    doc : dict
        Document containing at least 'left_context'.

    Returns
    -------
    str
        The extracted foreground text.
    """
    # В промтах упоминаются фигурные скобки { },
    # из-за чего str.format падает
    instruction = doc["instruction"]
    for field, value in doc["inputs"].items():
        instruction = instruction.replace('{'+field+'}', value)
    return instruction

def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def process_results_realcode_java(doc: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extract and summarize metrics from task results.

    Parameters
    ----------
    doc : dict
        Original input document (unused).
    results : list of dict
        Evaluation output for a single task.

    Returns
    -------
    dict
        Dictionary with key metrics.
    """
    metrics = results[0]
    if isinstance(metrics, dict):
        res = {
            "pass@1": metrics.get("pass_gen", 0),
            "pass_oracle@1": metrics.get("pass_gt", 0),
            "pass_stub_pass@1": metrics.get("pass_stub", 0),
            "pass_dry_run@1": metrics.get("pass_dry_run", 0),
            "execution_success": metrics.get("status", 0),
            "num_samples": 1,
        }
        return res
    else:
        return {
            "pass@1": 0.0,
            "pass_oracle@1": 0.0,
            "pass_stub_pass@1": 0.0,
            "pass_dry_run@1": 0.0,
            "execution_success": 0.0,
            "num_samples": 0.0,
        }


def sum_metric(values: List[float]) -> float:
    """
    Compute sum over list of values.

    Parameters
    ----------
    values : list of float

    Returns
    -------
    float
        Total sum.
    """
    return sum(values)
