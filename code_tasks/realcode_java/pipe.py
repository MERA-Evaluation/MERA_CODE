import json
import os
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

os.environ['REPOTEST_MAIN_FOLDER'] = '/media/dmitry/data/cache/repotest'
os.environ['REPOTEST_CACHE_FOLDER'] = '/media/dmitry/data/cache/repotest/repos'
from repotest import __version__ as repotest_version
from repotest.constants import disable_stdout_logs, enable_stdout_logs
from repotest.manager.realcode_java_evaluator import JavaEvaluatorRealcode

if not (repotest_version >= "0.3.89"):
    raise ImportError(f"Current repotest version is {repotest_version} it should be 0.3.89")


#ToDo: move this to repotest level
# Disable frozen=True, make it inplace
@dataclass(frozen=True)
class Task:
    id: int
    repo: str
    base_commit: str
    image_name: str
    build_command: str
    test_command: str
    file_path: str
    PASS_TO_PASS: str
    FAIL_TO_PASS: str
    gt: str
    stub: str
    intent: str
    intent_type: str
    left_context: str
    right_context: str


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
    return doc["instruction"].format(**doc["inputs"])


@register_filter("extract_from_tag_realcode_java")
class FromTagExtractorRCJava(Filter):
    def __init__(self) -> None:
        super().__init__()

    def apply(self, resps: List[List[str]], docs: List[Dict[str, Any]]) -> List[List[str]]:
        """
        Extract code blocks from responses.

        Parameters
        ----------
        resps : list of list of str
            List of generations per document.
        docs : list of dict
            Unused, present for compatibility.

        Returns
        -------
        list of list of str
            Code blocks extracted from between markdown tags.
        """
        code_results = []
        for sample in resps:
            sample_metrics = list(map(self._extract_from_tag, sample))
            code_results.append(sample_metrics)
        return code_results

    def _extract_from_tag(self, text: str) -> str:
        """
        Extract text between triple-backtick Java tags.

        Parameters
        ----------
        text : str
            Full model output text.

        Returns
        -------
        str
            Extracted code or original text if tags not found.
        """
        tag_start = "```java"
        tag_end = "```"
        index_start = text.find(tag_start)

        if index_start == -1:
            index_end = text.find(tag_end, 0)
        else:
            index_end = text.find(tag_end, index_start + len(tag_start))

        if index_start == -1 or index_end == -1:
            return text

        return text[index_start + len(tag_start): index_end]
    

def cut_c_style_func_body(prediction: str, left_ctx: Optional[str] = None):
    if left_ctx is None:
        text = prediction
        is_body = True
        c = 1  # счетчик скобок
        j = 0  # сколько доп. символов было добавлено
    else:
        left_ctx_last_line = left_ctx.splitlines()[-1]
        text = left_ctx_last_line + prediction
        is_body = False
        c = 0
        j = len(left_ctx_last_line)
    
    quotes_open = False
    for i, char in enumerate(text):
        if char == '"':
            quotes_open = not quotes_open
        if quotes_open:
            continue
        if char == '{':
            is_body = True
            c += 1
        elif char == '}':
            c -= 1
            if c == 0 and is_body and i-j >= 5:
                return prediction[:i-j+1]
    return None


def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")


@register_filter("scoring_realcode_java")
class ScoringFilterRCJava(Filter):
    def __init__(
        self,
        working_dir: str,
        generations_output_filepath: str,
        metrics_output_filepath: str,
        html_output_filepath: str,
        mode: str = 'docker',
        n_jobs: int = 1,
        gen_columns: List[str] = ['gt', 'stub'],
        raise_exception: bool = True,
        n_jobs_build: int = 1,
        enable_full_logs: bool = False,
        run_id: str = get_run_id()
    ) -> None:
        """
        Initializes the scoring filter with configuration for dataset, paths and logging.
        """
        super().__init__()
        self.working_dir = working_dir
        self.run_id = run_id

        # Verbose output folder
        print("Run_id=%s output folder=%s"%(run_id, os.path.abspath(os.path.join(working_dir, run_id))))
        self.generations_output_filepath = generations_output_filepath
        self.metrics_output_filepath = metrics_output_filepath
        self.html_output_filepath = html_output_filepath

        if enable_full_logs:
            enable_stdout_logs()
        else:
            disable_stdout_logs()

        self.pipeline = JavaEvaluatorRealcode(
            mode=mode,
            n_jobs=n_jobs,
            gen_columns=gen_columns,
            raise_exception=raise_exception,
            n_jobs_build=n_jobs_build
        )

    def apply(self, resps: List[List[str]], docs: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Process generations and run scoring.

        resps -> generation -> task_list --[eval inplace]-> task_list
        Parameters
        ----------
        resps : list of list of str
            Model responses.
        docs : list of dict
            Original document data.

        Returns
        -------
        list of list of dict
            Evaluation results per task.

        
        """
        generations = [[gen[0]] for gen in resps]
        self._save_to_file(self.generations_output_filepath, generations)
        self._save_to_file(os.path.join(self.working_dir, self.run_id, "generations.json"), 
                           generations
                          )

        dataset = self._load_dataset(docs)[:len(generations)]
        processed_gens = [
            [cut_c_style_func_body(gen, task.left_context) for gen in gens]
            for task, gens in zip(dataset, generations)
        ]

        task_list = []
        for task, gens in zip(dataset, processed_gens):
            task_list.append({
                **asdict(task),
                "gen": gens[0],
                "gt": task.gt,
                "stub": task.stub,
            })
        self.pipeline.inplace_build_and_eval(task_list)

        # Save artifacts after generations
        self._save_to_file(os.path.join(self.working_dir, self.run_id, "task_list.json"), 
                           task_list
                           )

        return [[i] for i in task_list]

    @staticmethod
    def _save_to_file(filepath: str, data: Any) -> None:
        """
        Save data to a JSON file.

        Parameters
        ----------
        filepath : str
            File path.
        data : any
            Data to serialize.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as file:
            json.dump(data, file)

    def _load_dataset(self, docs: List[Dict[str, Any]]) -> List[Task]:
        """
        Convert document list to Task instances.

        Parameters
        ----------
        docs : list of dict
            List of document dictionaries.

        Returns
        -------
        list of Task
        """
        return [Task(**doc['meta']) for doc in docs]


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
    column_replace_dict = {
        "pass_gen": "pass@1",
        "pass_gt": "pass_oracle@1",
        "pass_stub": "pass_stub_pass@1",
        "pass_empty_str": "pass_stub_empty_str@1",
        "pass_dry_run": "pass_dry_run@1",
        "status": "execution_success"
    }

    metrics = results[0]
    res = {
        column_replace_dict[key]: metrics[key]
        for key in column_replace_dict
        if key in metrics
    }

    res["num_samples"] = 1
    return res


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
