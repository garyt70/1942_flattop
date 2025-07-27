import random
from flattop.hex_board_game_model import Hex, Piece

class WindDirection:
    def __init__(self, sector, direction=None):
        self.sector = sector  # 1-8
        self.direction = direction if direction is not None else random.randint(1, 6) # 1-6 (hex direction, see Flat Top rules)

    def change_direction(self, new_direction):
        self.direction = new_direction

    def __repr__(self):
        return f"WindDirection(sector={self.sector}, direction={self.direction})"

class CloudMarker(Piece):
    """
    A cloud marker is a Piece on the board, with a sector and cloud type.
    It can determine if it is a storm based on overlapping with other clouds.
    """
    def __init__(self, sector, hex_pos, cloud_type="scattered", primary=False):
        # Name for display, side is always "Weather"
        super().__init__(name="Cloud", side="Weather", position=hex_pos, gameModel=None)
        self.sector = sector    # 1-8
        self.cloud_type = cloud_type  # "scattered" or "front"
        self.is_storm = False   # Will be set by WeatherManager

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
        new_hex = Hex(self.position.q + vec.q, self.position.r + vec.r)
        if board.is_valid_tile(new_hex):
            self.position = new_hex

    def __repr__(self):
        return f"CloudMarker(hex={self.position}, sector={self.sector}, type={self.cloud_type}, is_storm={self.is_storm})"

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
                    cloud = CloudMarker(sector, center_hex, "scattered", primary=True)
                    die = random.randint(1, 6)
                    for _ in range(die):
                        cloud.move(die, self.board)
                    self.cloud_markers.append(cloud)
                    #from this cloud marker create cloud coverage up to two hexes from the cloud marker
                    # Create cloud markers one hex out in all 6 directions
                    for direction in range(1, 7):
                        one_hex_out = self.move_hex(cloud.position, direction, 1)
                        self.cloud_markers.append(CloudMarker(sector, one_hex_out, "scattered"))
                    # Create cloud markers two hexes out in all 6 directions
                    for direction in range(1, 7):
                        two_hex_out = self.move_hex(cloud.position, direction, 2)
                        self.cloud_markers.append(CloudMarker(sector, two_hex_out, "scattered"))
                    
        elif self.scenario_cloud_type == "front":
            for sector in range(1, 9):
                center_hex = self.get_directional_hex(sector)
                cloud_center = CloudMarker(sector, center_hex, "front", primary=True)
                cloud_ne = CloudMarker(sector, self.move_hex(center_hex, 2, 5), "front", primary=True)
                cloud_sw = CloudMarker(sector, self.move_hex(center_hex, 5, 5), "front", primary=True)
                self.cloud_markers.extend([cloud_center, cloud_ne, cloud_sw])
                die = random.randint(1, 6)
                for cloud in [cloud_center, cloud_ne, cloud_sw]:
                    for _ in range(die):
                        cloud.move(die, self.board)
                        #from this cloud marker create cloud coverage up to two hexes from the cloud marker
                        # Create cloud markers one hex out in all 6 directions
                        for direction in range(1, 7):
                            one_hex_out = self.move_hex(cloud.position, direction, 1)
                            self.cloud_markers.append(CloudMarker(sector, one_hex_out, "scattered"))
                        # Create cloud markers two hexes out in all 6 directions
                        for direction in range(1, 7):
                            two_hex_out = self.move_hex(cloud.position, direction, 2)
                            self.cloud_markers.append(CloudMarker(sector, two_hex_out, "scattered"))
        self.update_storms()

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
            temp = Hex(temp.q, temp.r)
            direction_vectors = {
                1: Hex(1, 0),    # E
                2: Hex(1, -1),   # NE
                3: Hex(0, -1),   # NW
                4: Hex(-1, 0),   # W
                5: Hex(-1, 1),   # SW
                6: Hex(0, 1),    # SE
            }
            vec = direction_vectors.get(direction, Hex(1, 0))
            temp = Hex(temp.q + vec.q, temp.r + vec.r)
        return temp

    def wind_phase(self, turn_manager):
        if turn_manager.current_hour in [6, 12, 18, 0]:
            for wind in self.wind_directions:
                die = random.randint(1, 6)
                if die in [4, 5]:
                    wind.direction = (wind.direction % 6) + 1
                elif die == 6:
                    wind.direction = (wind.direction - 2) % 6 + 1

    def cloud_phase(self, turn_manager):
        if turn_manager.current_hour % 2 == 0:
            for cloud in self.cloud_markers:
                wind = self.wind_directions[cloud.sector-1]
                cloud.move(wind.direction, self.board)
            self.update_storms()

    def update_storms(self):
        # Count how many cloud markers are in each hex (cloud.position)
        from collections import Counter
        hex_counts = Counter()
        for cloud in self.cloud_markers:
            hex_counts[cloud.position] += 1
        # Optionally, you can store or return hex_counts if needed
        # For now, just update is_storm based on cloud marker count in its hex
        for cloud in self.cloud_markers:
            cloud.is_storm = hex_counts[cloud.position] > 1

    def get_cloud_pieces(self):
        # Return all cloud markers as Piece objects (for display)
        return self.cloud_markers

    def get_wind_pieces(self):
        # Return wind markers as dicts for display
        pieces = []
        for wind in self.wind_directions:
            piece = Piece("Wind", "Weather", position=self.get_directional_hex(wind.sector), gameModel=wind)
            pieces.append(piece)
        return pieces
           

    def get_weather_pieces(self):
        # Return all weather as pieces for display (clouds as Piece, wind as dict)
        pieces = []
        pieces.extend(self.get_cloud_pieces())
        pieces.extend(self.get_wind_pieces())
        return pieces

    def is_storm_hex(self, hex_obj):
        # Returns True if the hex is covered by 2+ clouds
        for cloud in self.cloud_markers:
            if cloud.is_storm and hex_obj == cloud.position:
                return True

    def is_cloud_hex(self, hex_obj):
        # Returns True if the hex is covered by any cloud
        for cloud in self.cloud_markers:
            if hex_obj == cloud.position:
                return True
        return False
    
    def get_weather_at_hex(self, hex_obj):
        # Returns "cloud" if hex is covered by any cloud, "storm" if storm, else "clear"
        for cloud in self.cloud_markers:
            if hex_obj == cloud.position:
                return "storm" if cloud.is_storm else "cloud"
        return "clear"

