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
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(self) -> None:
        super().__init__()

    def apply(self, resps, docs, predict_only = False):
        # resps: List[List[str]] - list of list generations
        if predict_only:
            return resps
        code_results = []
        for idx, sample in enumerate(resps):
            sample_metrics = list(map(self._extract_from_tag, sample))
            code_results.extend([sample_metrics])
        return code_results

    def _extract_from_tag(self, text):
        return parse_generation(text)


@register_filter("scoring")
class ScoringFilter(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(self,) -> None:
        super().__init__()
    
    def load_config(self):
        import yaml

        with open("code_tasks/yabloco/yabloco_config.yaml") as f:
            config = yaml.safe_load(f)
    
        self.working_dir = os.getenv("YABLOCO_WORKING_DIR", config["working_dir"])
        self.bench_version = os.getenv("YABLOCO_BENCH_VERSION", config["bench_version"])
        self.generations_output_filepath = os.getenv("YABLOCO_GENERATION_OUTPUT_FILEPATH", config["generations_output_filepath"])
        self.metrics_output_filepath = os.getenv("YABLOCO_METRICS_OUTPUT_FILEPATH", config["metrics_output_filepath"])

    def apply(self, resps, docs, predict_only = False):
        if predict_only:
            return resps
        self.load_config()
        generations = [[gen[0]] for gen in resps]  # Extract first generation per response
        self._save_to_file(self.generations_output_filepath, generations)

        generations = {
            doc["meta"]["original_id"]: gen[0]
            for doc, gen in zip(docs, generations)
        }

        sys.path.append(self.working_dir)

        try:
            from compute import run_tests
        except ImportError:
            print("WARNING! You are running task `yabloco` but do not have library `compute` installed.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library.")

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
