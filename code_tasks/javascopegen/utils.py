import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

try:
    from repotest import __version__ as repotest_version
    from repotest.constants import disable_stdout_logs, enable_stdout_logs
    from repotest.manager.realcode_java_task_manager import \
        JavaEvaluatorRealcode

    min_repotest_version = "0.4.4"
    if not (repotest_version >= min_repotest_version):
        raise ImportError(
            "Current repotest version is {} it should be {}".format(
                repotest_version, min_repotest_version
            )
        )
except ImportError:
    print(
        "WARNING! You are running task `realcode` but do not have library `repotest` installed or its version is less than 0.4.4.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library."
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
    file_path: str
    PASS_TO_PASS: str
    FAIL_TO_PASS: str
    gt: str
    stub: str
    intent: str
    intent_type: str
    left_context: str
    right_context: str
    scope: str


def doc_to_text_qwen_fim(doc: dict) -> str:
    fim_template = '<|fim_prefix|>{left_context}<|fim_suffix|>{right_context}<|fim_middle|>'
    instruction = fim_template.format(**doc["inputs"])
    return instruction


def get_run_id():
    return datetime.now().strftime("%Y%m%dT%H%M%S")


@register_filter("scoring_java_sg")
class ScoringFilterRCJava(Filter):
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

        with open("code_tasks/javascopegen/javasg_scoring_config.yaml") as f:
            config = yaml.safe_load(f)

        self.working_dir = os.getenv(
            "JAVA_SG_WORKING_DIR",
            config["working_dir"])
        self.run_id = get_run_id()

        self.enable_full_logs = os.getenv(
            "JAVA_SG_ENABLE_FULL_LOGS", config["enable_full_logs"]
        )
        self.mode = os.getenv(
            "JAVA_SG_SCORING_MODE",
            config["scoring_mode"])
        self.n_jobs = os.getenv("JAVA_SG_N_JOBS", config["n_jobs"])
        self.gen_columns = os.getenv(
            "JAVA_SG_GEN_COLUMNS",
            config["gen_columns"])
        self.raise_exception = os.getenv(
            "JAVA_SG_RAISE_EXCEPTION", config["raise_exception"]
        )
        self.n_jobs_build = os.getenv(
            "JAVA_SG_N_JOBS_BUILD", config["n_jobs_build"]
        )

        # Verbose output folder
        print(
            "Run_id=%s output folder=%s"
            % (
                self.run_id,
                os.path.abspath(os.path.join(self.working_dir, self.run_id)),
            )
        )
        self.generations_output_filepath = os.getenv(
            "JAVA_SG_GENERATION_OUTPUT_FILEPATH",
            config["generations_output_filepath"],
        )
        self.metrics_output_filepath = os.getenv(
            "JAVA_SG_METRICS_OUTPUT_FILEPATH",
            config["metrics_output_filepath"])
        self.html_output_filepath = os.getenv(
            "JAVA_SG_HTML_OUTPUT_FILEPATH", config["html_output_filepath"]
        )

    def load(self):
        if self.enable_full_logs:
            enable_stdout_logs()
        else:
            disable_stdout_logs()

        self.pipeline = JavaEvaluatorRealcode(
            mode=self.mode,
            n_jobs=self.n_jobs,
            gen_columns=self.gen_columns,
            raise_exception=self.raise_exception,
            n_jobs_build=self.n_jobs_build,
        )

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
        # processed_gens = [
        #     [cut_c_style_func_body(gen, task.left_context) for gen in gens]
        #     for task, gens in zip(dataset, generations)
        # ]

        task_list = []
        for task, gens in zip(dataset, generations):
            task_list.append(
                {
                    **asdict(task),
                    "gen": gens[0],
                    "gt": task.gt,
                    "stub": task.stub,
                }
            )
        self.pipeline.inplace_build_and_eval(task_list)

        # Save artifacts after generations
        self._save_to_file(
            os.path.join(
                self.working_dir,
                self.run_id,
                "task_list.json"),
            task_list)

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
        return [Task(**doc["meta"]) for doc in docs]


def process_results_java_sg(
    doc: Dict[str, Any], 
    results: List[Dict[str, Any]]
) -> Dict[str, float]:
    """
    Extract and summarize metrics from task results.

    Parameters
    ----------
    doc : dict
        Original input document.
    results : list of dict
        Evaluation output for a single task.

    Returns
    -------
    dict
        Dictionary with key metrics.
    """
    scope = doc["meta"].get("scope")
    metrics = results[0]
    res = {
        "pass@1": metrics.get("pass_gen", 0),
        "pass_oracle@1": metrics.get("pass_gt", 0),
        "pass_stub_pass@1": metrics.get("pass_stub", 0),
        "pass_dry_run@1": metrics.get("pass_dry_run", 0),
        "execution_success": metrics.get("status", 0),
        "num_samples": 1,
    }
    if scope is not None:
        add = dict()
        for k, v in res.items():
            key = f"{scope}__{k}"
            add[key] = v
        res.update(add)
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


@register_filter("postproc_java_scope_gens")
class JavaScopeGenProcessor(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def apply(self,
              resps: list[list[str]],
              docs: list[dict],
              predict_only: bool = False) -> list[list[str]]:
        if predict_only:
            return resps
        fixed = []
        for gens in resps:
            fixed_gens = []
            for gen in gens:
                gen = self.cut_func_body(gen, c=0)
                fixed_gens.append(gen)
            fixed.append(fixed_gens)
        return fixed
    
    @staticmethod
    def cut_func_body(snippet: str, c: Optional[int] = 0) -> str:
        """
        Parameters
        ----------
        snippet (str) : generated code snippet
        c       (int) : initial number of open curly braces


        Returns
        -------
        (str) : truncated code
        """
        braces = JavaScopeGenProcessor.find_code_block_braces(snippet)
        for char, pos in braces:
            if char == "{":
                c += 1
            if char == "}":
                c -= 1
                if c == 0 and pos >= 5:
                    return snippet[: pos + 1]
        # Ну не получилось..
        return snippet

    @staticmethod
    def find_code_block_braces(snippet: str) -> List[Tuple[str, int]]:
        code_braces = []
        is_char = False
        inside_string = False
        inside_short_comment = False
        inside_multi_line_comment = False
        for i, char in enumerate(snippet):
            two_chars = snippet[max(0, i - 1): i + 1]
            if char == '"' and two_chars != r"\"":
                inside_string = not inside_string
            if (
                char == "'"
                and two_chars != r"\'"
                and not inside_string
                and not inside_short_comment
                and not inside_multi_line_comment
            ):
                is_char = not is_char

            if two_chars == "//":
                inside_short_comment = True
            elif two_chars == "/*":
                inside_multi_line_comment = True
            elif two_chars == "*/":
                inside_multi_line_comment = False
            if char == "\n":
                inside_short_comment = False

            if (
                is_char
                or inside_string
                or inside_short_comment
                or inside_multi_line_comment
            ):
                # На такие случаи лучше убедиться, что is_char выключится точно
                # ", email='" + email + '\'' +
                # is_char = False
                continue
            if char in "{}":
                code_braces.append((char, i))
        return code_braces
