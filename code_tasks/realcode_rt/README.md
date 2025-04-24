TBD list (MERA_CODE.realcode_rt):

https://gitlab.ai.cloud.ru/rnd-core-team/plp/MERA_CODE/-/merge_requests/1#note_81485


1. move this MERA_CODE.realcode_rt.pipy.py:Task class to repotest. Rename it to more specific one like RealCodeTask.
2. make it possible to calculate @k easily
3. lmeh_realcode_rt create debug=True functionality
4. Complete refactor of manager functionality at RepoTest

is there a good example of something simmilar implementation?
SWE bench
https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/run_evaluation.py#L337
https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/utils.py#L79

I don't like this approach even more, because debug information is completely lost and saved only in .log file. Good that never use dict as input for function, this is really bad practise.

I thing good approach is
dataclass for Task    (fixed env/image)
dataclass for Problem (fixed env/image + diff)
dataclass has a field language
for different language it instantiate different class PythonDockerRepo, PythonLocalRepo, ...,
JavaDockerRepo, ...
Task is singleton object that also have a method success_build with logic over there
I need more good referece

5. jsonl2html have simple way to run from python
6. jsonl2html could work from json as input