import os

import pytest

from konstructcore.datatypes.result import Result


class Worker:
    def __call__(self, env_: dict) -> Result:
        if env_.get('SPECIAL_VALUE') == '1':
            return Result.ok('1')
        elif env_.get('SPECIAL_VALUE') == '2':
            return Result.err(ValueError('2'))
        return Result.err(ValueError('missing SPECIAL_VALUE env var'))


@pytest.mark.asyncio
async def test_pass_env_to_future_process_task():
    from konstructcore.tasks.mp_task import FutureProcessTask
    env_ = os.environ.copy()
    env_['SPECIAL_VALUE'] = '1'
    task = FutureProcessTask(
        'pass env var',
        workload=Worker(),
        env=env_
    )
    result = await task.run()
    assert result.is_ok()
    assert result.value == '1'


@pytest.mark.asyncio
async def test_future_process_task_return_error():
    from konstructcore.tasks.mp_task import FutureProcessTask
    env_ = os.environ.copy()
    env_['SPECIAL_VALUE'] = '2'
    task = FutureProcessTask(
        'pass env var',
        workload=Worker(),
        env=env_
    )
    result = await task.run()
    assert result.is_err()
    assert isinstance(result.error, ValueError)
