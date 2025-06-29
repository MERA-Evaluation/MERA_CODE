import json
import os
import re
import tempfile
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

from repotest import __version__ as repotest_version
from repotest.constants import disable_stdout_logs, enable_stdout_logs
from repotest.manager.realcode_java_task_manager import JavaEvaluatorRealcode

min_repotest_version = "0.4.4"
if not (repotest_version >= min_repotest_version):
    raise ImportError("Current repotest version is {} it should be {}".format(
        repotest_version, min_repotest_version
    ))


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
    # В промтах упоминаются фигурные скобки { },
    # из-за чего str.format падает
    instruction = doc["instruction"]
    for field, value in doc["inputs"].items():
        instruction = instruction.replace('{'+field+'}', value)
    return instruction


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
        if text is None:
            return ""
        tag_start = "```java"
        tag_end = "```"
        index_start = text.find(tag_start)

        if index_start == -1:
            index_end = text.find(tag_end, 0)
        else:
            index_end = text.find(tag_end, index_start + len(tag_start))

        if index_end != -1:
            text = text[:index_end]
        if index_start != -1:
            text = text[index_start + len(tag_start):]
        return text
    

def cut_c_style_func_body(prediction: str, left_ctx: Optional[str] = None):
    """
    Trims generation based on number of open|closed curly braces.

    Parameters
    ----------
    prediction : str
        Generated code.
    left_ctx : Optional[str]
        Code before generated part.

    Returns
    -------
    str
        Postprocessed code string.
    """

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

    # TODO: Тут еще обработки комментариев и одиночных символов в коде
    # не хватает. Где-то есть более полная версия.
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
    # Ну не получилось..
    return prediction


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
        # processed_gens = [
        #     [cut_c_style_func_body(gen, task.left_context) for gen in gens]
        #     for task, gens in zip(dataset, generations)
        # ]

        task_list = []
        for task, gens in zip(dataset, generations):
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
    metrics = results[0]
    res = {
        "pass@1": metrics.get("pass_gen", 0),
        "pass_oracle@1": metrics.get("pass_gt", 0),
        "pass_stub_pass@1": metrics.get("pass_stub", 0),
        "pass_dry_run@1": metrics.get("pass_dry_run", 0),
        "execution_success": metrics.get("status", 0),
        "num_samples": 1,
    }
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


@register_filter("javafix")
class JavaLMEvalAngel(Filter):
    def apply(self, resps: list[list[str]], docs: list[dict]) -> list[list[str]]:
        fixed = []
        for gens, doc in zip(resps, docs):
            intent = doc["meta"]["intent"]
            gt = doc["meta"]["gt"]
            left_context = doc["meta"]["left_context"]
            fixed_gens = []
            for gen in gens:
                gen = remove_signature(gen, left_context, intent)
                gen = fix_missing_closing_brace(gen, gt)
                gen = cut_c_style_func_body_v2(gen, c=1)
                fixed_gens.append(gen)
            fixed.append(fixed_gens)
        return fixed
    

def find_code_block_braces(snippet: str) -> List[Tuple[str, int]]:
    code_braces = []
    is_char = False
    inside_string = False
    inside_short_comment = False
    inside_multi_line_comment = False
    for i, char in enumerate(snippet):
        two_chars = snippet[max(0,i-1):i+1]
        if char == '"' and two_chars != r'\"':
            inside_string = not inside_string
        if (char == "'" and
            two_chars != r"\'" and
            not inside_string and
            not inside_short_comment and
            not inside_multi_line_comment):
            is_char = not is_char

        if two_chars == '//':
            inside_short_comment = True
        elif two_chars == '/*':
            inside_multi_line_comment = True
        elif two_chars == '*/':
            inside_multi_line_comment = False
        if char == '\n':
            inside_short_comment = False
        
        if (is_char or
            inside_string or
            inside_short_comment or 
            inside_multi_line_comment):
            # На такие случаи лучше убедиться, что is_char выключится точно
            # ", email='" + email + '\'' +
            # is_char = False
            continue
        if char in '{}':
            code_braces.append((char, i))
    return code_braces
    

def count_open_curly_braces(snippet: str) -> int:
    c = 0
    for char, pos in find_code_block_braces(snippet):
        if char == '{':
            c += 1
        elif char == '}':
            c -= 1
    return c


def fix_missing_closing_brace(generation: str, gt: str):
    """
    Дорисует скобку }, если функция не закрыта
    """
    if generation.rstrip().endswith('}'):
        c = count_open_curly_braces(generation)
        # Левый контекст содержит сигнатуру с открытой скобкой
        # поэтому должно быть -1 и меньше
        if c < 0:
            return generation

    # ищем в конце пустую строчку с }
    endings = re.findall(r'(?<=\n)[\t ]*}[\n\t ]*?$', gt)
    if len(endings) > 0:
        if not generation.endswith('\n'):
            generation = generation + '\n'
        return generation + endings[0]
    return generation


def find_signature(code: str, intent: str) -> str:
    """
    Найдет первую сигнатуру
    """
    open_brace = re.escape('{')
    signature_pattern = re.compile(rf"\s+{re.escape(intent)}\b.*{open_brace}[\n\t ]*?$", re.MULTILINE)
    match = signature_pattern.search(code)
    if match:
        return match.group(0)
    return None


def find_signature_last(code: str, intent: str) -> str:
    """
    Найдет последнюю сигнатуру.
    В Java может быть несколько функций с одним названием.
    
    """
    open_brace = re.escape('{')
    signature_pattern = re.compile(rf"\s+{re.escape(intent)}\b.*{open_brace}[\n\t ]*?$", re.MULTILINE)
    matches = signature_pattern.findall(code)
    if len(matches) > 0:
        return matches[-1]
    return None


def remove_signature(code: str, left_context: str, intent: str) -> str:
    """
    Если код начинается с сигнатуры, как в левом контексте,
    удалим ее.
    """
    intent = intent.split('[')[0]
    # Берем последние строчки левого контекста
    lc_end = '\n'.join( left_context.splitlines()[-20:] )
    # И ищем там сигнатуру ближе к самому концу
    signature = find_signature_last(lc_end, intent)
    if signature is None:
        return code
    return code.split(signature)[-1]


def cut_c_style_func_body_v2(snippet: str, c: Optional[int] = 0):
    for char, pos in find_code_block_braces(snippet):
        if char == '{':
            c += 1
        if char == '}':
            c -= 1
            if c == 0 and pos >= 5:
                return snippet[:pos+1]
    # Ну не получилось..
    return snippet
