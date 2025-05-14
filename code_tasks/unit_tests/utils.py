import re

from code_bleu import calc_code_bleu


def doc_to_text(doc: dict) -> str:
    """
    Функция берет данные из датасета и подставляет их в заготовленный шаблон промпта.
    """

    prompt = doc["instruction"].format(**doc["inputs"])
    return prompt.strip()


def get_code_from_markdown(text: str, language: str = "python") -> list[str]:
    """Outputs extracted code blocks from a list of strings of markdown text"""
    regex = re.compile(
        r"(?P<start>^```(?P<block_language>(\w|-)+)\n)(?P<code>.*?\n)(?P<end>```)",
        re.DOTALL | re.MULTILINE,
    )
    blocks = [
        (match.group("block_language"), match.group("code"))
        for match in regex.finditer(text)
    ]
    if len(blocks) == 0:
        # maybe an output was cutted
        regex = re.compile(
            r"(?P<start>^```(?P<block_language>(\w|-)+)\n)(?P<code>.*)",
            re.DOTALL | re.MULTILINE,
        )
        blocks = [
            (match.group("block_language"), match.group("code"))
            for match in regex.finditer(text)
        ]

    return "\n".join(
        [block for block_language, block in blocks if block_language == language]
    )


def process_results(doc: dict, results: list[str]) -> dict[str, float]:

    if doc["inputs"]["language"] == "csharp":
        lang = "c_sharp"
    if doc["inputs"]["language"] == "js":
        lang = "javascript"
    else:
        lang = doc["inputs"]["language"]

    target = doc["outputs"]
    # results - двумерный список, распаковываем его
    gen_tests = results[0]
    processed_gen_tests = [get_code_from_markdown(x) for x in gen_tests]
    hyps, refs = processed_gen_tests, [[target] for _ in processed_gen_tests]
    try:
        scores = calc_code_bleu(
            refs=refs, hyps=hyps, params=(0.25, 0.25, 0.25, 0.25), lang=lang
        )
    except:
        return {"code_bleu": 0}

    return {
        "code_bleu": scores["code_bleu_score"],
    }
