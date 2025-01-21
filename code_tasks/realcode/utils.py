import json
import os
from typing import Dict, List

try:
    from realcode_eval.lm_eval.evaluator import Evaluator
    from realcode_eval.lm_eval.datatypes import Task
    from lm_eval.api.filter import Filter
    from lm_eval.api.registry import register_filter
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "`realcode_eval` is required for realcode task metric calculation, install via \n"
        "`pip install git+https://github.com/NLP-Core-Team/RealCode_eval.git@v3_pip_package`"
    )


def doc_to_text_fg(doc):
    return f"{doc['left_context']}\n"


def doc_to_text_sg(doc):
    return (
        f"{doc['left_context']}"
        "(Fill in the missing code below. Ensure proper indentation and continue logically from the left context.)\n"
        f"{doc['right_context']}\n"
        "Missing code:\n"
    )


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


@register_filter("scoring")
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

        self.evaluator = Evaluator(
            dataset_root=self.dataset_root,
            num_samples=1,
            pass_k_list=[1],
            njobs=self.test_n_jobs,
            working_dir=self.working_dir,
        )

    def apply(self, resps, docs):
        generations = [[gen[0]] for gen in resps]  # Extract first generation per response

        self._save_to_file(self.generations_output_filepath, generations)

        dataset = self._load_dataset(docs)[:len(generations)]
        processed_gens = [
            [_postprocess(gen, get_indent(task.gt)) for gen in gens]
            for task, gens in zip(dataset, generations)
        ]

        metrics = self.evaluator.evaluate(dataset, processed_gens)
        self._save_to_file(self.metrics_output_filepath, metrics)

        return [[detailed] for detailed in metrics["detailed"]]

    @staticmethod
    def _save_to_file(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            json.dump(data, file)

    def _load_dataset(self, docs) -> List[Task]:
        return [Task(**doc) for doc in docs]


def process_results(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    metrics = results[0]
    return {
        "pass@1": metrics.get("Pass@1", 0.0),
        "exact_match": metrics.get("exact_match", 0.0),
        "compilation_error_rate": metrics.get("compilation_error_rate", 1.0),
    }
