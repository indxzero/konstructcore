"""
A future-process task is a task using concurrent.futures.ProcessPoolExecutor.

The premise is that, the workload function must ensure it can be serialized. If it is an object, all its attributes
must be serializable. Its only method __call__ must take a dict as argument, which contains the environment table.
It is up to the workload function or object to decide whether to update its process environment table.
It must return a Result object with serializable .value attribute.

All the task-level properties are inherited from the base Task class.
"""

import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Callable

from konstructcore.datatypes.result import Result
from konstructcore.tasks.retry import RetryPolicy
from konstructcore.tasks.task import Task


class FutureProcessTask(Task):
    def __init__(
            self,
            name: str,
            workload: Callable[[dict], Result],
            env: Optional[dict] = None,
            timeout: Optional[float] = None,
            retry_policy: Optional[RetryPolicy] = None,
    ):
        self.name = name
        self.workload = workload
        self.env = env
        self.timeout = timeout
        self.retry_policy = retry_policy

    async def _run(self) -> Result:
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.workload, self.env)

    async def run(self) -> Result:
        last_result = None
        for _ in range(self.retry_policy.num_retries() if self.retry_policy else 1):
            if result := await self._run():
                return result
            else:
                last_result = result
                if self.retry_policy and self.retry_policy.should_retry():
                    await self.retry_policy.prepare_retry(self)
        return last_result
