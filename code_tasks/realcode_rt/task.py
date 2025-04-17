from dataclasses import dataclass

@dataclass(frozen=True)
class Task:
    repo: str
    base_commit: str
    test_command: str
    build_command: str
    image_name: str
    left_context: str
    gt: str
    right_context: str
    fn: str
    PASS_TO_PASS: str
    FAIL_TO_PASS: str
    _more_params: str


    def _to_dict(self):
        return {k: getattr(self, k) for k in self.__dir__() if k[0] != '_'}

