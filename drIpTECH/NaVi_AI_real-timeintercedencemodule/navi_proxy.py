#!/usr/bin/env python3
"""
NaVi async proxy

Lightweight async HTTP proxy that forwards JSON requests to an upstream AI API,
logs requests/responses to SQLite, and exposes interception hooks where NaVi
can mutate prompts/responses in real-time.

This is a prototype scaffold — extend the `intercept_request` and
`intercept_response` functions to incorporate NaVi's logic and genetic
policy updates.
"""

import os
import argparse
import json
import asyncio
from aiohttp import web, ClientSession
import aiosqlite
from genetic import GeneticController

DB_PATH = os.path.join(os.path.dirname(__file__), 'navi_store.db')


async def init_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute('''CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ts DATETIME DEFAULT CURRENT_TIMESTAMP, direction TEXT, payload TEXT);''')
    await db.execute('''CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT, value TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP);''')
    await db.commit()
    return db


async def log_blob(db, direction, payload):
    await db.execute('INSERT INTO logs(direction,payload) VALUES(?,?)', (direction, json.dumps(payload)))
    await db.commit()


async def intercept_request(payload, ctx):
    """Hook to mutate/inspect outgoing request payload before forwarding.
    ctx: dict for passing ephemeral context (user prefs, profile id, etc.)
    Return modified payload (or same payload).
    """
    # Example: attach user preference token if available
    prefs = ctx.get('prefs')
    if prefs and 'style' in prefs:
        # For image APIs, we might append style tags to prompt
        if 'prompt' in payload and isinstance(payload['prompt'], str):
            payload['prompt'] = payload['prompt'] + f"\nStyle: {prefs['style']}"
    return payload


async def intercept_response(response_json, ctx):
    """Hook to inspect/modify the response before returning to client."""
    # placeholder - could apply re-ranking, filtering, or augmentation
    return response_json


async def handle(request):
    app = request.app
    db = app['db']
    upstream = app['upstream']
    api_key = app.get('api_key')

    try:
        payload = await request.json()
    except Exception:
        return web.Response(status=400, text='Invalid JSON')

    # minimal context - can be expanded to user/session-specific
    ctx = {'prefs': app.get('prefs', {})}

    await log_blob(db, 'client->proxy', payload)

    # allow NaVi to mutate request
    payload = await intercept_request(payload, ctx)

    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    headers['Content-Type'] = 'application/json'

    async with ClientSession() as sess:
        async with sess.post(upstream, json=payload, headers=headers, timeout=120) as resp:
            try:
                resp_json = await resp.json()
            except Exception:
                text = await resp.text()
                return web.Response(status=502, text='Upstream non-JSON response: ' + text[:400])

    await log_blob(db, 'upstream->proxy', resp_json)

    # allow NaVi to mutate response
    resp_json = await intercept_response(resp_json, ctx)

    return web.json_response(resp_json)


async def main(args):
    db = await init_db()
    app = web.Application()
    app['db'] = db
    app['upstream'] = args.upstream
    app['api_key'] = args.api_key
    app['prefs'] = {}  # load user prefs later

    # attach genetic controller instance (stub)
    app['genetic'] = GeneticController()

    app.router.add_post('/', handle)

    host, port = args.listen.split(':') if ':' in args.listen else (args.listen, '8080')
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, int(port))
    print(f'NaVi proxy listening on {host}:{port}, forwarding to {args.upstream}')
    await site.start()
    # run until canceled
    while True:
        await asyncio.sleep(3600)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--listen', default='127.0.0.1:8080')
    parser.add_argument('--upstream', default=os.environ.get('UPSTREAM_API_URL'))
    parser.add_argument('--api-key', default=os.environ.get('UPSTREAM_API_KEY'))
    args = parser.parse_args()
    if not args.upstream:
        print('Set UPSTREAM_API_URL via --upstream or environment variable')
        raise SystemExit(2)
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print('Shutting down NaVi')
