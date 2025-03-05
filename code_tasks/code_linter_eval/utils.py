import ast
import contextlib
import faulthandler
import io
import os
import platform
import signal
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

import multiprocess as mp
import numpy as np

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

import uuid
import os
import subprocess
import json


def process_results(doc: Dict, results: List[str]) -> Dict[str, float]:
    if len(doc["outputs"]) > 0:
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
    }  # if no label provided (test answers are secret)
	
	
@register_filter("rucodelinterevalscoring")
class ruCodeLinterEvalScoring(Filter):
    def __init__(self) -> None:
        """
        Считывание необходимых для фильтра параметров
        """

    def apply(self, resps, docs):
        """
        Метод, который отвечает за применение фильтра
        """
        code_results = []
        for idx, sample in enumerate(resps):
            sample_metrics = []
            for completion in sample:
                processed_completion = preprocess_generation(completion)
                pass1 = execute_function(processed_completion)
                sample_metrics.extend([pass1])
            code_results.extend([sample_metrics])
        return code_results
		

# TODO: реализовать пост-обработку - ? как сделать универсально
def preprocess_generation(completion):
    if '[PYTHON]' in completion and '[/PYTHON]' in completion:
        start = completion.find('[PYTHON]')+len('[PYTHON]')+1
        finish = completion.find('[/PYTHON]')
    else:
        return 'error parsing'
    return completion[start:finish]
	

def execute_function(processed_completion):
    id = str(uuid.uuid4())
    LINTER_PATH = os.getenv("LINTER_PATH")
    os.makedirs('./extracted_codes', exist_ok=True)
    os.makedirs('./reports', exist_ok=True)
    
    code_file_path = f'./extracted_codes/temporary_file_{id}.py'
    json_report_file = f'./reports/temporary_file_{id}.json'
    json_error_report_file = f'./reports/temporary_file_{id}.json'
    
    with open(code_file_path, 'w') as f:
        f.write(processed_completion) 
        
    try:
        proc = subprocess.Popen([LINTER_PATH, "--format=json", code_file_path], 
                                stdout=open(json_report_file, "w"),
                                stderr=open(json_error_report_file, "w"))
    except:
        raise ValueError('Ошибка! Проверьте установлена ли переменная окружения LINTER_PATH для линтера flake8') 
            
    proc.wait()
    status = proc.returncode
    if status == 1:
        with open(f'./reports/temporary_file_{id}.json', 'r') as file:
            data = json.load(file)
    else:
        with open(f'./reports/temporary_file_{id}.json', 'r') as file:
            data = json.load(file)
    
    codes = []
    for error in data[code_file_path]:
        codes.append(error.get('code', ''))

    if len(codes)>0:
        pass1 = 0
    else:
        pass1 = 1
    return pass1
	
	
def compute_pass_k(n, c, k):
    if n - c < k:
        return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))