import os

import pytest

from konstructcore.tasks.ext_task import ExtTask, ExtTaskOutput
from konstructcore.tasks.retry import RetryWithConstantSleep, ExponentialBackoffRetry
from konstructcore.tasks.task import TaskFailure
from tests.konstructcore.tasks.helpers import CommandHelper


@pytest.mark.asyncio
async def test_basic_echo():
    task = ExtTask(name="echo test", command=CommandHelper.get_echo_command())
    result = await task.run()
    assert result.is_ok()
    ext_task_output: ExtTaskOutput = result.value
    assert "hello" in ext_task_output.stdout
    assert ext_task_output.stderr == ""
    assert ext_task_output.return_code == 0


@pytest.mark.asyncio
async def test_with_cwd():
    user_dir = os.path.expanduser("~")
    task = ExtTask(name="echo with cwd",
                   command=CommandHelper.get_print_current_dir_command(),
                   cwd=user_dir)
    result = await task.run()
    assert result.is_ok()
    ext_task_output: ExtTaskOutput = result.value
    assert user_dir in ext_task_output.stdout
    assert ext_task_output.return_code == 0


@pytest.mark.asyncio
async def test_with_env():
    task = ExtTask(name="echo with env",
                   command=CommandHelper.get_echo_env_command('TEST_VAR'),
                   env={"TEST_VAR": "test_value"})
    result = await task.run()
    assert result.is_ok()


@pytest.mark.asyncio
async def test_timeout():
    task = ExtTask(name="sleep task",
                   command=CommandHelper.get_sleep_command(2),
                   timeout=0.2)
    result = await task.run()
    assert result.is_err()
    assert TaskFailure.unwrap_failure_type(result.error) == TaskFailure.Fail_Time_Out

    # timeout is long enough for the task to finish
    task = ExtTask(name="sleep task",
                   command=CommandHelper.get_sleep_command(2),
                   timeout=4)
    result = await task.run()
    print(result)
    assert result.is_ok()



@pytest.mark.asyncio
async def test_failing_command():
    task = ExtTask(name="failing command", command=CommandHelper.get_failing_command())
    result = await task.run()
    assert result.is_err()
    assert isinstance(result.error, TaskFailure)


@pytest.mark.asyncio
async def test_constant_retry():
    task = ExtTask(name="failing with retry",
                   command=CommandHelper.get_failing_command(),
                   retry_policy=RetryWithConstantSleep(sleep_sec=0.1,
                                                       retries=3))
    result = await task.run()
    assert result.is_err()
    assert isinstance(result.error, TaskFailure)
    assert task.retry_policy.num_failures() == 3


@pytest.mark.asyncio
async def test_exponential_retry():
    task = ExtTask(name="failing with exp retry",
                   command=CommandHelper.get_failing_command(),
                   retry_policy=ExponentialBackoffRetry(base_sleep_sec=0.1,
                                                        exp=2.0,
                                                        max_retries=3))
    result = await task.run()
    assert result.is_err()
    assert isinstance(result.error, TaskFailure)
    assert task.retry_policy.num_failures() == 3


@pytest.mark.asyncio
async def test_run_without_output():
    task = ExtTask(name="echo no output", command=CommandHelper.get_echo_command(), collect_output=False)
    result = await task.run()
    assert result.is_ok()
    assert result.value is None


@pytest.mark.asyncio
async def test_format_and_command_string():
    task = ExtTask(name="format test",
                   command=["test", "command"],
                   cwd="/tmp",
                   env={"TEST": "VALUE"},
                   timeout=10)
    cmd_str = task.command_string()
    assert "```test command```" == cmd_str

    fmt_str = task.format()
    assert "Task [format test]" in fmt_str
    assert "cwd=/tmp" in fmt_str
    assert "TEST" in fmt_str
    assert "timeout=10" in fmt_str

@pytest.mark.asyncio
async def test_task_with_output_applier():
    """
    To apply f to the task output
    """

    task = ExtTask(name="echo test", command=CommandHelper.get_echo_command())

    def f(out: ExtTaskOutput) -> ExtTaskOutput:
        return ExtTaskOutput(
            stdout=f"MODIFIED {out.stdout}",
            stderr=out.stderr,
            return_code=out.return_code
        )

    result = await task.run_with(f)
    assert result.is_ok()
    ext_task_output: ExtTaskOutput = result.value
    assert "MODIFIED hello" in ext_task_output.stdout
    assert ext_task_output.stderr == ""
    assert ext_task_output.return_code == 0

@pytest.mark.asyncio
async def test_task_without_output_applier_failure():
    """
    To apply f to the task output but it throws an exception
    """
    task = ExtTask(name="echo test", command=CommandHelper.get_echo_command())

    def f(out: ExtTaskOutput) -> ExtTaskOutput:
        if out.return_code == 0:
            raise ValueError()
        return ExtTaskOutput(
            stdout=f"MODIFIED {out.stdout}",
            stderr=out.stderr,
            return_code=out.return_code
        )

    result = await task.run_with(f)
    assert result.is_err()
    assert TaskFailure.unwrap_failure_type(result.error) == TaskFailure.Cannot_Process_Output
