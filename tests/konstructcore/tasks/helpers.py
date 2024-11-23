"""
test helpers for the tasks package
"""
import sys


class CommandHelper:
    """
    helper functions to get platform-specific test commands
    """

    @staticmethod
    def get_echo_command() -> list[str]:
        if sys.platform == "win32":
            return ["cmd.exe", "/c", "echo", "hello"]
        return ["echo", "hello"]

    @staticmethod
    def get_echo_env_command(var_name: str) -> list[str]:
        if sys.platform == "win32":
            return ["cmd.exe", "/c", "echo", f"%{var_name}%"]
        return ["echo", f"${var_name}"]

    @staticmethod
    def get_print_current_dir_command() -> list[str]:
        if sys.platform == "win32":
            return ["cmd.exe", "/c", "echo", "%CD%"]
        return ["echo", "$PWD"]

    @staticmethod
    def get_sleep_command(seconds: float) -> list[str]:
        if sys.platform == "win32":
            return ["cmd.exe", "/c", "start", "/min", "timeout.exe", str(int(seconds))]
        return ["sleep", str(seconds)]

    @staticmethod
    def get_failing_command() -> list[str]:
        if sys.platform == "win32":
            return ["cmd.exe", "/c", "exit 1"]
        return ["false"]
