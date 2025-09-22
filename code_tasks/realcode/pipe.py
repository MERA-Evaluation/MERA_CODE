import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

try:
    from repotest import __version__ as repotest_version
    from repotest.constants import disable_stdout_logs, enable_stdout_logs
    from repotest.manager.realcode_python_task_manager import \
        TaskManagerRealcode

    if not (repotest_version >= "0.3.52"):
        raise ImportError(
            f"Current repotest version is {repotest_version} it should be 0.3.52"
        )
except ImportError:
    print(
        "WARNING! You are running task `realcode` but do not have library `repotest` installed or its version is less than 0.3.52.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library."
    )


try:
    from jsonl2html import convert_jsonl_to_html
except ImportError:
    print(
        "WARNING! You are running task `realcode` but do not have library `jsonl2html` installed.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library."
    )


# ToDo: move this to repotest level
# Disable frozen=True, make it inplace
@dataclass(frozen=True)
class Task:
    id: int
    repo: str
    base_commit: str
    image_name: str
    build_command: str
    test_command: str
    fn: str
    PASS_TO_PASS: str
    FAIL_TO_PASS: str
    gt: str
    intent: str
    intent_type: str
    left_context: str
    right_context: str

def doc_to_text_fg_right_context(doc: Dict[str, Any]) -> str:
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
    meta = doc.get("meta", {})
    
    left_context = meta.get("left_context", "")
    right_context = meta.get("right_context", "")
    insert_token = "        # === ТВОЙ КОД ==="
    
    combined_context = f"\n{left_context.rstrip()}\n{insert_token}\n{right_context.lstrip()}\n"
    
    prompt = doc['instruction'].format(left_context=combined_context)
    
    return prompt

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


