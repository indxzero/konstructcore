"""
str manipulation
"""

def trim_multilines(s: str) -> str:
    """
    trimming triple-quoted str
    """
    return ''.join(_ for _ in (line.strip() for line in s.splitlines()) if _)
