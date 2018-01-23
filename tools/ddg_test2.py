#!/usr/bin/env python

import asyncio
import sys
import json

import aiohttp

DDG_API = "https://api.duckduckgo.com/"


async def async_main():
    qry = sys.argv[1] if len(sys.argv) > 1 else "testing"

    async with aiohttp.ClientSession() as session:
        params = {'q': qry, 'format': 'json'}
        async with session.get(DDG_API, params=params) as response:
            print(response)
            data = await response.json(content_type='application/x-javascript')
            print(json.dumps(data, indent=2, sort_keys=True))


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == '__main__':
    main()
