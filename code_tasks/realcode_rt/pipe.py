from pathlib import Path
# Fix relative imports at LMEH
import sys
sys.path.insert(0, str(Path(__file__).parent))
from evaluate_rt import EvaluatorRT

import json
import os
from typing import Dict, List
from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter
import logging
logger = logging.getLogger("repotest")
logger.setLevel(logging.CRITICAL)


import json
import typing as tp
from task import Task

def doc_to_text_fg(doc):
    return f"{doc['left_context']}\n"

def doc_to_text_rt(doc):
    return (
        f"{doc['left_context']}"
        "(Fill in the missing code below. Ensure proper indentation and continue logically from the left context.)\n"
        f"{doc['right_context']}\n"
        "Missing code:\n"
    )
def doc_to_text_sg(doc):
    return (
        f"{doc['left_context']}"
        "(Fill in the missing code below. Ensure proper indentation and continue logically from the left context.)\n"
        f"{doc['right_context']}\n"
        "Missing code:\n"
    )


@register_filter("extract_from_tag_rt")
class FromTagExtractor(Filter):
    def __init__(self) -> None:
        super().__init__()

    def apply(self, resps, docs):
        # resps: List[List[str]] - list of list generations
        code_results = []
        for idx, sample in enumerate(resps):
            sample_metrics = list(map(self._extract_from_tag, sample))
            code_results.extend([sample_metrics])
        return code_results

    def _extract_from_tag(self, text):
        tag_start = "```python"
        tag_end = "```"
        index_start = text.find(tag_start)

        # Avoid the case that tag_begin contains tag_end, e.g. ```python and ```
        if index_start == -1:
            index_end = text.find(tag_end, 0)
        else:
            index_end = text.find(tag_end, index_start + len(tag_start))

        if index_start == -1 or index_end == -1:
            missing_tags = []
            if index_start == -1:
                missing_tags.append(tag_start)
            if index_end == -1:
                missing_tags.append(tag_end)

            return text

        extract_text = text[index_start + len(tag_start) : index_end]  # noqa: E203

        return extract_text


def get_indent(code):
    line = [t for t in code.split('\n') if t.strip()][0]
    return len(line) - len(line.strip())


def _postprocess(generation: str, indent: int):
    new_gen = []
    for i, line in enumerate(generation.split('\n')):
        if line.strip() != '' and get_indent(line) < indent:
            break
        new_gen.append(line)

    return "\n".join(new_gen).rstrip() + '\n\n'

@register_filter("scoring_rt")
class ScoringFilter(Filter):
    def __init__(
        self,
        dataset_root,
        working_dir,
        test_n_jobs,
        generations_output_filepath,
        metrics_output_filepath,
    ) -> None:
        super().__init__()
        self.dataset_root = dataset_root
        self.working_dir = working_dir
        self.test_n_jobs = test_n_jobs
        self.generations_output_filepath = generations_output_filepath
        self.metrics_output_filepath = metrics_output_filepath

        # self.evaluator = Evaluator(
        #     dataset_root=str(Path(self.dataset_root).resolve()),
        #     num_samples=1,
        #     pass_k_list=[1],
        #     njobs=self.test_n_jobs,
        #     working_dir=str(Path(self.working_dir).resolve()),
        # )
    def _generate_empty_string_code(self, gt):
        return " "*get_indent(gt) + 'pass'

    def _generate_pass_code(self, gt):
        return " "*get_indent(gt) + 'return ""'
    
    def apply(self, resps, docs):
        generations = [[gen[0]] for gen in resps]  # Extract first generation per response

        self._save_to_file(self.generations_output_filepath, generations)

        dataset = self._load_dataset(docs)[:len(generations)]
        processed_gens = [
            [_postprocess(gen, get_indent(task.gt)) for gen in gens]
            for task, gens in zip(dataset, generations)
        ]

        task_list = []
        for task, gen in zip(dataset, processed_gens):
            print(task)
            task_list.append({**task._to_dict(), **{"gen": gen[0],
                                 "gen_gt": task.gt,
                                 "gen_pass": self._generate_empty_string_code(task.gt),
                                 "gen_empty_string": self._generate_pass_code(task.gt)
                                }})
            print(task_list[-1].keys())
        
        evaluator = EvaluatorRT(n_parralel=self.test_n_jobs, 
                                mode='docker',
                                debug = True
                               )
        evaluator.evaluate_list(task_list)
        return [[i] for i in task_list]

    @staticmethod
    def _save_to_file(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            json.dump(data, file)

    def _load_dataset(self, docs) -> List[Task]:
        return [Task(**doc) for doc in docs]


def process_results(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    metrics = results[0]
    res = {key: metrics.get(key, 0.0) for key in ['pass_dry_run', 'pass_gt', 'pass_pass', 
                                                   'pass_return_empty_str', 'pass_gen',
                                                   'evaluate_fail'
                                                   ]
           }
    return res
        #"pass_gen@1": metrics.get("Pass@1", 0.0),
        #"exact_match": metrics.get("exact_match", 0.0),
        #"compilation_error_rate": metrics.get("compilation_error_rate", 1.0),
    # }
