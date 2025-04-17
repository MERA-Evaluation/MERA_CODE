import time
from tqdm import tqdm
import threading
from collections import defaultdict, Counter
import heapq
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import json
import repotest
from repotest import __version__
print("Repotest version", __version__)
from repotest.core.docker.python import PythonDockerRepo
from repotest.core.local.python import PythonLocalRepo
from repotest.core.exceptions import GitException
from task import Task
from typing import Dict, List

def extract_test(dct):
    list_of_tests = dct.get('pytest_json', {}).get('tests', {})
    passed = set()
    failed = set()
    was = set()
    for dct in list_of_tests:
        test_name = dct['nodeid']
        assert test_name not in was
        was.add(test_name)
        if dct['outcome'] == 'passed':
            passed.add(test_name)
        else:
            failed.add(test_name)
    return passed, failed

def get_passed_dict(task):
    passed, failed = extract_test(task["test_dry_run"])
    res = {}
    res['pass_dry_run'] = int(len(passed) > 0)
    for key in ['test_gt', 'test_pass', 'test_return_empty_str', "test_gen"]:
        if (key in task) or (key == "test_gen"):
            passed_current, failed_current = extract_test(task[key])
            res_column_name = f"pass_{key[len('test_'):]}"
            res[res_column_name] = int((passed_current & passed) == passed)
    return res

def change_file(fn, left_context, gt, right_context):
    #ToDo: move to repotest
    old_code = open(fn, "r").read()
    assert left_context.strip() in old_code.strip()
    assert right_context.strip() in old_code.strip()
    new_code = left_context + gt + right_context
    open(fn, "w+").write(new_code)
    return 

def change_file_and_run_test(repo, test_command, fn, gt, left_context, right_context):
    repo.clean()
    change_file(fn=fn, 
                left_context=left_context, 
                gt=gt,
                right_context=right_context
               )
    return repo.run_test(test_command)


def eval_single_task(task, debug = True):
    repo = PythonDockerRepo(repo = task['repo'],
                            base_commit = task['base_commit'],
                            image_name = task['image_name']
                           )
    # Disable this line in future
    repo.image_name = repo.default_image_name

    repo.clean()
    task['test_dry_run'] = repo.run_test(task['test_command'])
    
    repo.image_name = repo.default_image_name
    
    if debug:
        task['test_gt'] = change_file_and_run_test(repo, task['test_command'], 
                                     task['fn'], 
                                     task['gt'], task['left_context'], task['right_context'])

        task['test_pass'] = change_file_and_run_test(repo, task['test_command'], 
                                     task['fn'], 
                                     task['gen_pass'], 
                                     task['left_context'], task['right_context']
                                     )

        task['test_return_empty_str'] = change_file_and_run_test(repo, task['test_command'], 
                                     task['fn'], 
                                     task['gen_empty_string'],
                                     task['left_context'], 
                                     task['right_context']
                                    )

    task['test_gen'] = change_file_and_run_test(repo, task['test_command'], 
                                 task['fn'], 
                                 task['gen'], 
                                 task['left_context'], 
                                 task['right_context']
                                )
    
    dict_pass_res = get_passed_dict(task)
    for k, v in dict_pass_res.items():
        task[k] = v
    print("task.keys()", task.keys())

def get_parallel_index_dict(task_list: List[Task], n_parallel: int = 2) -> List[List[int]]:
    """
    Distributes tasks into groups such that each group contains unique `base_commit` values.
    The distribution aims to balance the number of tasks in each group.

    Parameters
    ----------
    task_list : List[Task]
        A list of tasks where each task must include the key `'base_commit'`.
    n_parallel : int, optional
        The number of groups to divide the tasks into, by default 2.

    Returns
    -------
    List[List[int]]
        A list of lists, where each sublist contains indices of tasks belonging to that group.
    """
    index_groups: Dict[str, List[int]] = defaultdict(list)

    for task in task_list:
        assert 'base_commit' in task

    for index, task in enumerate(task_list):
        index_groups[task['base_commit']].append(index)

    grouped_tasks = [[len(indices), base_commit, indices] for base_commit, indices in index_groups.items()]
    grouped_tasks.sort()

    parallel_index_groups: List[List[Any]] = [[0, []] for _ in range(n_parallel)]
    
    while grouped_tasks:
        n_add, base_commit, indices = grouped_tasks.pop()
        current_total, current_indices = heapq.heappop(parallel_index_groups)
        heapq.heappush(parallel_index_groups, [current_total + n_add, current_indices + indices])

    return [group[1] for group in parallel_index_groups]


def check_parallel_groups_index_valid(parallel_groups_index: List[List[int]], task_list: List[Task]) -> None:
    """
    Validates that each base_commit appears in only one group and all task indices are covered.

    Parameters
    ----------
    parallel_groups_index : List[List[int]]
        The grouped indices returned by `get_parallel_index_dict`.
    task_list : List[Task]
        The original list of tasks.

    Raises
    ------
    AssertionError
        If any base_commit appears in multiple groups or if any task index is missing.
    """
    commit_to_group: Dict[str, int] = {}
    seen_indices = set()

    for group_id, index_list in enumerate(parallel_groups_index):
        for index in index_list:
            seen_indices.add(index)
            base_commit = task_list[index]['base_commit']
            assert commit_to_group.get(base_commit, group_id) == group_id
            commit_to_group[base_commit] = group_id

    assert len(seen_indices) == len(task_list)



def get_parralel_task_list(task_list, n_parallel=2):
    task_groups_list = parallel_groups_index = get_parallel_index_dict(task_list, n_parallel=n_parallel)
    check_parallel_groups_index_valid(task_groups_list, task_list)
    return [[task_list[ind] for ind in group_ind_list] for group_ind_list in task_groups_list]


class EvaluatorRT:
    def __init__(self, 
                 n_parralel=1, 
                 mode='docker', 
                 run_id=time.time(),#ToDo: use uuid time here
                 debug = True
                ):
        assert mode in ['local', 'docker']
        if mode == 'local':
            self.REPO_CLASS = PythonLocalRepo
            raise NotImplemented("local mode not implemented yet")
        if mode == 'local':
            self.REPO_CLASS = PythonDockerRepo
            pass
        
        self.run_id = run_id
        self.mode = mode
        self.debug = debug
        self.n_parallel = n_parralel
        self.build_dict = {}
    
    def build_list(task_list):
        pass
    
    def evaluate_list(self, task_list):
        # for task in task_list:
        #     eval_single_task(task)  # in-place modification
        # return
        task_list_of_list = get_parralel_task_list(task_list=task_list,
                                                   n_parallel=self.n_parallel
                                                   )
        # eval_single_task(task_list[0])
        # Count total number of tasks for progress bar
        total_tasks = sum(len(task_group) for task_group in task_list_of_list)
        print("total_tasks=", total_tasks)
        # Thread-safe progress bar
        lock = threading.Lock()
        pbar = tqdm(total=total_tasks)

        def process_task_group(task_group):
            """
                process tasks, update pbar
            """
            for task in task_group:
                try:
                    eval_single_task(task)  # in-place modification
                    task['evaluate_fail'] = 0
                except Exception as e:
                    print("!! !!! !! "*50)
                    print("CRITICAL Fail")
                    print(e)
                    task['evaluate_fail'] = 1
                    raise e
                
                with lock:
                    pbar.update(1)

        with ThreadPoolExecutor() as executor:
            executor.map(process_task_group, task_list_of_list)

        pbar.close()



        
