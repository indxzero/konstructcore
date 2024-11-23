import asyncio

import aiohttp

from konstructcore.datatypes.result import Result


class IPAddressAPIError(Exception):
    """
    Raised when unable to retrieve public IP address from external API service. (ipify.org)
    This can happen due to network issues, API being down, or rate limiting.
    """


async def get_host_public_ip(num_retry: int = 10, delay_sec: float = 2.0, apis: list[str] = None) -> Result[str]:
    """
    Asynchronously retrieve the public IP address of the host machine.
    
    Makes requests to ipify.org API service with retries on failure.
    
    Returns:
        Tuple containing:
        - Optional[Exception]: None if successful, Exception if failed
        - str: The public IP address if successful, empty string if failed
        
    Retries up to {num_retry} times with {delay_sec} second delay between retries.
    """
    apis = apis or ['https://api.ipify.org', 'http://checkip.amazonaws.com']
    async with aiohttp.ClientSession() as session:
        error = None
        # cycle through the existing apis {num_retry} times
        for api_ in apis * num_retry:
            try:
                async with session.get(api_) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(delay_sec)
                        continue
                    text = await resp.text()
                    return Result.ok(text.strip())
            except Exception as err:
                error = err
                await asyncio.sleep(delay_sec)
                continue

    return Result.err(
        IPAddressAPIError(f'Failed to get public IP address after {num_retry} retries! Last error ==> {error}'))
