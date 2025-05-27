# The codelinter_eval dataset

Для запуска необходимо установить дополнительные пакеты:

pip install flake8 flake8-json

После установки пакетов необходимо установить переменную среды окружения LINTER_PATH с указанием пути до flake8.

Путь до flake8 можно проверить командой where flake8.

## Description

Бенчмарк для оценки генерации корректного кода на основе некорректного кода и списка ошибок/предупреждений от линтера.
Датасет был создан на основе датасета mbpp путем проверки референсных примеров линтером flake8 и ручным исправлением этих ошибок/предупреждений в коде для получения канонического решения.

Пример структуры :
{
    "inputs": {
        "code": "def first_repeated_char(str1):\n  for index,c in enumerate(str1):\n    if str1[:index+1].count(c) > 1:\n      return c",
        "feedback": "E111: indentation is not a multiple of 4 in 2 line\nE231: missing whitespace after ',' in 2 line\nE111: indentation is not a multiple of 4 in 4 line\nW292: no newline at end of file in 4 line\n"
    },
    "instruction": "Перепиши код с учетом ошибок полученных от линтера. \nКод: {code} \nОшибки от линтера:{feedback}",
    "meta": {
        "canonical_code": "\ndef find_repeated_character(string):\n    seen = set()\n    for char in string:\n        if char in seen:\n            return char\n        seen.add(char)\n    return None\n",
        "id": 0
    },
    "outputs": [
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1
    ]
}

Описание полей:
- instruction — строка, содержащая формулировку запроса к языковой модели;
- inputs - словарь, содержащий входные данные задания;
- code — строка, содержащая код на Python, содержащий ошибки;
- feedback — строка, содержащая описание ошибок от линтера;
- outputs — одномерный массив строк размера n_samples, где n_samples - количество сэмплов, требуемое для подсчета метрики pass@k.
- meta — cловарь, содержащий метаинформацию:
- canonical_code — каноническое решение задачи (код без ошибок/предупреждений линтера);
- id - идентификатор задания;


## Homepage

https://mera.a-ai.ru

## License

MIT License
