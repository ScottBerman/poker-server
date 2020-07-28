import json
import uuid
from jsonrpc import JsonRpc

from Game import Game
import tornado
# @method
# async def get_game_info(game_id):
    # print("Method get_game_info() called successfully no params: ", game_id)

class PlayerClient:
    def __init__(self, address, writer, client_number, all_clients, all_games):
        self.id = uuid.uuid4()
        self.address = address
        self.writer = writer
        self.all_clients = all_clients
        self.chips = None
        self.client_number = client_number
        self.game_id = None
        self.player_id = None
        self.game = None
        self.all_games = all_games
        self.seat = None
        
        self.rpc = JsonRpc({
            "get_game_info": self.rpc_get_game_info,
            "join_game": self.rpc_join_game
        })
    
    # write own encoder https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    def serialize(self):
        player_json = {
            "id" : str(self.id),
            "chips": self.chips,
            "seat": self.seat
        }
        return player_json
    
    async def receive(self, data):
        print("Client number: ", self.client_number)
        json_data = json.loads(data)
        rpc_response = await self.rpc.handle(json_data)
        await self.writer(json.dumps(rpc_response))

    
    async def rpc_join_game(self, *args):
        print("SEAT: ", args[0])
        position = int(args[0])
        
        # Check if seat is available (ADD LOCK IN FUTURE)
        if self.game.seat_arr[position]:
            return False
        
        # Set new player information
        self.chips = self.game.starting_chips
        self.seat= position # Setting the player's seat
        new_player_info = self.serialize()

        # Remove player from lobby (ADD LOCK TO THIS IN FUTURE)
        self.game.lobby.remove(self)

        # Broadcast new player to everyone in the game and everyone in the game lobby.
        for player in self.game.players:
            await player.new_player_joined(new_player_info)
        for player in self.game.lobby:
            await player.new_player_joined(new_player_info)
        
        # Join game
        self.game.players.append(self) # Player joining the game
        self.game.seat_arr[position] = True

        # Return information back to caller.
        join_successful = True # Update to be able to be false.
        join_game_response = dict()
        join_game_response["player_info"] = new_player_info
        join_game_response["join_successful"] = True
        return join_game_response

    async def new_player_joined(self, new_player):
        rpc_method = "new_player_joined"
        params = new_player
        rpc_id = str(uuid.uuid4())
        # SEND TO PLAYERS IN GAME LOBBY AS WELL
        await self.writer(json.dumps(JsonRpc.build_request(rpc_id, rpc_method, params)))

    # @method
    # This is called when a player clicks on an existing game.
    async def rpc_get_game_info(self, *args):
        # Get args
        game_id = args[0]
        player_id = args[1]
        self.game_id = game_id
        self.player_id = player_id
        
        # Get game
        game = self.all_games.get(game_id)
        if not game:
            game = Game(game_id)
            self.all_games[game_id] = game
            self.game.admin = self # change later
        self.game = game

        # Add self to game's lobby
        self.game.lobby.append(self)

        # Get game info
        game_info = dict()
        game_info["players"] = []
        for player in game.players:
            game_info["players"].append(player.serialize())
        game_info["self"] = self.serialize()
        return game_info
        # In the future this should be removed because creating a game will be a separate route.  This function will only be invoked when a person clicks on an existing game.