from typing import Dict, List
import numpy as np
import os


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:
    if len(doc["outputs"]) > 0 and isinstance(results[0], list):
        output_results = []
        pass1_outputs = results[0]
        for score in pass1_outputs:
            output_results.extend([score])

        total, correct = len(output_results), sum(output_results)

        pass_1 = compute_pass_k(total, correct, 1)
        pass_5 = compute_pass_k(total, correct, 5)
        pass_10 = compute_pass_k(total, correct, 10)
        return {"pass@1": pass_1, "pass@5": pass_5, "pass@10": pass_10}
    return {
        "pass@1": 0.0,
        "pass@5": 0.0,
        "pass@10": 0.0,
    }
	
	
def compute_pass_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))
