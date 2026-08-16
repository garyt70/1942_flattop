"""
Tests for base damage victory point tracking at end of turn.
"""
import unittest
from flattop.hex_board_game_model import HexBoardModel, Piece, Hex, TurnManager
from flattop.operations_chart_models import Base, AirOperationsConfiguration


class TestBaseDamageVP(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.board = HexBoardModel(10, 10)
        self.turn_manager = TurnManager(total_days=2)
        
    def test_base_damage_awards_vp_per_turn(self):
        """Test that damaged bases with LF≤0 award 5 VP per turn."""
        # Create an Allied base
        base_config = AirOperationsConfiguration(
            name="Test Base Config",
            ready_factors=10,
            launch_factor_min=5,
            launch_factor_max=20,
            launch_factor_normal=10
        )
        allied_base = Base(
            name="Allied Base 1",
            side="Allied",
            air_operations_config=base_config
        )
        allied_base_piece = Piece(
            name="Allied Base 1",
            side="Allied",
            position=Hex(5, 5),
            gameModel=allied_base
        )
        self.board.add_piece(allied_base_piece)
        
        # Damage the base so LF ≤ 0
        # launch_factor_min = 5, so damage of 6 makes it -1
        allied_base.damage = 6
        
        # Verify base is damaged with LF ≤ 0
        self.assertLessEqual(allied_base.available_launch_factor_min, 0)
        
        # Initial VP should be 0
        initial_allied_vp = self.turn_manager.victory_points.allied_points
        initial_japanese_vp = self.turn_manager.victory_points.japanese_points
        
        # Advance turn - Japanese should get 5 VP for damaged Allied base
        self.turn_manager.next_turn(self.board)
        
        # Japanese should have gained 5 VP
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp + 5,
            "Japanese should get 5 VP for damaged Allied base with LF≤0"
        )
        
        # Allied points should be unchanged
        self.assertEqual(
            self.turn_manager.victory_points.allied_points,
            initial_allied_vp,
            "Allied points should not change"
        )
        
        # Advance another turn - should get another 5 VP
        self.turn_manager.next_turn(self.board)
        
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp + 10,
            "Japanese should get 5 VP per turn for damaged base"
        )
    
    def test_undamaged_base_no_vp(self):
        """Test that undamaged bases don't award VP."""
        # Create an undamaged Allied base
        allied_base = Base(name="Allied Base 2", side="Allied")
        allied_base_piece = Piece(
            name="Allied Base 2",
            side="Allied",
            position=Hex(3, 3),
            gameModel=allied_base
        )
        self.board.add_piece(allied_base_piece)
        
        initial_japanese_vp = self.turn_manager.victory_points.japanese_points
        
        # Advance turn
        self.turn_manager.next_turn(self.board)
        
        # No VP should be awarded
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp,
            "No VP should be awarded for undamaged base"
        )
    
    def test_damaged_base_with_positive_lf_no_vp(self):
        """Test that damaged bases with LF>0 don't award VP."""
        base_config = AirOperationsConfiguration(
            name="Test Base Config",
            launch_factor_min=10
        )
        allied_base = Base(
            name="Allied Base 3",
            side="Allied",
            air_operations_config=base_config
        )
        allied_base_piece = Piece(
            name="Allied Base 3",
            side="Allied",
            position=Hex(4, 4),
            gameModel=allied_base
        )
        self.board.add_piece(allied_base_piece)
        
        # Damage the base but keep LF > 0
        allied_base.damage = 5  # LF = 10 - 5 = 5 (still positive)
        
        self.assertGreater(allied_base.available_launch_factor_min, 0)
        
        initial_japanese_vp = self.turn_manager.victory_points.japanese_points
        
        # Advance turn
        self.turn_manager.next_turn(self.board)
        
        # No VP should be awarded
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp,
            "No VP should be awarded for base with LF>0"
        )
    
    def test_multiple_damaged_bases_award_vp(self):
        """Test that multiple damaged bases each award VP."""
        # Create two damaged Allied bases
        for i in range(2):
            base_config = AirOperationsConfiguration(
                launch_factor_min=5
            )
            allied_base = Base(
                name=f"Allied Base {i}",
                side="Allied",
                air_operations_config=base_config
            )
            allied_base.damage = 6  # LF ≤ 0
            allied_base_piece = Piece(
                name=f"Allied Base {i}",
                side="Allied",
                position=Hex(i, i),
                gameModel=allied_base
            )
            self.board.add_piece(allied_base_piece)
        
        initial_japanese_vp = self.turn_manager.victory_points.japanese_points
        
        # Advance turn
        self.turn_manager.next_turn(self.board)
        
        # Japanese should get 5 VP per base = 10 VP total
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp + 10,
            "Japanese should get 5 VP per damaged base (2 bases = 10 VP)"
        )
    
    def test_japanese_base_damage_awards_allied_vp(self):
        """Test that damaged Japanese bases award VP to Allied side."""
        base_config = AirOperationsConfiguration(launch_factor_min=5)
        japanese_base = Base(
            name="Japanese Base 1",
            side="Japanese",
            air_operations_config=base_config
        )
        japanese_base.damage = 6  # LF ≤ 0
        japanese_base_piece = Piece(
            name="Japanese Base 1",
            side="Japanese",
            position=Hex(7, 7),
            gameModel=japanese_base
        )
        self.board.add_piece(japanese_base_piece)
        
        initial_allied_vp = self.turn_manager.victory_points.allied_points
        
        # Advance turn
        self.turn_manager.next_turn(self.board)
        
        # Allied should get 5 VP
        self.assertEqual(
            self.turn_manager.victory_points.allied_points,
            initial_allied_vp + 5,
            "Allied should get 5 VP for damaged Japanese base"
        )
    
    def test_next_phase_triggers_base_vp_at_turn_end(self):
        """Test that next_phase() triggers base VP when advancing to new turn."""
        base_config = AirOperationsConfiguration(launch_factor_min=5)
        allied_base = Base(
            name="Allied Base Phase Test",
            side="Allied",
            air_operations_config=base_config
        )
        allied_base.damage = 6  # LF ≤ 0
        allied_base_piece = Piece(
            name="Allied Base Phase Test",
            side="Allied",
            position=Hex(2, 2),
            gameModel=allied_base
        )
        self.board.add_piece(allied_base_piece)
        
        initial_japanese_vp = self.turn_manager.victory_points.japanese_points
        
        # Advance through all phases to trigger turn change
        # TurnManager starts at phase_index=-1, so we need len(PHASES)+1 calls
        # to cycle through all phases and trigger next_turn()
        phases_count = len(self.turn_manager.PHASES) + 1
        for _ in range(phases_count):
            self.turn_manager.next_phase(self.board)
        
        # Should have advanced to new turn and awarded VP
        self.assertEqual(
            self.turn_manager.victory_points.japanese_points,
            initial_japanese_vp + 5,
            "VP should be awarded when next_phase triggers new turn"
        )
    
    def test_no_board_parameter_no_crash(self):
        """Test that next_turn() without board parameter doesn't crash."""
        # Should not crash, just skip VP awards
        try:
            self.turn_manager.next_turn()
            self.turn_manager.next_turn(None)
        except Exception as e:
            self.fail(f"next_turn() without board should not crash: {e}")


if __name__ == '__main__':
    unittest.main()
