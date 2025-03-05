import re

from code_bleu import calc_code_bleu


def add_markdown(code: str, language: str | None) -> str:
    if language is None:
        return f"```\n{code.rstrip()}\n```"
    return f"```{language}\n{code.rstrip()}\n```"


def construct_user_prompt(
    user_lang: str,
    language: str,
    focal_func: str,
    focal_func_context: str | None,
    focal_file_path: str,
    test_func_type: str,
    test_func_context: str | None,
    test_file_path: str,
    prompts_dict_sampled: dict[str, str],
    test_framework: str | None = None,
) -> str:
    en2ru_test = {
        "en": {
            "function": "test function",
            "method": "test method",
            "file": "test file",
        },
        "ru": {
            "function": "тестовую функцию",
            "method": "тестовый метод",
            "file": "тестовый файл",
        },
    }

    prompt_lines = []

    language = language.lower()

    prompt_lines.append(
        prompts_dict_sampled["user_start"].format(
            language=language.capitalize(), focal_file_path=focal_file_path
        )
    )

    prompt_lines.append(add_markdown(focal_func, language=language))

    test_func_type_lang = en2ru_test[user_lang][test_func_type]
    prompt_lines.append(
        prompts_dict_sampled["user_test_instruction"].format(
            language=language.capitalize(),
            test_func_type=test_func_type_lang,
            test_file_path=test_file_path,
        )
    )
    if test_framework is not None:
        prompt_lines.append(
            prompts_dict_sampled["user_test_instruction_framework"].format(
                test_framework=test_framework
            )
        )

    if test_func_context is not None:
        prompt_lines.append(prompts_dict_sampled["user_test_context"])
        prompt_lines.append(add_markdown(test_func_context, language=None))

    if focal_func_context is not None:
        prompt_lines.append(prompts_dict_sampled["user_focal_context"])
        prompt_lines.append(add_markdown(focal_func_context, language=None))

    return "\n\n".join(prompt_lines)


def get_ru_default_chat_prompt(
    dataset_item: dict[str, str],
    max_focal_context_len: int = 30000,
    max_test_context_len: int = 10000,
) -> dict[str, str]:

    ru_prompts_dict_sampled = {
        "user_start": "Напиши тест для этого кода на языке {language} из файла '{focal_file_path}'. Напиши только тест без пояснений и комментариев.",
        "user_test_instruction": "Тебе необходимо написать {test_func_type} на языке {language}. Тест будет помещен в файл '{test_file_path}'.",
        "user_test_instruction_framework": "Используй {test_framework} тестовый фреймворк для написания тестового кода.",
        "user_test_context": "Обязательно учитывай код, собранный из будущего тестового файла: ",
        "user_focal_context": "Для тебя собран код из репозитория, который может помочь тебе в написании теста: ",
    }

    user_lang = "ru"
    language = dataset_item["language"]
    test_framework = None
    if "test_framework" in dataset_item and dataset_item["test_framework"] is not None:
        test_framework = dataset_item["test_framework"]

    focal_func_context, test_func_context = None, None

    if dataset_item["focal_func_context"] is not None:
        focal_func_context = f'#{dataset_item["focal_file_path"]}\n{dataset_item["focal_func_context"][:max_focal_context_len]}'

    if dataset_item["test_func_context"] is not None:
        test_func_context = dataset_item["test_func_context"][:max_test_context_len]

    user_prompt = construct_user_prompt(
        user_lang=user_lang,
        language=language,
        focal_func=dataset_item["focal_func"],
        focal_func_context=focal_func_context,
        focal_file_path=dataset_item["focal_file_path"],
        test_func_type=dataset_item["test_func_type"],
        test_func_context=test_func_context,
        test_file_path=dataset_item["test_file_path"],
        prompts_dict_sampled=ru_prompts_dict_sampled,
        test_framework=test_framework,
    )
    return user_prompt


def doc_to_text(doc: dict) -> str:
    """
    Функция берет данные из датасета и подставляет их в заготовленный шаблон промпта.
    """

    prompt = get_ru_default_chat_prompt(
        dataset_item=doc, max_focal_context_len=50000, max_test_context_len=20000
    )
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

    if doc["language"] == "csharp":
        lang = "c_sharp"
    if doc["language"] == "js":
        lang = "javascript"
    else:
        lang = doc["language"]

    target = doc["test_func"]
    # results - двумерный список, распаковываем его
    gen_tests = results[0]
    processed_gen_tests = [get_code_from_markdown(x) for x in gen_tests]
    hyps, refs = processed_gen_tests, [[target] for _ in processed_gen_tests]
    scores = calc_code_bleu(
        refs=refs, hyps=hyps, params=(0.25, 0.25, 0.25, 0.25), lang=lang
    )

    return {
        "code_bleu": scores["code_bleu_score"],
        "dataflow_match": scores["dataflow_match"],
        "syntax_match": scores["syntax_match"],
    }
