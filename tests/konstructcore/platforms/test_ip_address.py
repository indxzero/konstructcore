import unittest

import pytest

from konstructcore.platforms.ip_address import get_host_public_ip


@pytest.fixture
def do_setup():
    data = dict(foo='bar')
    return len(data)


@pytest.mark.asyncio
async def test_get_ip_address(do_setup):
    assert do_setup == 1
    result = await get_host_public_ip()
    print(result)
    assert result.is_ok()
