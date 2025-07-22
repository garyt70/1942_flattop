import random
from flattop.hex_board_game_model import Hex, TurnManager  # Import Hex for use in weather model

class WindDirection:
    def __init__(self, sector, direction=1):
        self.sector = sector  # 1-8
        self.direction = direction  # 1-6 (hex direction, see Flat Top rules)

    def change_direction(self, new_direction):
        self.direction = new_direction

    def __repr__(self):
        return f"WindDirection(sector={self.sector}, direction={self.direction})"

class CloudMarker:
    def __init__(self, hex_pos, sector, cloud_type="scattered"):
        self.hex_pos = hex_pos  # Hex object
        self.sector = sector    # 1-8
        self.cloud_type = cloud_type  # "scattered" or "front"

    def move(self, direction, board):
        # Move one hex in the given direction (1-6)
        direction_vectors = {
            1: Hex(1, 0),    # E
            2: Hex(1, -1),   # NE
            3: Hex(0, -1),   # NW
            4: Hex(-1, 0),   # W
            5: Hex(-1, 1),   # SW
            6: Hex(0, 1),    # SE
        }
        vec = direction_vectors.get(direction, Hex(1, 0))
        new_hex = Hex(self.hex_pos.q + vec.q, self.hex_pos.r + vec.r)
        if board.is_valid_tile(new_hex):
            self.hex_pos = new_hex

    def __repr__(self):
        return f"CloudMarker(hex={self.hex_pos}, sector={self.sector}, type={self.cloud_type})"

class WeatherManager:
    def __init__(self, board, scenario_cloud_type="scattered"):
        self.board = board
        self.wind_directions = [WindDirection(sector=i+1, direction=1) for i in range(8)]
        self.cloud_markers = []
        self.scenario_cloud_type = scenario_cloud_type
        self.init_clouds()

    def init_clouds(self):
        if self.scenario_cloud_type == "scattered":
            for sector in range(1, 9):
                center_hex = self.get_directional_hex(sector)
                for _ in range(4):
                    cloud = CloudMarker(center_hex, sector, "scattered")
                    die = random.randint(1, 6)
                    for _ in range(die):
                        cloud.move(die, self.board)
                    self.cloud_markers.append(cloud)
        elif self.scenario_cloud_type == "front":
            for sector in range(1, 9):
                center_hex = self.get_directional_hex(sector)
                cloud_center = CloudMarker(center_hex, sector, "front")
                cloud_ne = CloudMarker(self.move_hex(center_hex, 2, 5), sector, "front")
                cloud_sw = CloudMarker(self.move_hex(center_hex, 5, 5), sector, "front")
                self.cloud_markers.extend([cloud_center, cloud_ne, cloud_sw])
                die = random.randint(1, 6)
                for cloud in [cloud_center, cloud_ne, cloud_sw]:
                    for _ in range(die):
                        cloud.move(die, self.board)

    def get_directional_hex(self, sector):
        # These should match your board's directional hexes
        sector_centers = [
            Hex(9, 11), Hex(29, 11), Hex(49, 11), Hex(69, 11),
            Hex(9, 33), Hex(29, 33), Hex(49, 33), Hex(69, 33)
        ]
        return sector_centers[(sector-1) % 8]

    def move_hex(self, hex_obj, direction, distance):
        temp = Hex(hex_obj.q, hex_obj.r)
        for _ in range(distance):
            cloud = CloudMarker(temp, 0)
            cloud.move(direction, self.board)
            temp = cloud.hex_pos
        return temp

    def wind_phase(self, turn_manager: TurnManager):
        if turn_manager.current_hour in [6, 12, 18, 0]:
            for wind in self.wind_directions:
                die = random.randint(1, 6)
                if die in [4, 5]:
                    wind.direction = (wind.direction % 6) + 1
                elif die == 6:
                    wind.direction = (wind.direction - 2) % 6 + 1

    def cloud_phase(self, turn_manager: TurnManager):
        if turn_manager.current_hour % 2 == 0:
            for cloud in self.cloud_markers:
                wind = self.wind_directions[cloud.sector-1]
                cloud.move(wind.direction, self.board)

    def get_cloud_hexes(self):
        cloud_hexes = set()
        for cloud in self.cloud_markers:
            cloud_hexes.add(cloud.hex_pos)
            for neighbor in cloud.hex_pos.neighbors():
                cloud_hexes.add(neighbor)
                for n2 in neighbor.neighbors():
                    cloud_hexes.add(n2)
        return cloud_hexes

    def get_storm_hexes(self):
        from collections import Counter
        hex_counts = Counter()
        for cloud in self.cloud_markers:
            hexes = [cloud.hex_pos] + list(cloud.hex_pos.neighbors())
            for h in hexes:
                hex_counts[h] += 1
        return {h for h, count in hex_counts.items() if count > 1}

    def is_storm_hex(self, hex_obj):
        return hex_obj in self.get_storm_hexes()

    def is_cloud_hex(self, hex_obj):
        return hex_obj in self.get_cloud_hexes()

    def as_pieces(self):
        # Return weather as a list of "pieces" for display on the board
        pieces = []
        for cloud in self.cloud_markers:
            pieces.append({
                "type": "cloud",
                "hex": cloud.hex_pos,
                "sector": cloud.sector,
                "cloud_type": cloud.cloud_type
            })
        for wind in self.wind_directions:
            pieces.append({
                "type": "wind",
                "sector": wind.sector,
                "direction": wind.direction,
                "hex": self.get_directional_hex(wind.sector)
            })
        return pieces

