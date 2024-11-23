"""
External task is an abstraction of subprocess and async io.

User defines how to execute an external program and how to handle its I/O.
The rest is managed by the task object.
There are two outcomes
- the task succeeded
- failed or timed out

User can specify a retry policy (backoff, constant sleep time, etc.) to handle failures.
"""
import asyncio
from typing import Optional, NamedTuple, Callable

from konstructcore.datatypes.result import Result
from konstructcore.tasks.retry import RetryPolicy
from konstructcore.tasks.task import Task, TaskFailure


class ExtTaskOutput(NamedTuple):
    """
    Encapsulates the output of an external task.

    Stdout
    Stderr
    Return code
    """

    stdout: str
    stderr: str
    return_code: int


class ExtTaskFailure(TaskFailure):

    def __init__(self, *args):
        super().__init__(*args)
        self.return_code = None

    def with_return_code(self, return_code: int) -> 'ExtTaskFailure':
        self.return_code = return_code
        return self


class ExtTask(Task):
    """
    ExtTask is an immutable object describing how to execute an external task.

    It provides two methods to execute the task:

    - Method run(): to run the task till timeout, termination or completion.
        Return either ExtTaskOutput or ExtTaskFailure
    - Method run_with(): to run the task till timeout, termination or completion.
        If the task succeeds, apply a function f to ExtTaskOutput and return another ExtTaskOutput
        If f fails, return ExtTaskFailure with type CannotProcessOutput
    """

    def __init__(
            self,
            name: str,
            command: list[str],
            cwd: Optional[str] = None,
            env: Optional[dict] = None,
            timeout: Optional[float] = None,
            retry_policy: Optional[RetryPolicy] = None,
            collect_output: bool = True,
    ):
        self.name = name
        self.command = command
        self.cwd = cwd
        self.env = env
        self.timeout = timeout
        self.retry_policy = retry_policy
        self.collect_output = collect_output

    def command_string(self) -> str:
        """
        Return the command string with arguments separated by space. The entire string is wrapped in a pair of
        triple-backticks
        """
        s = ' '.join(self.command)
        return f'```{s}```'

    def format(self) -> str:
        """
        Return a nicely formatted representation of the task
        """
        return f"""Task [{self.name}] (
    cwd={self.cwd},
    env={self.env},
    timeout={self.timeout},
    retry={self.retry_policy}
    
    {self.command_string()}
)"""

    async def _run(self, collect_output: bool = True, retry_policy: Optional[RetryPolicy] = None) -> Result:
        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                *self.command,
                cwd=self.cwd,
                env=self.env,
                stdout=asyncio.subprocess.PIPE if collect_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if collect_output else asyncio.subprocess.DEVNULL,
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)
            except asyncio.TimeoutError:
                process.kill()

                # If a timeout occurs, it kills the subprocess and waits for the pipes to close properly to
                # avoid ungraceful exceptions.
                await process.communicate()
                return Result.err(ExtTaskFailure.from_task(self, True).with_return_code(process.returncode))

            if process.returncode != 0:
                stderr_str = self._safe_decode(stderr) if stderr else ""
                return Result.err(
                    ExtTaskFailure.from_task_and_stderr(self, stderr_str).with_return_code(process.returncode))

            if collect_output:
                stdout_str = self._safe_decode(stdout) if (collect_output and stdout) else ""
                stderr_str = self._safe_decode(stderr) if (collect_output and stderr) else ""
                return Result.ok(ExtTaskOutput(stdout_str, stderr_str, process.returncode))
            else:
                return Result.ok(None)

        except Exception as e:
            ret = process.returncode if process is not None else -1
            return Result.err(ExtTaskFailure.from_task_and_error(self, e).with_return_code(ret))

    @staticmethod
    def _safe_decode(byte_string: bytes) -> str:
        """
        Safely decode byte string, replacing invalid characters.
        Read:
        https://docs.python.org/3/library/exceptions.html#UnicodeDecodeError
        https://docs.python.org/3/library/codecs.html#codec-base-classes
        """
        return byte_string.decode('utf-8', errors='replace')

    async def run(self) -> Result:
        """
        Run will execute the external program with the given command, env, cwd and timeout.

        If the program executes successfully, wrap its output in Result.ok();
        or if not collect output, return Result.ok(None)

        If the program fails or times out, return one of:
        Result.err(ExtTaskFailure.from_task(task))
        Result.err(ExtTaskFailure.from_task_and_error(task, error))
        Result.err(ExtTaskFailure.from_task_and_stderr(task, stderr))
        """
        last_result = None
        for _ in range(self.retry_policy.num_retries() if self.retry_policy else 1):
            if result := await self._run(collect_output=self.collect_output, retry_policy=self.retry_policy):
                return result
            else:
                last_result = result
                if self.retry_policy and self.retry_policy.should_retry():
                    await self.retry_policy.prepare_retry(self)
        return last_result

    async def run_with(self, f: Callable[[ExtTaskOutput], ExtTaskOutput] = None) -> Result:
        """
        Similar to run, but apply a function to the output of the external program.
        If no function is given, it will discard the output of the external program, effectively similar to calling
        self.run(collect_output=False)

        Note, the failure of f is NOT retryable and if throws an exception will be caught and propagated immediately.
        Function f is supposed to be pure: f: ExtTaskOutput -> ExtTaskOutput.
        """
        last_result = None
        for _ in range(self.retry_policy.num_retries() if self.retry_policy else 1):
            if result := await self._run(collect_output=f is not None, retry_policy=self.retry_policy):
                if f is not None:
                    try:
                        return Result.ok(f(result.value))
                    except Exception as err:
                        return Result.err(
                            ExtTaskFailure.cannot_process_output(self, err).with_return_code(result.value.return_code))
                return result
            else:
                last_result = result
                if self.retry_policy and self.retry_policy.should_retry():
                    await self.retry_policy.prepare_retry(self)
        return last_result
