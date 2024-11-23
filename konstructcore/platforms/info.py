"""
provide platform (operating system + user) information
"""

import os
import platform
import socket
from typing import NamedTuple, Any

from konstructcore.datatypes.result import Result
from konstructcore.platforms.ip_address import get_host_public_ip


class PlatformInfoError(Exception):
    """Thrown when failed to get platform information."""


class PlatformInfo(NamedTuple):
    """
    Encapsulate platform information.
    
    Extra information can be added to the `ext` dictionary
    """
    hostname: str
    username: str
    os_name: str
    os_version: str
    public_ip: str
    ext: dict[str, Any]

    @classmethod
    async def create_from_env(cls) -> Result['PlatformInfo']:
        try:
            hostname = socket.gethostname()
        except Exception as err:
            return Result.err(PlatformInfoError(f'Failed to get hostname. Error ==> {err}'))
        try:
            username = os.getlogin()
        except Exception as err:
            return Result.err(PlatformInfoError(f'Failed to get username. Error ==> {err}'))
        if ip_result := await get_host_public_ip():
            pub_ip = ip_result.value
        else:
            pub_ip = 'unknown.public.ip'
        try:
            os_name = platform.system()
        except Exception as err:
            return Result.err(PlatformInfoError(f'Failed to get OS name. Error ==> {err}'))
        try:
            os_version = platform.version()
        except Exception as err:
            return Result.err(PlatformInfoError(f'Failed to get OS version. Error ==> {err}'))
        return Result.ok(cls(
            hostname=hostname,
            username=username,
            os_name=os_name,
            os_version=os_version,
            public_ip=pub_ip,
            ext=dict()
        ))

    def to_identity(self) -> str:
        """
        Return an identity string from this platform info.
        """
        return f'[{self.os_name} {self.os_version}] {self.username}@{self.hostname} : {self.public_ip}'
