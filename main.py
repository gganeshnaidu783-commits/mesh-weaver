"""CLI:
  python -m meshweaver node --port 9000
  python -m meshweaver node --port 9001 --seed 127.0.0.1:9000
  python -m meshweaver submit --node 127.0.0.1:9001 add '{"a": 2, "b": 3}'
  python -m meshweaver peers --node 127.0.0.1:9001
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging

from .node import Node
from .protocol import rpc


async def run_node(args) -> None:
    node = Node(args.host, args.port, seeds=args.seed,
                max_concurrency=args.concurrency)
    await node.start()
    try:
        await asyncio.Event().wait()  # run forever
    finally:
        await node.stop()


async def submit(args) -> None:
    payload = json.loads(args.payload)
    reply = await rpc(args.node, {"type": "submit", "name": args.name,
                                  "payload": payload}, timeout=args.timeout)
    print(json.dumps(reply, indent=2))


async def peers(args) -> None:
    print(json.dumps(await rpc(args.node, {"type": "peers"}), indent=2))


def main() -> None:
    p = argparse.ArgumentParser(prog="meshweaver")
    sub = p.add_subparsers(dest="cmd", required=True)

    n = sub.add_parser("node", help="run a mesh node")
    n.add_argument("--host", default="127.0.0.1")
    n.add_argument("--port", type=int, default=9000)
    n.add_argument("--seed", action="append", default=[], help="host:port of a known node")
    n.add_argument("--concurrency", type=int, default=4)

    s = sub.add_parser("submit", help="submit a task via any node")
    s.add_argument("--node", required=True)
    s.add_argument("name")
    s.add_argument("payload", nargs="?", default="null")
    s.add_argument("--timeout", type=float, default=60)

    q = sub.add_parser("peers", help="show a node's view of the mesh")
    q.add_argument("--node", required=True)

    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    handler = {"node": run_node, "submit": submit, "peers": peers}[args.cmd]
    try:
        asyncio.run(handler(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
