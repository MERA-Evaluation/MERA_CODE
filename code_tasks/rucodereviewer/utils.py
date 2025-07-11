import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict

import sacrebleu
from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

try:
    import httpx
    import litellm

    litellm._logging._disable_debugging()
    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.WARNING)

    litellm.client_session = httpx.Client(verify=False)
    litellm.aclient_session = httpx.AsyncClient(verify=False)

except ImportError:
    print(
        "WARNING! You are running task `rucodereviewer` but do not have libraries `litellm`, `httpx` installed.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library:\npip install litellm httpx"
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

n = 10


def parse_comments(response):
    comment_pattern = re.compile(
        r"Комментарий \d+:\s*(.*?)(?=Комментарий \d+:|$)", re.DOTALL
    )

    comments = comment_pattern.findall(response)

    comments = comments[:n]

    comments = [comment.strip() for comment in comments if comment.strip()]

    return comments


JUDGE_PROMPT_FIRST = """Вы - судья.
Вам будет предоставлен фрагмент изменений в коде и два комментария из кода, описывающие проблему.
Ваша задача — определить, описывают ли оба комментария одну и ту же проблему.
Если два комментария описывают одну и ту же проблему и предлагаемое решение, ответьте: correct.
Если комментарии описывают разные проблемы и решения, ответьте: wrong.
Напишите ваш ответ, correct или wrong, без кавычек и других лишних символов.\n\n"""

JUDGE_PROMPT_SECOND = """Input data:
code block difference: {diff_block}
comment 1: {comment1}
comment 2: {comment2}
answer:"""


class llmAsAJudge:

    def load_config(self):
        import yaml

        with open("code_tasks/rucodereviewer/rucodereview_config.yaml") as f:
            config = yaml.safe_load(f)

        self.max_retries = int(
            os.getenv(
                "JUDGE_MAX_RETRIES",
                config["max_retries"]))
        self.retry_delay = int(
            os.getenv(
                "JUDGE_RETRY_DELAY",
                config["retry_delay"]))
        self.model_name = os.getenv("JUDGE_MODEL_NAME", config["model_name"])
        self.temperature = float(
            os.getenv(
                "JUDGE_TEMPERATURE",
                config["temperature"]))
        self.max_tokens = int(
            os.getenv(
                "JUDGE_MAX_TOKENS",
                config["max_tokens"]))
        self.provider = os.getenv(
            "JUDGE_CUSTOM_LLM_PROVIDER",
            config["provider"])
        self.api_key = os.getenv("JUDGE_API_KEY", config["api_key"])
        self.url = os.getenv("JUDGE_URL", config["url"])
        self.few_shot_path = os.getenv(
            "JUDGE_FEW_SHOT_PATH", config["few_shot_path"])

    def load_data(self):
        if not os.path.exists(self.few_shot_path):
            err = f"File '{self.few_shot_path}' not found."
            logger.error(err)
            raise FileNotFoundError(err)

        with open(self.few_shot_path, "r") as file:
            few_shots = json.load(file)

        self.prompt_first = JUDGE_PROMPT_FIRST

        for idx, sample in enumerate(few_shots):
            self.prompt_first += f"Example {idx + 1}:\ncode block difference: {sample['diff_block']}\ncomment 1: {sample['comment1']}\ncomment 2: {sample['comment2']}\nanswer: {sample['answer']}\n\n"

        self.prompt_second = JUDGE_PROMPT_SECOND

    def post_query(self, message):
        messages = [{"role": "user", "content": message}]
        completion_params = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "base_url": self.url,
        }

        for attempt in range(self.max_retries):
            try:
                response = litellm.completion(
                    **completion_params,
                    custom_llm_provider=self.provider,
                    api_key=self.api_key,
                )
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed. Retrying in {self.retry_delay} seconds..."
                    )
                    time.sleep(self.retry_delay)
                else:
                    err = f"All {self.max_retries} attempts failed. Error: {str(e)}"
                    logger.error(err)
                    raise RuntimeError(err)

    def calculate(self, doc: Dict[str, Any], result: str) -> list[float]:
        data = {
            "diff_block": doc["inputs"]["diff_block"],
            "comment1": doc["outputs"]}

        labels = [0.0 for _ in range(n)]
        for comment_id, comment in enumerate(parse_comments(result)):
            data["comment2"] = comment

            prompt = self.prompt_first + self.prompt_second.format(**data)

            res = self.post_query(prompt)

            res = res.lower().strip()

            if res.startswith("correct") or res.endswith("correct"):
                labels[comment_id] = 1.0
            if res.startswith("wrong") or res.endswith("wrong"):
                labels[comment_id] = 0.0

        return labels


@register_filter("llmasajudgescoring")
class llmASaJudgeScoring(Filter):
    DISABLE_ON_PREDICT_ONLY = True

    def __init__(self) -> None:
        self.judge = llmAsAJudge()

    def process_sample(
        self, idx: int, sample: str, doc: Dict[str, Any]
    ) -> Dict[str, float]:
        labels = self.judge.calculate(doc, sample)
        sample_metrics = compute_classic_metrics(doc["outputs"], sample)

        for k in [1, 5, n]:
            sample_metrics[f"pass@{k}"] = float(sum(labels[:k]) > 0)

        return sample_metrics

    def apply(
        self,
        resps: list[list[str]],
        docs: list[Dict[str, Any]],
        predict_only: bool = False,
    ) -> list[Dict[str, float]]:
        if predict_only:
            return resps
        self.judge.load_config()
        self.judge.load_data()
        with ThreadPoolExecutor(os.getenv("JUDGE_MAX_WORKERS", 50)) as executor:
            tasks = [
                (idx, sample[0], doc)
                for idx, (sample, doc) in enumerate(zip(resps, docs))
            ]
            results = list(
                executor.map(
                    lambda x: self.process_sample(
                        *x), tasks))
        return results


def compute_classic_metrics(answer: str, message: str) -> Dict[str, float]:
    comments = parse_comments(message)

    result = {"bleu": [], "chrf": []}

    a = [answer]
    for comment in comments:
        b = [[comment]]
        result["bleu"].append(sacrebleu.corpus_bleu(a, b).score)
        result["chrf"].append(sacrebleu.corpus_chrf(a, b).score)

    result["bleu"] = max(result["bleu"]) if result["bleu"] else 0.0
    result["chrf"] = max(result["chrf"]) if result["chrf"] else 0.0

    return result


def doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = doc["instruction"].format(**doc["inputs"])

    return prompt


def process_results(
    doc: Dict[str, Any], results: list[Dict[str, float]]
) -> Dict[str, float]:
    return results[0]
