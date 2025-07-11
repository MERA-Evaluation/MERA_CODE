import re

try:
    from code_bleu import calc_code_bleu
except ImportError:
    print(
        "WARNING! You are running task `unittests` or `unittestspublic` but do not have library `code_bleu` installed.\nIf you are running the evaluation with `--predict_only` flag, ignore this warning. Otherwise consider installing the required library from the repository:\nhttps://github.com/Pstva/code_bleu"
    )


def doc_to_text(doc: dict) -> str:
    """
    Функция берет данные из датасета и подставляет их в заготовленный шаблон промпта.
    """

    prompt = doc["instruction"].format(**doc["inputs"])
    return prompt.strip()


def get_code_from_markdown(text: str, language: str = "python") -> list[str]:
    """
    Достает код из маркдаун-блока.
    Гарантируется корректная работа при следующих трех ситуациях:
    1. Сгенерирован один или несколько полных md-блоков с указанием верного языка.
        Пример для python:

        ```python
        def lala():
            return 1
        ```

        Вывод:

        def lala():
            return 1

    Таких блоков может быть несколько, они все спарсятся и соединятся.

    2. Сгенерирован один md-блок с указанием верного языка, но конец блока недогенерировался.
        Пример для python:

        ```python
        def lala():
            return 1

        Вывод:

        def lala():
            return 1


    3. Сгенерирован полный md-блок, но язык вообще не указан.

        Пример для python:

        ```
        def lala():
            return 1
        ```

        Вывод:

        def lala():
            return 1

    Для всех остальных ситуаций ничего не гарантируется и,
    если ничего не удалось спарсить, то в ответе выдается оригинальный текст.
    Например, если сгенерирован блок с другим языком, он вернется таким же.
    """
    regex = re.compile(
        r"```(?P<block_language>(\w|-)+)\n(?P<code>.*?)```",
        re.DOTALL | re.MULTILINE,
    )
    blocks = [
        (match.group("block_language"), match.group("code"))
        for match in regex.finditer(text)
    ]

    # if an output was cutted
    if len(blocks) == 0:
        regex = re.compile(
            r"```(?P<block_language>(\w|-)+)\n(?P<code>.*)",
            re.DOTALL | re.MULTILINE,
        )
        blocks = [
            (match.group("block_language"), match.group("code"))
            for match in regex.finditer(text)
        ]

    # if there is no language in the output
    if len(blocks) == 0:
        regex = re.compile(
            r"```\n(?P<code>.*?)```",
            re.DOTALL | re.MULTILINE,
        )
        blocks = [(language, match.group("code"))
                  for match in regex.finditer(text)]

    blocks = [
        block for block_language,
        block in blocks if block_language == language]
    parsed_text_from_md = "\n".join(blocks)

    # if no code was found, return the original text
    if len(blocks) == 0 or len(parsed_text_from_md.strip()) == 0:
        return text

    return parsed_text_from_md.strip("\n")


def process_results(doc: dict, results: list[str]) -> dict[str, float]:

    # results - двумерный список, распаковываем его
    gen_tests = results[0]
    processed_gen_tests = [
        get_code_from_markdown(x, doc["inputs"]["language"]) for x in gen_tests
    ]

    if doc["inputs"]["language"] == "csharp":
        lang = "c_sharp"
    elif doc["inputs"]["language"] == "js":
        lang = "javascript"
    else:
        lang = doc["inputs"]["language"]

    target = doc["outputs"]
    hyps, refs = processed_gen_tests, [[target] for _ in processed_gen_tests]
    try:
        scores = calc_code_bleu(
            refs=refs, hyps=hyps, params=(0.25, 0.25, 0.25, 0.25), lang=lang
        )
    except BaseException:
        return {"code_bleu": 0}

    return {
        "code_bleu": scores["code_bleu_score"],
    }
