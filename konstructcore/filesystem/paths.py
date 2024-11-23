"""
cross-platform filesystem operations
"""

import os


def join_paths(*args):
    """
    Joins the given paths into a single path.
    Format the resulting path using the POSIX separator.
    """
    p_ = os.path.abspath(os.path.sep.join(args))
    return p_.replace(os.path.sep, '/')
