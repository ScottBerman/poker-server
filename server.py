#!/usr/bin/env python

import logging
from tornado.ioloop import IOLoop
from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.options import options, define
from PlayerClient import *
import tornado

define("port", default=9888, help="TCP port to listen on")
logger = logging.getLogger(__name__)


class EchoServer(TCPServer):
    client_number = 1
    all_clients = []
    all_games = dict()

    async def handle_stream(self, stream, address):

        async def writer(message): # it's a closure!
            return await stream.write(tornado.escape.utf8(message) + b"\0")

        client = PlayerClient(address, writer, self.client_number, self.all_clients, self.all_games)
        self.all_clients.append(client)
        self.client_number += 1


        while True:
            # try:
            data = await stream.read_until(b"\0")
            logger.info("Received bytes: %s", data)
            await client.receive(tornado.escape.to_unicode(data).rstrip("\0"))

            # except StreamClosedError:
            #     logger.warning("Lost client at host %s", address[0])
            #     break
            # except Exception as e:
            #     print(e)


if __name__ == "__main__":
    options.parse_command_line()
    server = EchoServer()
    server.listen(options.port)
    logger.info("Listening on TCP port %d", options.port)
    IOLoop.current().start()