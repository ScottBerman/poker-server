# TCPServer's handle_stream event receives an IOStream object that's unique to that TCP connection, and an address tuple with the IP and port of the client. Since Tornado is asyncio, handle_stream is running in an async loop, and more than one handle_stream may be active at a time, one per connected client
# so what you can do is while True inside handel_stream, and everything in there is related to the client. The code I shared with you before looks like:

async def handle_stream(self, stream, address):
        """ Data comes in here """

        # make sure redis is connected
        await self.ensure_connect_redis()

        # dependency injection for writing to client
        async def writer(message): # it's a closure!
            return await stream.write(tornado.escape.utf8(message) + b"\0")

        # create client
        client = PlayerClient(self.redis_conn, address, writer, self.subscribe, self.unsubscribe)

        # create background task
        tick = PeriodicCallback(client.tick, 1000/TICKRATE)
        tick.start()

        # input loop
        while True:
            try:
                data = await stream.read_until(b"\0") # newlines
                await client.receive(tornado.escape.to_unicode(data).rstrip("\0"))
            except StreamClosedError:
                break

        tick.stop()
        await client.disconnect()
        del client # free up client

# from top to bottom, in my code this happens:
# 1. ensure a connection to redis. as described previously, I have an itra-process backbone based on redis, which provides horizontal scaling. This is how we can have an MMO - thousands if not tens of thousands of server instances can connect to the same backbone, spreading processing load over multiple servers, as is needed for a true MMO.
# 2. define a closure called writer that captures stream.write which sends data back to the stream
# 3. create the client object. this contains all of the client code
# 4. create a PeriodicCallback (part of tornado's ioloop library) that will run the client's "tick" function at TICKRATE (e.g. 10Hz, 20Hz, however fast you want your server's loop to run), and start that. The tick function is what's running the server-side game logic related to the player. Other things like NPCs and world updates are running in their own microservices outside this server, and communicating on the redis bus
# 5. inside a while True loop, handle all incoming data, and call the client.receive() function with that data, as well as catching the execption StreamClosedError which is what happens when the TCP stream disconnects. Note that the stream read function is an await this is what allows the function to collaboratively multitask with other instances of handle_stream if no data is being received, await stream.read_until will block this threadlet but allow other threadlets to run and handle their own data. Without await here, this class would only support one connected client at a time
# 6. upon breaking out of the while True loop, which only happens on a disconnect, stop the tick updates, call the client.disconnect() function which cleans up some data. In this case I also explicitly del client which encourages GC of client data, which otherwise would hang around for a bit longer than necessary
# The reason I don't have any handling of multiple clients here is because clients contact each other over the redis backbone. If you were to do this without redis, and have one tornado server serving multiple clients, what you'd do is pass into client your list of other clients. So:

client = PlayerClient(self.all_clients, ...)
self.all_clients.push(client)

# this way, inside PlayerClient instance, you have access to all_clients a list of all connected clients (including itself)
# alternatively, pass in not the other clients, but broadcast functions:

client = PlayerClient(self.broadcast, ...)
self.all_clients.push(client)

# where self.broadcast  is a method of this instance that inherits from TCPServer that is going to loop over all_clients and trigger relevant receive functions