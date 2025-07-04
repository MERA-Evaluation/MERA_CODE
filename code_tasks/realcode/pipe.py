from typing import Any, Dict, List
from datetime import datetime


def doc_to_text_fg(doc: Dict[str, Any]) -> str:
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
    return doc["instruction"].format(**doc["inputs"])

def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")


def process_results(doc: Dict[str, Any], results: List[Dict[str, Any]]) -> Dict[str, float]:
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
    column_replace_dict = {
        "pass_gen": "pass@1",
        "pass_gt": "pass_oracle@1",
        "pass_return_pass": "pass_stub_pass@1",
        "pass_return_empty_str": "pass_stub_empty_str@1",
        "pass_dry_run": "pass_dry_run@1",
        "status": "execution_success"
    }

    metrics = results[0]
    if isinstance(metrics, dict):
        res = {
            column_replace_dict[key]: metrics[key]
            for key in column_replace_dict
            if key in metrics
        }

        res["num_samples"] = 1
        return res
    else:
        return {
            "pass@1": 0.0,
            "pass_oracle@1": 0.0,
            "pass_stub_pass@1": 0.0,
            "pass_stub_empty_str@1": 0.0,
            "pass_dry_run@1": 0.0,
            "execution_success": 0.0,
            "num_samples": 0.0
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
