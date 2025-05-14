from typing import List, Dict, Any
import sys
import logging
import os
import json
from repotest.core.docker.java import JavaDockerRepo
from repotest.utils.git.git_diff_wrapper import GitDiffWrapper
from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

sys.path.append("code_tasks/java_testgen/")
from logger import setup_logger


setup_logger()
logger = logging.getLogger("java_testgen_bench")


def doc_to_text_java_testgen(doc: Dict[str, Any]) -> str:
    return doc["instruction"].format(**doc["inputs"])


def process_results_java_testgen(doc: Dict, results: List[Dict]) -> Dict[str, float]:
    metrics = results[0]['evaluation']
    return {
        "success_rate": float(metrics["parser"]["success"]),
        "compilation_rate": float(metrics["parser"]["compiled"]),
    }


def evaluate(repo: str,
             base_commit: str,
             image_name: str,
             test_command: str,
             fn_test: str,
             source_code: str,
             code: str,
             timeout: int = 300) -> Dict[str, Any]:
    """
    Evaluates generated Java code in a Dockerized test environment.

    Parameters
    ----------
    repo : str
        Repository path.
    base_commit : str
        Base commit hash.
    image_name : str
        Name of the Docker image.
    test_command : str
        command to run tests.
    fn_test : str
        Test file name.
    source_code : str
        Source code path.
    code : str
        The generated Java code.
    timeout : int, optional
        Maximum test execution time in seconds, by default 300.

    Returns
    -------
    Dict[str, Any]
        Result dictionary containing test execution details.
    """
    repo_instance = JavaDockerRepo(repo=repo, base_commit=base_commit, 
                                   image_name=image_name, cache_mode='volume')
    repo_instance.clean()

    git_diff_wrapper = GitDiffWrapper(repo=repo_instance, 
                                      base_commit=base_commit)
    git_diff_wrapper.change_test(fn_test=fn_test, str_test=code, 
                                 str_source=source_code)
    git_diff_wrapper.fix_pom_file()
    git_diff = git_diff_wrapper.git_diff()
    repo_instance.clean()

    logger.info("len(git_diff)=%s"%len(git_diff))

    repo_instance.apply_patch(git_diff + '\n')
    result = repo_instance.run_test(test_command, timeout=timeout)

    logger.info("Attempt1: %s"%str(result)[:100])

    if not result.get("parser", {}).get("success", False):
        logger.info("Fail")
    else:
        logger.info("Success")
    return result


@register_filter("extract_from_tag_java")
class ExtractFromTagJava(Filter):
    def apply(self, resps, docs):
        return [[self._extract_java(gen) for gen in generations] for generations in resps]

    @staticmethod
    def _extract_java(text):
        if '```java' in text:
            text = text.split('```java')[1]
        if '```' in text:
            text = text.split('```')[0]
        return text.strip()


@register_filter("scoring_java_testgen")
class ScoringJavaTestgen(Filter):
    def __init__(
        self,
        working_dir,
        generations_output_filepath,
        metrics_output_filepath,
    ) -> None:
        super().__init__()
        self.working_dir = working_dir
        self.generations_output_filepath = generations_output_filepath
        self.metrics_output_filepath = metrics_output_filepath
        os.makedirs(self.working_dir, exist_ok=True)

    def apply(self, resps, docs):
        generations = [[gen[0]] for gen in resps]
        self._save_to_file(self.generations_output_filepath, generations)

        results = []
        for doc, gen in zip(docs, generations):
            code = gen[0]
            result = self._evaluate(doc, code)
            results.append(result)

        self._save_to_file(self.metrics_output_filepath, results)
        return [[{"evaluation": res}] for res in results]

    def _evaluate(self, doc, code):
        meta = doc['meta']
        if code.strip():
            result = evaluate(
                repo=meta['repo'],
                base_commit=meta['base_commit'],
                image_name=meta['image_name'],
                fn_test=meta['fn_test'],
                test_command=meta['test_command'],
                source_code=meta['source_code'],
                code=code
            )
        else:
            result = {
                "stdout": "",
                "stderr": "empty code",
                "std": "empty code",
                "returncode": -2,
                "parser": {'success': False, 'compiled': False},
                "time": 0.01
            }
        return result

    @staticmethod
    def _save_to_file(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        def convert_bytes(obj):
            if isinstance(obj, bytes):
                return obj.decode("utf-8", errors="ignore")
            if isinstance(obj, dict):
                return {k: convert_bytes(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [convert_bytes(i) for i in obj]
            return obj

        with open(filepath, "w") as file:
            json.dump(convert_bytes(data), file, indent=4)
