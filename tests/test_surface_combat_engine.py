import unittest

from flattop.operations_chart_models import (
    AircraftFactory,
    AircraftOperationsStatus,
    AircraftType,
    Carrier,
    Ship,
    TaskForce,
)
from flattop.surface_combat_engine import resolve_surface_combat


class TestSurfaceCombatEngine(unittest.TestCase):
    def test_surface_combat_sinks_defender_and_removes_ship(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")

        attacker.add_ship(Ship("USS Iowa", "BB", "Operational", gunnery_factor=46, damage_factor=1))
        defender.add_ship(Ship("IJN Fubuki", "DD", "Operational", gunnery_factor=0, damage_factor=1))

        result = resolve_surface_combat(attacker, defender, die_roll_fn=lambda: 6)

        self.assertIsNotNone(result)
        self.assertTrue(result["defender_destroyed"])
        self.assertEqual(len(defender.ships), 0)
        self.assertTrue(attacker.attacked_this_turn)

    def test_surface_combat_sunk_carrier_eliminates_aircraft(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")

        attacker.add_ship(Ship("USS South Dakota", "BB", "Operational", gunnery_factor=46, damage_factor=1))

        carrier = Carrier("Akagi", "CV", "Operational", attack_factor=0, anti_air_factor=4, move_factor=2, damage_factor=4)
        zero = AircraftFactory.create(AircraftType.ZERO)
        zero.count = 3
        carrier.air_operations.set_operations_status(zero, AircraftOperationsStatus.READY)
        defender.add_ship(carrier)

        result = resolve_surface_combat(attacker, defender, die_roll_fn=lambda: 6)

        self.assertIsNotNone(result)
        self.assertTrue(result["defender_destroyed"])
        eliminated = result["attacker"]["eliminated_aircraft"]
        self.assertTrue(any(count == 3 for _, count in eliminated))

    def test_surface_combat_returns_none_for_empty_taskforce(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        attacker.add_ship(Ship("USS Northampton", "CA", "Operational", gunnery_factor=8, damage_factor=1))

        result = resolve_surface_combat(attacker, defender)
        self.assertIsNone(result)

    def test_surface_combat_uses_attacker_target_allocation(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")

        firing_ship = Ship("USS Atlanta", "CL", "Operational", gunnery_factor=46, damage_factor=1)
        attacker.add_ship(firing_ship)

        high_priority = Ship("IJN Shokaku", "CV", "Operational", gunnery_factor=0, damage_factor=5)
        allocated_target = Ship("IJN Kagero", "DD", "Operational", gunnery_factor=0, damage_factor=1)
        defender.add_ship(high_priority)
        defender.add_ship(allocated_target)

        result = resolve_surface_combat(
            attacker,
            defender,
            die_roll_fn=lambda: 6,
            attacker_target_allocation={firing_ship: allocated_target},
        )

        self.assertIsNotNone(result)
        self.assertIn("IJN Kagero", result["attacker"]["sunk_ships"])
        self.assertEqual(high_priority.status, "Operational")


if __name__ == "__main__":
    unittest.main()
