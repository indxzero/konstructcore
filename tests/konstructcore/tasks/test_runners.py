"""
test task runner
"""
import pytest

from konstructcore.tasks.ext_task import ExtTask
from konstructcore.tasks.runners import run_all
from tests.konstructcore.tasks.helpers import CommandHelper


@pytest.mark.asyncio
async def test_run_all_tasks_expect_concurrency():
    tasks = []
    num_tasks = 5
    for i in range(num_tasks):
        task = ExtTask(name=f"sleep task {i}",
                       command=CommandHelper.get_sleep_command(1.5))
        tasks.append(task)
    results = await run_all(tasks)
    assert len(results) == num_tasks
    for result in results:
        assert result.is_ok()
