#!/usr/bin/env python

from tornado.ioloop import IOLoop
from tornado import gen
from tornado.tcpclient import TCPClient
from tornado.options import options, define

import json 
import time

define("host", default="localhost", help="TCP server host")
define("port", default=9888, help="TCP port to connect to")
define("message", default="ping", help="Message to send")


async def send_message():
    stream = await TCPClient().connect(options.host, options.port)

    message = { "params": [ 1,2 ], "method": "get_game_info", "id": "2081135912", "jsonrpc": "2.0" }
    await stream.write((json.dumps(message) + "\0").encode())
    print("Sent to server:", message)
    reply = await stream.read_until(b"\0")
    print("Response from server:", reply.decode().strip())
    
    message2 = { "params": [1], "method": "join_game", "id": "2081135912", "jsonrpc": "2.0" }
    await stream.write((json.dumps(message2) + "\0").encode())
    print("Sent to server:", message2)
    reply2 = await stream.read_until(b"\0")
    print("Response from server:", reply2.decode().strip())
    time.sleep(5)
if __name__ == "__main__":
    options.parse_command_line()
    IOLoop.current().run_sync(send_message)