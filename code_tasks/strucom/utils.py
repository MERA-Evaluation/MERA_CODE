def doc_to_target(doc: dict) -> str:
    """
    Функция берет инструкцию из документа doc по ключу instruction, затем
    подставляет в нее значение из ключа inputs. У результата удаляются пробельные
    символы слева и справа.
    """
    instruction = doc["instruction"]
    prompt = instruction.format(function=doc["inputs"]["function"])
    return prompt.strip()
