import argparse
import glob
import hashlib
import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

import datasets
import numpy as np
from tqdm.auto import tqdm

from lm_eval.loggers.evaluation_tracker import GeneralConfigTracker
from lm_eval.utils import load_yaml_config, sanitize_model_name


CUSTOM_TASK_PATH = "./code_tasks/config.yaml"
BENCHMARK_STORAGE: Optional[str] = load_yaml_config(CUSTOM_TASK_PATH).get(
    "dataset_path"
)
_TASKS = {}
DATASETS_TO_TRUNCATION = []
INPUT_DATE_FORMAT = "%Y-%m-%dT%H-%M-%S.%f"
SAMPLES_SUFFIX = "samples_"
RESULTS_SUFFIX = "results_"
INDEX_TO_GET = 0

TASKS_WITH_RAW_RESPS = [
    "realcode", "realcodejava", "realcodedebug", 
    "javatestgen", "rucodereviewer", "yabloco", 
    "codelintereval"
]


def get_files_from_dir(dir_path):
    f = []
    for _, _, filenames in os.walk(dir_path):
        for fn in filenames:
            fn = os.path.join(dir_path, fn)
            f.extend([fn])
    return f


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(obj, file, ensure_ascii=False, indent=4)


def load_json(path):
    with open(path, encoding="utf-8") as file:
        text = json.loads(file.read().strip())
    return text


def load_jsonl(path):
    with open(path, encoding="utf-8") as file:
        result = [json.loads(line) for line in file.readlines()]
    return result


def save_jsonl(file, path):
    with open(path, "w", encoding="utf-8") as outfile:
        for entry in file:
            json.dump(entry, outfile, ensure_ascii=False)
            outfile.write("\n")


def extract_date(file_name: str) -> datetime:
    extract_str_date = file_name.split(".json")[0].split("_")[-1]
    date = datetime.strptime(extract_str_date, INPUT_DATE_FORMAT)
    return date


def register_task(cls):
    _TASKS[cls.__name__] = cls
    return cls


class BaseTask:
    @property
    def src_name(self):
        return self.__class__.__name__.lower()

    @property
    def dst_name(self):
        return self.__class__.__name__
    
    @property
    def key(self):
        if self._key is None:
            if self.src_name in TASKS_WITH_RAW_RESPS:
                self._key = "resps"
            else:
                self._key = "filtered_resps"
        return self._key
    
    @property
    def take_first(self):
        if self._take_first is None:
            if self.src_name in TASKS_WITH_RAW_RESPS:
                self._take_first = True
            else:
                self._take_first = False
        return self._take_first

    @property
    def outputs_path(self):
        filelist = glob.glob(
            os.path.join(self.outputs_dir, f"samples_{self.src_name}*.json*")
        )
        if not filelist:
            # raise error if filelist is empty
            raise FileNotFoundError(
                "No samples to pack found, or there is an error in path processed"
            )
        # sorting filelist to get the latest
        filelist = sorted(filelist, key=extract_date, reverse=True)
        res = filelist[INDEX_TO_GET]
        return res

    @property
    def submission_path(self):
        return os.path.join(self.dst_dir, f"{self.dst_name}.json")

    @staticmethod
    def doc_to_meta(doc):
        return doc["meta"]

    def doc_to_id(self, doc):
        return self.doc_to_meta(doc)["id"]

    def load(self):
        path = self.dataset_path or os.path.join(BENCHMARK_STORAGE, self.dst_name)
        dataset = datasets.load_dataset(path=path)[
            "test"
        ]
        examples = {}
        for example in dataset:
            doct_id = self.doc_to_id(example)
            examples[doct_id] = example
        return examples

    def __init__(
        self, outputs_dir, dst_dir, dataset_path: Optional[str] = None
    ):
        self.outputs_dir = outputs_dir
        self.dst_dir = dst_dir
        self.dataset_path = dataset_path
        self.dataset = self.load()
        self._key = None
        self._take_first = None


class TextTask(BaseTask):
    def convert(self):
        submission = None
        try:
            submission = self.outputs_to_submission(load_jsonl(self.outputs_path))
            save_json(submission, self.submission_path)
        except FileNotFoundError:
            print(
                "No samples to pack found, or there is an error in path processed. Src:",
                self.src_name,
            )
        return submission

    def outputs_to_submission(self, outputs):
        res = []
        for doc in outputs:
            doc_id = int(self.doc_to_id(doc["doc"]))
            resp = doc[self.key]
            res.extend([self.doc_outputs_to_submission(doc_id, resp)])
        return {"data": {"test": res}}

    @staticmethod
    def parse_doc(doc):
        return doc[0]
    
    def doc_outputs_to_submission(self, doc_id, outputs):
        res = {
            "outputs": outputs[0][0] if self.take_first else outputs[0],
            "meta": {"id": doc_id},
        }
        return res
    

class MultiOutputTask(TextTask):
    def doc_outputs_to_submission(self, doc_id, outputs):
        res = {
            "outputs": outputs,
            "meta": {
                "id": doc_id,
            },
        }
        return res

