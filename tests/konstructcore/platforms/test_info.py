from konstructcore.platforms import info

import pytest


@pytest.mark.asyncio
async def test_get_platform_info():
    result = await info.PlatformInfo.create_from_env()
    print(result)
    assert result.is_ok()