@register_filter("extract_from_tag")
class FromTagExtractor(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(self) -> None:
        super().__init__()

    def apply(
        self, resps: List[List[str]], docs: List[Dict[str, Any]], predict_only=False
    ) -> List[List[str]]:
        if predict_only:
            return resps
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
        if text is None:
            return ""
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
        line = next(t for t in code.split("\n") if t.strip())
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
    for line in generation.split("\n"):
        if line.strip() and get_indent(line) < indent:
            break
        new_gen.append(line)
    return "\n".join(new_gen).rstrip() + "\n\n"


def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")


@register_filter("scoring")
class ScoringFilter(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(
        self,
    ) -> None:
        """
        Initializes the scoring filter with configuration for dataset, paths and logging.
        """
        super().__init__()

    def load_config(self):
        import yaml

        with open("code_tasks/realcode/realcode_config.yaml") as f:
            config = yaml.safe_load(f)

        self.working_dir = os.getenv(
            "REALCODE_WORKING_DIR",
            config["working_dir"])
        self.run_id = get_run_id()

        self.enable_full_logs = os.getenv(
            "REALCODE_ENABLE_FULL_LOGS", config["enable_full_logs"]
        )
        self.mode = os.getenv("REALCODE_SCORING_MODE", config["scoring_mode"])
        self.n_jobs = os.getenv("REALCODE_N_JOBS", config["n_jobs"])
        self.gen_columns = os.getenv(
            "REALCODE_GET_COMUNS",
            config["gen_columns"])
        self.raise_exception = os.getenv(
            "REALCODE_RAISE_EXCEPTION", config["raise_exception"]
        )
        self.n_jobs_build = os.getenv(
            "REALCODE_N_JOBS_BUILD",
            config["n_jobs_build"])

        # Verbose output folder
        print(
            "Run_id=%s output folder=%s"
            % (
                self.run_id,
                os.path.abspath(os.path.join(self.working_dir, self.run_id)),
            )
        )
        self.generations_output_filepath = os.getenv(
            "REALCODE_GENERATION_OUTPUT_FILEPATH",
            config["generations_output_filepath"])
        self.metrics_output_filepath = os.getenv(
            "REALCODE_METRICS_OUTPUT_FILEPATH",
            config["metrics_output_filepath"])
        self.html_output_filepath = os.getenv(
            "REALCODE_HTML_OUTPUT_FILEPATH", config["html_output_filepath"]
        )

    def load(self):
        if self.enable_full_logs:
            enable_stdout_logs()
        else:
            disable_stdout_logs()

        self.manager = TaskManagerRealcode(
            mode=self.mode,
            n_jobs=self.n_jobs,
            gen_columns=self.gen_columns,
            raise_exception=self.raise_exception,
            n_jobs_build=self.n_jobs_build,
        )

    def _generate_empty_string_code(self, gt: str) -> str:
        return " " * get_indent(gt) + "pass"

    def _generate_pass_code(self, gt: str) -> str:
        return " " * get_indent(gt) + 'return ""'

    def apply(
        self,
        resps: List[List[str]],
        docs: List[Dict[str, Any]],
        predict_only: bool = False,
    ) -> List[List[Dict[str, Any]]]:
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
        if predict_only:
            return resps
        self.load_config()
        self.load()
        generations = [[gen[0]] for gen in resps]
        self._save_to_file(self.generations_output_filepath, generations)
        self._save_to_file(
            os.path.join(
                self.working_dir,
                self.run_id,
                "generations.json"),
            generations)

        dataset = self._load_dataset(docs)[: len(generations)]
        processed_gens = [
            [_postprocess(gen, get_indent(task.gt)) for gen in gens]
            for task, gens in zip(dataset, generations)
        ]

        task_list = []
        for task, gen in zip(dataset, processed_gens):
            task_list.append(
                {
                    **asdict(task),
                    "gen": gen[0],
                    "gt": task.gt,
                    "return_pass": self._generate_empty_string_code(task.gt),
                    "return_empty_str": self._generate_pass_code(task.gt),
                }
            )

        self.manager.inplace_build_and_eval(task_list)

        # Save artifacts after generations
        self._save_to_file(
            os.path.join(
                self.working_dir,
                self.run_id,
                "task_list.json"),
            task_list)

        # Save html vizualization
        self.create_vizualization(task_list, self.html_output_filepath)
        self.create_vizualization(
            task_list,
            os.path.join(
                self.working_dir,
                self.run_id,
                "task_list.html"))

        return [[i] for i in task_list]

    @staticmethod
    def create_vizualization(
        task_list: List[Dict[str, Any]], fn_html_output_filepath: str
    ) -> None:
        """
        Create an HTML visualization of tasks.

        Parameters
        ----------
        task_list : list of dict
            List of task records to visualize.
        fn_html_output_filepath : str
            Output HTML file path.
        """
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=True, suffix=".jsonl"
        ) as tmpfile:
            for task in task_list:
                tmpfile.write(json.dumps(task) + "\n")
            convert_jsonl_to_html(
                fn_input=tmpfile.name,
                index_column="auto",
                fn_output=fn_html_output_filepath,
                additional_table_content={"content": "value"},
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
        return [Task(**doc["meta"]) for doc in docs]


def process_results(
    doc: Dict[str, Any], results: List[Dict[str, Any]]
) -> Dict[str, float]:
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
        "status": "execution_success",
    }

    metrics = results[0]
    res = {column_replace_dict[key]: metrics.get(
        key, 0.0) for key in column_replace_dict}

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


@register_filter("autofix")
class LMEvalAutoFixerFilter(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(
        self,
    ):
        super().__init__()

    def load_config(self):
        import yaml

        with open("code_tasks/realcode/realcode_config.yaml") as f:
            config = yaml.safe_load(f)

        self.mode = os.getenv("REALCODE_AUTOFIX_MODE", config["autofix_mode"])

    def apply(self,
              resps: list[list[str]],
              docs: list[dict],
              predict_only: bool = False) -> list[list[str]]:
        if predict_only:
            return resps
        self.load_config()
        fixed = []
        for gens, doc in zip(resps, docs):
            intent = doc["meta"]["intent"]
            gt = doc["meta"]["gt"]
            left_context = doc["meta"]["left_context"]
            if self.mode == "simple":
                fixed_gens = [fix_all(gen, intent, gt) for gen in gens]
            elif self.mode == "suffix":
                sig = extract_signature_by_intent(left_context, intent)
                fixed_gens = [
                    fix_all(
                        remove_suffix(
                            gen,
                            sig),
                        intent,
                        gt) for gen in gens]
            else:
                fixed_gens = gens
            fixed.append(fixed_gens)
        return fixed


def cut_before_signature(code: str, intent: str) -> str:
    """
    Оставляет только код после первой сигнатуры def/class intent(...):
    Всё, что выше (включая декораторы), удаляется.
    Если сигнатура не найдена — возвращает исходный код.
    """
    pattern = re.compile(
        rf"^\s*(def|class)\s+{re.escape(intent)}\b.*$",
        re.MULTILINE)
    match = pattern.search(code)
    if match:
        return code[match.end():].lstrip("\n")
    return code


def fix_indent(code: str, outputs: str) -> str:
    target_indent = get_indent(outputs)
    lines = code.splitlines()
    non_empty = [line for line in lines if line.strip()]
    if not non_empty:
        return ""
    current_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
    adjusted = []
    for line in lines:
        stripped = (line[current_indent:] if len(line)
                    >= current_indent else line.lstrip())
        adjusted.append(" " * target_indent + stripped)
    return "\n".join(adjusted)


def fix_all(code: str, intent: str, outputs: str) -> str:
    body = cut_before_signature(code, intent)
    return fix_indent(body, outputs)


def extract_signature_by_intent(
        left_context: str,
        intent_name: str) -> str | None:
    import re

    pattern = re.compile(rf"(def|class)\s+{re.escape(intent_name)}\b[\s\S]*")
    matches = pattern.findall(left_context)
    if matches:
        return matches[-1]
    return None


def remove_suffix(code: str, sig: str | None) -> str:
    if sig and code.startswith(sig):
        return code[len(sig):].lstrip("\n")
    return code
