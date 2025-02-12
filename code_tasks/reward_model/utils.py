import datasets


INSTRUCTION = ("Даны два кода: фокальный и тест. Определи, скомпилируется ли тест. "
               "Верни 0, если не скомпилируется, и 1, если скомпилируется.\n{inputs}")


def doc_to_text(doc: dict) -> str:
    focal = doc['focal']
    test = doc['test']
    inputs = f'{focal}\n{test}'
    prompt = INSTRUCTION.format(inputs=inputs)

    return prompt.strip()

