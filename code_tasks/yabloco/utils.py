import json
import os
import sys
from typing import Dict, List

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter


def doc_to_text(doc):
    return doc["instruction"].format(**doc["inputs"]).strip()


def parse_generation(text):
    if not isinstance(text, str):
        return ""

    # most probably code is tagged with ```
    sections = text.split('```')
    generated_code = "-"
    if len(sections) >= 3:
        generated_code = sections[1]
    if len(sections) == 1:
        generated_code = sections[0]

    remove_prefix = ["cpp", "c++", "c", "++"]
    for pref in remove_prefix:
        generated_code = generated_code.removeprefix(pref)
    generated_lines = generated_code.split('\n')

    # remove redundant code around the target function
    generated_lines = [
        line
        for line in generated_lines
        if not line.startswith("#include")
    ]
    ind_of_main = [
        ind
        for ind, s in enumerate(generated_lines)
        if s.startswith("void main(") or s.startswith("int main(")
    ]

    if len(ind_of_main) != 0:
        generated_lines = generated_lines[:ind_of_main[0]]

    return "\n".join(generated_lines) + "\n"


@register_filter("extract_from_tag")
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
        return parse_generation(text)


@register_filter("scoring")
class ScoringFilter(Filter):
    def __init__(self, working_dir, bench_version, generations_output_filepath, metrics_output_filepath) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.bench_version = bench_version
        self.generations_output_filepath = generations_output_filepath
        self.metrics_output_filepath = metrics_output_filepath

    def apply(self, resps, docs):
        generations = [[gen[0]] for gen in resps]  # Extract first generation per response
        self._save_to_file(self.generations_output_filepath, generations)

        generations = {
            doc["meta"]["id"]: gen
            for doc, gen in zip(docs, generations)
        }

        sys.path.append(self.working_dir)
        from compute import run_tests
        metrics = run_tests(generations, self.working_dir, self.bench_version)

        self._save_to_file(self.metrics_output_filepath, metrics)
        return metrics

    @staticmethod
    def _save_to_file(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            json.dump(data, file)


def process_results(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    metrics = results[0]
    return {
        "pass@1": metrics.get("pass@1", 0.0),
        "exact_match": metrics.get("exact_match", 0.0),
    }
