"""
provide more advanced features for running the tasks
"""
import asyncio
from typing import Optional

import more_itertools

from konstructcore.datatypes.result import Result
from konstructcore.tasks.task import Task, TaskFailure


async def run_all(tasks: list[Task]) -> list[Result]:
    """
    Run all the tasks to completion or failure.
    Collect their results in a list following the order of the tasks.
    """
    return await asyncio.gather(*[t.run() for t in tasks])


async def repeat(task: Task, count: Optional[int] = None) -> Result:
    """
    Repeatedly execute a task until:
    - It reaches the specified number of times (if provided)
    - It runs into a failure as Result.err
    - It runs into an exception, which is caught and returned as Result.err
    """
    if count is None:
        it = more_itertools.repeat_last(range(1), 0)
    else:
        it = range(count)
    try:
        for _ in it:
            if (result := await task.run()).is_err():
                return result
    except Exception as err:
        return Result.err(TaskFailure.from_task_and_error(task, err))
