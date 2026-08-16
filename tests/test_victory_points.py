"""
Tests for Victory Points tracking system.
"""

import unittest
from flattop.victory_points import VictoryPointsTracker, AIRCRAFT_ELIMINATED_POINTS


class TestVictoryPointsTracker(unittest.TestCase):
    
    def setUp(self):
        self.tracker = VictoryPointsTracker()
    
    def test_initial_points(self):
        """Test that both sides start with 0 points."""
        self.assertEqual(self.tracker.get_points("Allied"), 0)
        self.assertEqual(self.tracker.get_points("Japanese"), 0)
    
    def test_award_aircraft_eliminated(self):
        """Test awarding points for aircraft elimination."""
        # Allied eliminates 5 Japanese Zero aircraft
        self.tracker.award_aircraft_eliminated("Allied", "Zero", 5, unnecessary=False, turn_number=1)
        self.assertEqual(self.tracker.get_points("Allied"), 10)  # 5 * 2 = 10
        self.assertEqual(self.tracker.get_points("Japanese"), 0)
        
        # Japanese eliminates 3 Allied Wildcat aircraft (unnecessary loss)
        self.tracker.award_aircraft_eliminated("Japanese", "Wildcat", 3, unnecessary=True, turn_number=2)
        self.assertEqual(self.tracker.get_points("Allied"), 10)
        self.assertEqual(self.tracker.get_points("Japanese"), 30)  # 3 * 10 = 30
    
    def test_award_ship_sunk(self):
        """Test awarding points for ship sunk."""
        # Allied sinks Japanese CV with damage factor 4
        self.tracker.award_ship_sunk("Allied", "Shokaku", "CV", 4, turn_number=1)
        self.assertEqual(self.tracker.get_points("Allied"), 96)  # 24 * 4 = 96
        
        # Japanese sinks Allied DD with damage factor 1
        self.tracker.award_ship_sunk("Japanese", "Hammann", "DD", 1, turn_number=2)
        self.assertEqual(self.tracker.get_points("Japanese"), 6)  # 6 * 1 = 6
    
    def test_award_ship_damaged(self):
        """Test awarding points for damaged ship (when exiting map)."""
        # Allied damages Japanese CA (3 damage out of 3 damage factor)
        self.tracker.award_ship_damaged("Allied", "Kako", "CA", 3, 3, turn_number=1)
        self.assertEqual(self.tracker.get_points("Allied"), 36)  # 12 * 3 * 1.0 = 36
        
        # Japanese damages Allied CA (1 damage out of 3 damage factor)
        self.tracker.award_ship_damaged("Japanese", "Portland", "CA", 1, 3, turn_number=2)
        self.assertEqual(self.tracker.get_points("Japanese"), 12)  # 12 * 3 * 0.33 = 12
    
    def test_award_base_damaged(self):
        """Test awarding points for base with LF <= 0."""
        # Allied damages Japanese base for 1 turn
        self.tracker.award_base_damaged("Allied", "Rabaul", turn_number=1)
        self.assertEqual(self.tracker.get_points("Allied"), 5)
        
        # Same base damaged for another turn
        self.tracker.award_base_damaged("Allied", "Rabaul", turn_number=2)
        self.assertEqual(self.tracker.get_points("Allied"), 10)
    
    def test_transport_unload(self):
        """Test awarding points for transport unloading."""
        # Allied transport unloads for 3 turns
        self.assertTrue(self.tracker.award_transport_unload("Allied", "Transport1", turn_number=1))
        self.assertTrue(self.tracker.award_transport_unload("Allied", "Transport1", turn_number=2))
        self.assertTrue(self.tracker.award_transport_unload("Allied", "Transport1", turn_number=3))
        self.assertEqual(self.tracker.get_points("Allied"), 9)  # 3 * 3 = 9
        
        # Try to unload for 9th turn (should fail)
        for i in range(5):
            self.tracker.award_transport_unload("Allied", "Transport1", turn_number=4+i)
        # Now at max 8 turns
        self.assertFalse(self.tracker.award_transport_unload("Allied", "Transport1", turn_number=10))
        self.assertEqual(self.tracker.get_points("Allied"), 24)  # 8 * 3 = 24
    
    def test_transport_remaining_value(self):
        """Test calculating remaining transport value after unloading."""
        # Before any unloading, full value
        self.assertEqual(self.tracker.get_transport_remaining_value("Transport1", "AP"), 24)
        
        # After 4 unloads (half), should be half value
        for i in range(4):
            self.tracker.award_transport_unload("Allied", "Transport1", turn_number=i)
        self.assertEqual(self.tracker.get_transport_remaining_value("Transport1", "AP"), 12)
        
        # After 8 unloads (max), should be 0
        for i in range(4):
            self.tracker.award_transport_unload("Allied", "Transport1", turn_number=4+i)
        self.assertEqual(self.tracker.get_transport_remaining_value("Transport1", "AP"), 0)
    
    def test_check_automatic_victory(self):
        """Test checking for automatic victory."""
        # Award Allied 100 points
        self.tracker.award_points("Allied", 100, "test", 1)
        
        # Check with auto victory level 50 (should trigger)
        has_victory, winner = self.tracker.check_automatic_victory(50)
        self.assertTrue(has_victory)
        self.assertEqual(winner, "Allied")
        
        # Check with auto victory level 150 (should not trigger)
        has_victory, winner = self.tracker.check_automatic_victory(150)
        self.assertFalse(has_victory)
        self.assertIsNone(winner)
    
    def test_determine_winner(self):
        """Test determining winner at game end."""
        # Both below 50 points
        self.tracker.award_points("Allied", 40, "test", 1)
        self.tracker.award_points("Japanese", 30, "test", 1)
        self.assertEqual(self.tracker.determine_winner(), "Draw")
        
        # Allied has more and over 50
        self.tracker.award_points("Allied", 20, "test", 2)
        self.assertEqual(self.tracker.determine_winner(), "Allied")
        
        # Reset and test Japanese win
        self.tracker = VictoryPointsTracker()
        self.tracker.award_points("Japanese", 60, "test", 1)
        self.tracker.award_points("Allied", 40, "test", 1)
        self.assertEqual(self.tracker.determine_winner(), "Japanese")
    
    def test_serialization(self):
        """Test that tracker can be serialized and deserialized."""
        # Add some data
        self.tracker.award_aircraft_eliminated("Allied", "Zero", 5, False, 1)
        self.tracker.award_ship_sunk("Japanese", "Lexington", "CV", 4, 2)
        
        # Serialize
        data = self.tracker.to_dict()
        
        # Deserialize
        new_tracker = VictoryPointsTracker.from_dict(data)
        
        # Verify
        self.assertEqual(new_tracker.get_points("Allied"), self.tracker.get_points("Allied"))
        self.assertEqual(new_tracker.get_points("Japanese"), self.tracker.get_points("Japanese"))
        self.assertEqual(len(new_tracker.point_history), len(self.tracker.point_history))


if __name__ == '__main__':
    unittest.main()
