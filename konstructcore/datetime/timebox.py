"""
let you run certain codes only during certain times

Example:

    tb = Timebox(seconds)
    while tb:
        print(ps.stdout.readline(), end='')

"""
import time


class Timebox:
    """
    to be used with the `while` statement to run certain code (repeatedly) only during certain times
    """
    def __init__(self, budget_in_seconds: int):
        self.budget = budget_in_seconds
        self.start = time.perf_counter()

    def __bool__(self):
        if time.perf_counter() - self.start > self.budget:
            return False
        return True
