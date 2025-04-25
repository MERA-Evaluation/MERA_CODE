import json
import os
import tempfile
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

from jsonl2html import convert_jsonl_to_html
from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter
from repotest import __version__ as repotest_version
from repotest.constants import disable_stdout_logs, enable_stdout_logs
from repotest.manager.realcode_python_task_manager import TaskManagerRealcode
from datetime import datetime

if not (repotest_version >= "0.3.52"):
    raise ImportError(f"Current repotest version is {repotest_version} it should be 0.3.52")

#ToDo: move this to repotest level
# Disable frozen=True, make it inplace
@dataclass(frozen=True)
class Task:
    repo: str
    base_commit: str
    test_command: str
    build_command: str
    image_name: str
    left_context: str
    gt: str
    right_context: str
    fn: str
    PASS_TO_PASS: str
    FAIL_TO_PASS: str
    _more_params: str


def doc_to_text_fg(doc: Dict[str, str]) -> str:
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
    return f"{doc['left_context']}\n"


def doc_to_text_sg(doc: Dict[str, str]) -> str:
    """
    Builds a prompt-style string from document contexts.

    Parameters
    ----------
    doc : dict
        Document with 'left_context' and 'right_context'.

    Returns
    -------
    str
        Combined string formatted for a model prompt.
    """
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
        Extract text between triple-backtick Python tags.

        Parameters
        ----------
        text : str
            Full model output text.

        Returns
        -------
        str
            Extracted code or original text if tags not found.
        """
        tag_start = "```python"
        tag_end = "```"
        index_start = text.find(tag_start)

        if index_start == -1:
            index_end = text.find(tag_end, 0)
        else:
            index_end = text.find(tag_end, index_start + len(tag_start))

        if index_start == -1 or index_end == -1:
            return text

        return text[index_start + len(tag_start): index_end]


def get_indent(code: str) -> int:
    """
    Determines indentation level of first non-empty line.

    Parameters
    ----------
    code : str
        Multiline code string.

    Returns
    -------
    int
        Number of leading spaces.
    """
    try:
        line = next(t for t in code.split('\n') if t.strip())
        return len(line) - len(line.lstrip())
    except StopIteration:
        return 0


def _postprocess(generation: str, indent: int) -> str:
    """
    Trims generation based on indentation rules.

    Parameters
    ----------
    generation : str
        Generated code.
    indent : int
        Indentation level to respect.

    Returns
    -------
    str
        Postprocessed code string.
    """
    new_gen = []
    for line in generation.split('\n'):
        if line.strip() and get_indent(line) < indent:
            break
        new_gen.append(line)
    return "\n".join(new_gen).rstrip() + '\n\n'

def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")

@register_filter("scoring")
class ScoringFilter(Filter):
    def __init__(
        self,
        working_dir: str,
        generations_output_filepath: str,
        metrics_output_filepath: str,
        html_output_filepath: str,
        mode: str = 'docker',
        n_jobs: int = 1,
        gen_columns: List[str] = ['gt', 'return_pass', 'return_empty_str', "gen"],
        raise_exception: bool = True,
        n_jobs_build: int = 1,
        enable_full_logs: bool = False,
        run_id = get_run_id()
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

        self.manager = TaskManagerRealcode(
            mode=mode,
            n_jobs=n_jobs,
            gen_columns=gen_columns,
            raise_exception=raise_exception,
            n_jobs_build=n_jobs_build
        )

    def _generate_empty_string_code(self, gt: str) -> str:
        return " " * get_indent(gt) + 'pass'

    def _generate_pass_code(self, gt: str) -> str:
        return " " * get_indent(gt) + 'return ""'

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
            [_postprocess(gen, get_indent(task.gt)) for gen in gens]
            for task, gens in zip(dataset, generations)
        ]

        task_list = []
        for task, gen in zip(dataset, processed_gens):
            task_list.append({
                **asdict(task),
                "gen": gen[0],
                "gt": task.gt,
                "return_pass": self._generate_empty_string_code(task.gt),
                "return_empty_str": self._generate_pass_code(task.gt)
            })

        self.manager.inplace_build_and_eval(task_list)

        # Save artifacts after generations
        self._save_to_file(os.path.join(self.working_dir, self.run_id, "task_list.json"), 
                           task_list
                           )

        # Save html vizualization
        self.create_vizualization(task_list, self.html_output_filepath)
        self.create_vizualization(task_list, os.path.join(self.working_dir, self.run_id, "task_list.html"))

        return [[i] for i in task_list]

    @staticmethod
    def create_vizualization(task_list: List[Dict[str, Any]], fn_html_output_filepath: str) -> None:
        """
        Create an HTML visualization of tasks.

        Parameters
        ----------
        task_list : list of dict
            List of task records to visualize.
        fn_html_output_filepath : str
            Output HTML file path.
        """
        with tempfile.NamedTemporaryFile(mode='w+', delete=True, suffix='.jsonl') as tmpfile:
            for task in task_list:
                tmpfile.write(json.dumps(task) + '\n')
            convert_jsonl_to_html(
                fn_input=tmpfile.name,
                index_column='auto',
                fn_output=fn_html_output_filepath,
                additional_table_content={"content": "value"}
            )

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
        return [Task(**doc) for doc in docs]


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
    column_replace_dict = {"pass_gen": "pass_gen@1"}

    metrics = results[0]
    res = {column_replace_dict.get(key, key): metrics.get(key, 0.0) for key in [
        'pass_dry_run', 'pass_gt', 'pass_return_pass',
        'pass_return_empty_str', 'pass_gen', 'status'
    ]}
    res['num_of_samples'] = 1
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