from typing import Any, Dict


def _doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = doc["instruction"].format(**doc["inputs"])

    return prompt


def doc_to_text(doc: Dict[str, Any]) -> str:
    prompt = _doc_to_text(doc)

    return prompt
