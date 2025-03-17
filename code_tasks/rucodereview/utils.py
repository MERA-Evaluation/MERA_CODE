from typing import Any, Dict

from lm_eval.api.filter import Filter
from lm_eval.api.registry import register_filter

import json, re, logging

import litellm, httpx
import sacrebleu


litellm._logging._disable_debugging()
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

litellm.client_session = httpx.Client(verify=False)
litellm.aclient_session = httpx.AsyncClient(verify=False)

n = 10


def post_query(message):
    try:
        url = "model_url"

        messages = [{"role": "user", "content": message}]
        completion_params = {
            "model": "qwen-coder-32b",
            "messages": messages,
            "stream": False,
            "temperature": 0.,
            "max_tokens": 100,
            "base_url": url,
        }

        response = litellm.completion(
            **completion_params,
            custom_llm_provider="openai",
            api_key='None',
        )

        return response.json()['choices'][0]['message']['content']
    except:
        print('ERROR')
        return "ERROR"


def parse_comments(response):
    comment_pattern = re.compile(r'Комментарий \d+:\s*(.*?)(?=Комментарий \d+:|$)', re.DOTALL)

    comments = comment_pattern.findall(response)

    comments = comments[:n]

    comments = [comment.strip() for comment in comments if comment.strip()]

    return comments


class llmAsAJudge():
    def __init__(self, few_shot_path: str = "/workdir/MERA_CODE/code_tasks/few_shot.json") -> None:

        with open(few_shot_path, 'r') as file:
            few_shots = json.load(file)

        self.prompt_first = f"""Вы - судья.
Вам будет предоставлен фрагмент изменений в коде и два комментария из кода, описывающие проблему.
Ваша задача — определить, описывают ли оба комментария одну и ту же проблему.
Если два комментария описывают одну и ту же проблему и предлагаемое решение, ответьте: correct.
Если комментарии описывают разные проблемы и решения, ответьте: wrong.
Напишите ваш ответ, correct или wrong, без кавычек и других лишних символов.\n\n"""

        for idx, sample in enumerate(few_shots):
            self.prompt_first += f"Example {idx + 1}:\ncode block difference: {sample['diff_block']}\ncomment 1: {sample['comment1']}\ncomment 2: {sample['comment2']}\nanswer: {sample['answer']}\n\n"

        self.prompt_second = """Input data:
        code block difference: {diff_block}
        comment 1: {comment1}
        comment 2: {comment2}
        answer:"""

    def calculate(self, doc: Dict, result: str) -> list[float]:
        data = {'diff_block': doc['inputs']['diff_block'], 'comment1': doc['outputs']}

        labels = [0. for _ in range(n)]
        for comment_id, comment in enumerate(parse_comments(result)):
            data['comment2'] = comment

            prompt = self.prompt_first + self.prompt_second.format(**data)

            res = post_query(prompt)

            res = res.lower().strip()

            if res.startswith('correct') or res.endswith('correct'):
                labels[comment_id] = 1.
            if res.startswith('wrong') or res.endswith('wrong'):
                labels[comment_id] = 0.

        return labels


def compute_classic_metrics(answer, message):
    comments = parse_comments(message)

    result = {'bleu': [], 'chrf': []}

    a = [answer]
    for comment in comments:
        b = [[comment]]
        result['bleu'].append(sacrebleu.corpus_bleu(a, b).score)
        result['chrf'].append(sacrebleu.corpus_chrf(a, b).score)

    result['bleu'] = max(result['bleu']) if result['bleu'] else 0.
    result['chrf'] = max(result['chrf']) if result['chrf'] else 0.

    return result


def _doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = doc["instruction"].format(**doc["inputs"])

    return prompt


def doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = _doc_to_text(doc)

    return prompt


def process_results(doc: Dict, results: list[str]) -> Dict[str, float]:
    judge = llmAsAJudge()

    labels = judge.calculate(doc, results[0])

    result = compute_classic_metrics(doc['outputs'], results[0])

    for k in [1, 5, 10]:
        result[f"pass@{k}"] = sum(labels[:k]) > 0

    return result