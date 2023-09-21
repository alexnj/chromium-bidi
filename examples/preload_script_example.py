#!/usr/bin/env python3
#
# Copyright 2023 Google LLC.
# Copyright (c) Microsoft Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import itertools
import logging
from pathlib import Path

from _helpers import get_websocket, run_and_wait_command

ID = itertools.count(1000)

logging.basicConfig(
    format="%(message)s",
    level=logging.DEBUG,
)


async def main():
    # Open browser
    websocket = await get_websocket()
    await run_and_wait_command(
        {
            "id": next(ID),
            "method": "session.new",
            "params": {}
        }, websocket)

    # Add preload script
    await run_and_wait_command(
        {
            "id": next(ID),
            "method": "script.addPreloadScript",
            "params": {
                "functionDeclaration": """() => { window.foo='bar'; }""",
            }
        }, websocket)

    # Open tab
    command_result = await run_and_wait_command(
        {
            "id": next(ID),
            "method": "browsingContext.create",
            "params": {
                "type": "tab"
            }
        }, websocket)
    context_id = command_result['result']['context']

    # Navigate to page: https://news.ycombinator.com/
    # To avoid network dependency in this test, use a local (static) copy.
    page_url = f'file://{Path(__file__).parent.resolve()}/app.html'
    await run_and_wait_command(
        {
            "id": next(ID),
            "method": "browsingContext.navigate",
            "params": {
                "url": page_url,
                "context": context_id,
                "wait": "complete"
            }
        }, websocket)

    # Verify preload script is executed.
    result = await run_and_wait_command(
        {
            "id": next(ID),
            "method": "script.evaluate",
            "params": {
                "expression": "window.foo",
                "target": {
                    "context": context_id
                },
                "awaitPromise": True,
                "resultOwnership": "root",
            }
        }, websocket)
    assert result["result"]["result"] == {"type": "string", "value": "bar"}


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
result = loop.run_until_complete(main())
