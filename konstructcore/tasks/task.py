"""
the abstract Task type
"""
from typing import Callable

from konstructcore.datatypes.result import Result


class Task:
    async def run(self) -> Result:
        raise NotImplementedError()

    async def run_with(self, f: Callable) -> Result:
        raise NotImplementedError()

    def format(self) -> str:
        raise NotImplementedError()


class TaskFailure(Exception):
    """
    Describe how a task failed.

    It provides:

    - Failure type
    - The return code of the external task

    """

    Fail_Unspecified = 'Unspecified'
    Fail_Time_Out = 'TimeOut'
    Fail_Exception = 'Exception'
    Fail_With_Stderr = 'WithStderr'
    Cannot_Process_Output = 'CannotProcessOutput'

    def __init__(self, *args):
        super().__init__(*args)
        self.failure_type = TaskFailure.Fail_Unspecified

    @staticmethod
    def unwrap_failure_type(err) -> str:
        if isinstance(err, TaskFailure):
            return err.failure_type
        return ''

    @classmethod
    def from_task(cls, task: 'Task', is_timeout: bool) -> 'TaskFailure':
        if not is_timeout:
            return cls(f'External Task fails to run.\n{task.format()}')
        ins = cls(f'External task times out.\n{task.format()}')
        ins.failure_type = TaskFailure.Fail_Time_Out
        return ins

    @classmethod
    def from_task_and_error(cls, task: 'Task', error: Exception) -> 'TaskFailure':
        ins = cls(f'External Task fails to run.\n{task.format()}\nError ==> {error}')
        ins.failure_type = TaskFailure.Fail_Exception
        return ins

    @classmethod
    def from_task_and_stderr(cls, task: 'Task', stderr: str) -> 'TaskFailure':
        ins = cls(f'External Task fails to run.\n{task.format()}\nError Message ==> {stderr}')
        ins.failure_type = TaskFailure.Fail_With_Stderr
        return ins

    @classmethod
    def cannot_process_output(cls, task: 'Task', error: Exception) -> 'TaskFailure':
        ins = cls(f'Cannot process output of external task.\n{task.format()}\nError ==> {error}')
        ins.failure_type = TaskFailure.Cannot_Process_Output
        return ins
