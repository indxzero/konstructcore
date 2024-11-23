"""
The concept of retry is an important part of a task system because all the async/IO tasks can fail.

A retry policy describes how a task and its subtasks should be retried.
"""

import asyncio
from typing import Callable

from konstructcore.tasks.task import Task


class RetryPolicy:

    def should_retry(self) -> bool:
        raise NotImplementedError()

    async def prepare_retry(self, task: Task):
        raise NotImplementedError()

    def num_retries(self) -> int:
        raise NotImplementedError()

    def num_failures(self) -> int:
        raise NotImplementedError()


class RetryWithConstantSleep(RetryPolicy):

    def __init__(self, sleep_sec: float, retries: int, cb: Callable[[Task, int], None]=None):
        self.sleep_sec = sleep_sec
        self.retries = retries
        self.failures = 0
        self.callback = cb

    def should_retry(self) -> bool:
        return True

    async def prepare_retry(self, task: Task):
        self.failures += 1
        if self.callback is not None:
            self.callback(task, self.failures)
        await asyncio.sleep(self.sleep_sec)

    def num_retries(self) -> int:
        return self.retries

    def num_failures(self) -> int:
        return self.failures

    def __str__(self):
        return f'RetryWithConstantSleep(sleep_sec={self.sleep_sec}, retries={self.retries})'


class ExponentialBackoffRetry(RetryPolicy):

    def __init__(self, base_sleep_sec: float, exp: float, max_retries: int, cb: Callable[[Task, int], None]=None):
        """
        exp is expected to be greater than 1, such as 1.5, 1.75

        suppose base sleep sec is 1
        for 1.5 the first retry will sleep 1.5 * 1 = 1.5 seconds, then 2.25, 3.375, 5.0625, ...
        for 1.75 the first retry will sleep 1.74 * 1 = 1.74 seconds, then 3.0625 5.359375 9.37890625, ...
        for 2.0 the first retry will sleep 2.0 * 1 = 2.0 seconds, then 4.0, 8.0, 16.0, ...
        """
        self.base_sleep_sec = base_sleep_sec
        self.exp = exp
        self.max_retries = max_retries
        self.failures = 0
        self.callback = cb

    def should_retry(self) -> bool:
        return True

    async def prepare_retry(self, task: Task):
        ratio = self.exp ** self.failures
        self.failures += 1
        if self.callback is not None:
            self.callback(task, self.failures)
        await asyncio.sleep(self.base_sleep_sec * ratio)

    def num_retries(self) -> int:
        return self.max_retries

    def num_failures(self) -> int:
        return self.failures

    def __str__(self):
        return f'ExponentialBackoffRetry(base_sleep_sec={self.base_sleep_sec}, exp={self.exp}, retries={self.max_retries})'