@register_task
class ruHumanEval(MultiOutputTask):
    pass

@register_task
class ruCodeEval(MultiOutputTask):
    pass

@register_task
class CodeLinterEval(MultiOutputTask):
    pass

@register_task
class ruCodeReviewer(TextTask):
    pass

@register_task
class JavaTestGen(TextTask):
    pass

@register_task
class RealCode(TextTask):
    pass

@register_task
class RealCodeJava(TextTask):
    pass

@register_task
class YABLoCo(TextTask):
    pass
    
@register_task
class stRuCom(TextTask):
    pass

@register_task
class UnitTests(TextTask):
    pass

@register_task
class CodeCorrectness(TextTask):
    pass


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs_dir", type=str, help="lm-evaluation-harness outputs")
    parser.add_argument(
        "--dst_dir",
        type=str,
        default="submission/",
        help="dir to save files for submission",
    )
    parser.add_argument(
        "--model_args",
        type=str,
        default="",
        help="Comma separated string arguments for model, e.g. `pretrained=EleutherAI/pythia-160m,dtype=float32`",
    )
    res = parser.parse_known_args()[0]
    return res


def pack_submission_logs(outputs_dir: str, dst_dir: str):
    if os.path.isdir(outputs_dir):
        zip_dir = os.path.join(dst_dir, "logs_public")
        os.makedirs(zip_dir, exist_ok=True)
        files_to_pack = glob.glob(os.path.join(outputs_dir, "*.json*"))
        for file_path in files_to_pack:
            file_name = os.path.split(file_path)[-1].lower()
            if file_name.startswith((SAMPLES_SUFFIX, RESULTS_SUFFIX)):
                # copy with possible truncation of outputs
                copy_and_truncate(file_path, zip_dir)
            else:
                print("Unknown file {fn}".format(fn=file_path))
        zip_path = shutil.make_archive(zip_dir, "zip", zip_dir)
        shutil.rmtree(zip_dir)
        print("Logs to add with public submission stored at", zip_path)
    else:
        raise ValueError(f"{outputs_dir} is not directory")


def create_submission(outputs_dir, dst_dir):
    os.makedirs(dst_dir, exist_ok=True)
    for task_name, task_cls in tqdm(_TASKS.items(), total=len(_TASKS)):
        print("Process task", task_name)
        task = task_cls(outputs_dir=outputs_dir, dst_dir=dst_dir)
        _ = task.convert()
        print("---------------------")
    print("Packing logs for public submission...")
    pack_submission_logs(outputs_dir, dst_dir)
    zip_path = shutil.make_archive(dst_dir, "zip", dst_dir)
    print("Submission stored at", zip_path)
    return zip_path


def preprocess_outputs_dir(outputs_dir: str, model_args: str) -> str:
    """
    User either provides "full" path to dir with jsons or provides path to
    folder of upper level and model_args to define subdir with jsons.
    If user explicitly provides model_args, parse it and use to define subdir.
    Otherwise, return the initial outputs_dir with no changes.
    """
    if model_args:
        # get model_name cleared of "pretrained=" and everything after first comma
        model_name = GeneralConfigTracker._get_model_name(model_args)
        # use func to find the name of subdir from model_name
        subdirectory = sanitize_model_name(model_name)
        # join paths
        full_path = os.path.join(outputs_dir, subdirectory)
        return full_path
    return outputs_dir


def truncate_outputs(path):
    """
    Function that takes `path` to file, reads it and substitute all 'arg_0' values
    of each item 'arguments' keys with their sha256 codes.
    """
    if path.endswith("json"):
        data = load_json(path)
    elif path.endswith("jsonl"):
        data = load_jsonl(path)
    else:
        raise ValueError("Undefined format of {directory} file".format(directory=path))
    for line in data:
        for key in line["arguments"]:
            if isinstance(line["arguments"][key]["arg_0"], str):
                line["arguments"][key]["arg_0"] = hashlib.sha256(
                    line["arguments"][key]["arg_0"].encode()
                ).hexdigest()
            else:
                line["arguments"][key]["arg_0"] = hashlib.sha256(
                    line["arguments"][key]["arg_0"][0].encode()
                ).hexdigest()
    return data


def copy_and_truncate(file_path, zip_dir):
    """
    For datasets in DATASETS_TO_TRUNCATION truncates the outputs in logs while copying
    the file into zip_dir. For other files just make copy.
    """
    for file in DATASETS_TO_TRUNCATION:
        if file in os.path.split(file_path)[-1]:
            data = truncate_outputs(file_path)
            name = os.path.split(file_path)[-1]
            save_jsonl(data, os.path.join(zip_dir, name))
            return
    shutil.copy2(file_path, zip_dir)
    return


def main():
    args = get_args()
    outputs_dir = preprocess_outputs_dir(args.outputs_dir, args.model_args)
    create_submission(outputs_dir, args.dst_dir)


if __name__ == "__main__":
    main()
