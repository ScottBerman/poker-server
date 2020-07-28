class Game:
    def __init__(self, id):
        self.id = id
        self.seat_count = 8
        self.seat_arr = [False]*self.seat_count
        self.starting_chips = 20000
        self.players = []
        self.lobby = []
        