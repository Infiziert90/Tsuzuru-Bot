#!/usr/bin/env python

import asyncio
import sys

import duckduckgo

DDG_API = "https://api.duckduckgo.com/"


async def async_main():
    qry = sys.argv[1] if len(sys.argv) > 1 else "testing"

    answer = await duckduckgo.query(qry, safesearch=False, meanings=False)
    print(answer.type)
    print(answer.results)
    # print(json.dumps(answer.json, indent=2))
    # result = await duckduckgo.zci(qry, safesearch=False, meanings=False)
    # print(result)
    if answer.heading:
        print(f"Heading: {answer.heading}")

    if answer.redirect.url:
        print(f"Redirected to: {answer.redirect.url}")
    if answer.answer.text:
        print(f"Answer ({answer.answer.type}): {answer.answer.text}")
    if answer.abstract.text:
        print(f"Abstract: {answer.abstract.text} ({answer.abstract.url}; {answer.abstract.source})")
    if answer.results:
        result = answer.results[0]
        print(f"Result: {result.text} ({result.url})")  # result.icon
    if answer.related:
        result = answer.related[0]
        print(f"Related: {result.text} ({result.url})")  # result.icon
    if answer.definition.text:
        print(f"Definition: {answer.definition.text} ({answer.definition.url}; {answer.definition.url})")

    if answer.image.url:
        print(f"Image: {answer.image.url}")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == '__main__':
    main()
