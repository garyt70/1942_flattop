import unittest

from flattop.operations_chart_models import (
    AircraftFactory,
    AircraftOperationsStatus,
    AircraftType,
    Carrier,
    Ship,
    TaskForce,
)
from flattop.surface_combat_engine import (
    POSITION_GUNNERY,
    POSITION_SCREEN,
    POSITION_TORPEDO,
    assign_default_positions,
    resolve_surface_combat,
)


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


class TestAssignDefaultPositions(unittest.TestCase):
    def test_crippled_and_anchored_forced_to_screen(self):
        crippled = Ship("Cripple", "DD", "Crippled", gunnery_factor=5)
        anchored = Ship("Anchor", "DD", "Anchored", gunnery_factor=5)
        positions = assign_default_positions([crippled, anchored], "Allied")
        self.assertEqual(positions[crippled], POSITION_SCREEN)
        self.assertEqual(positions[anchored], POSITION_SCREEN)

    def test_torpedo_capable_defaults_to_torpedo(self):
        ship = Ship("Torper", "DD", "Operational", gunnery_factor=3, torpedo_factor=4)
        positions = assign_default_positions([ship], "Allied")
        self.assertEqual(positions[ship], POSITION_TORPEDO)

    def test_used_torpedo_defaults_to_gunnery(self):
        ship = Ship("Used", "DD", "Operational", gunnery_factor=3, torpedo_factor=4)
        ship.torpedo_factor_used = True
        positions = assign_default_positions([ship], "Allied")
        self.assertEqual(positions[ship], POSITION_GUNNERY)


class TestBHTAndDice(unittest.TestCase):
    def test_bht_sum_and_bounds(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        attacker.add_ship(Ship("USS Iowa", "BB", "Operational", gunnery_factor=10, damage_factor=10))
        defender.add_ship(Ship("IJN CA", "CA", "Operational", gunnery_factor=10, damage_factor=10))

        low = resolve_surface_combat(attacker, defender, attacker_die=1, defender_die=1, die_roll_fn=lambda: 1)
        self.assertEqual(low["bht"], 2)

        high = resolve_surface_combat(attacker, defender, attacker_die=6, defender_die=6, die_roll_fn=lambda: 1)
        self.assertEqual(high["bht"], 12)

        mid = resolve_surface_combat(attacker, defender, attacker_die=4, defender_die=3, die_roll_fn=lambda: 1)
        self.assertEqual(mid["bht"], 7)
        self.assertEqual(mid["attacker_die"], 4)
        self.assertEqual(mid["defender_die"], 3)


class TestTorpedoPhase(unittest.TestCase):
    def test_torpedo_blocked_below_day_threshold(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        torp_ship = Ship("Torp DD", "DD", "Operational", gunnery_factor=0, torpedo_factor=8, damage_factor=2)
        attacker.add_ship(torp_ship)
        defender.add_ship(Ship("Target", "CA", "Operational", gunnery_factor=0, damage_factor=8))

        result = resolve_surface_combat(attacker, defender, attacker_die=1, defender_die=3, night=False, die_roll_fn=lambda: 6)
        self.assertTrue(result["attacker_torpedo"].get("torpedoes_blocked"))
        self.assertFalse(torp_ship.torpedo_factor_used)

    def test_torpedo_fires_and_is_expended(self):
        attacker = TaskForce(1, side="Japanese")
        defender = TaskForce(2, side="Allied")
        torp_ship = Ship("IJN DD", "DD", "Operational", gunnery_factor=0, torpedo_factor=8, damage_factor=2)
        attacker.add_ship(torp_ship)
        defender.add_ship(Ship("USS Target", "CA", "Operational", gunnery_factor=0, damage_factor=8))

        result = resolve_surface_combat(attacker, defender, attacker_die=5, defender_die=5, night=False, die_roll_fn=lambda: 6)
        self.assertFalse(result["attacker_torpedo"].get("torpedoes_blocked"))
        self.assertTrue(torp_ship.torpedo_factor_used)

    def test_used_torpedoes_do_not_fire_again(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        torp_ship = Ship("USS DD", "DD", "Operational", gunnery_factor=0, torpedo_factor=8, damage_factor=2)
        torp_ship.torpedo_factor_used = True
        attacker.add_ship(torp_ship)
        defender.add_ship(Ship("Target", "CA", "Operational", gunnery_factor=0, damage_factor=8))

        result = resolve_surface_combat(attacker, defender, attacker_die=5, defender_die=5, die_roll_fn=lambda: 6)
        self.assertEqual(result["attacker_torpedo"].get("hits", {}), {})


class TestAmmunitionTracking(unittest.TestCase):
    def test_no_ammo_ship_cannot_fire(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        ship = Ship("Dry", "CA", "Operational", gunnery_factor=20, damage_factor=2, ammunition_factor=0)
        attacker.add_ship(ship)
        defender.add_ship(Ship("Target", "DD", "Operational", gunnery_factor=0, damage_factor=2))

        result = resolve_surface_combat(attacker, defender, attacker_die=3, defender_die=3, die_roll_fn=lambda: 6)
        self.assertEqual(result["attacker_gunnery"]["hits"], {})

    def test_ammo_is_consumed_by_bht(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        ship = Ship("Plenty", "CA", "Operational", gunnery_factor=10, damage_factor=2, ammunition_factor=15)
        attacker.add_ship(ship)
        defender.add_ship(Ship("Target", "DD", "Operational", gunnery_factor=0, damage_factor=99))

        resolve_surface_combat(attacker, defender, attacker_die=3, defender_die=4, die_roll_fn=lambda: 1)
        self.assertEqual(ship.ammunition_factor, 8)

    def test_low_ammo_halves_gunnery(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        ship = Ship("LowAmmo", "CA", "Operational", gunnery_factor=10, damage_factor=2, ammunition_factor=3)
        attacker.add_ship(ship)
        defender.add_ship(Ship("Target", "DD", "Operational", gunnery_factor=0, damage_factor=99))

        result = resolve_surface_combat(attacker, defender, attacker_die=5, defender_die=5, die_roll_fn=lambda: 1)
        story = " ".join(result["attacker_gunnery"].get("story_line", []))
        self.assertIn("halving", story.lower())


class TestScreenAndRestrictions(unittest.TestCase):
    def test_screened_ships_not_targeted_in_gunnery(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        attacker.add_ship(Ship("USS Gunner", "BB", "Operational", gunnery_factor=46, damage_factor=1))
        screened = Ship("IJN Screened", "DD", "Operational", gunnery_factor=0, damage_factor=1)
        exposed = Ship("IJN Exposed", "CA", "Operational", gunnery_factor=0, damage_factor=1)
        defender.add_ship(screened)
        defender.add_ship(exposed)

        resolve_surface_combat(
            attacker,
            defender,
            die_roll_fn=lambda: 6,
            defender_positions={screened: POSITION_SCREEN, exposed: POSITION_GUNNERY},
        )
        self.assertNotEqual(screened.status, "Sunk")

    def test_non_bb_killer_cannot_hit_bb_when_other_targets_exist(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        cl = Ship("USS Atlanta", "CL", "Operational", gunnery_factor=46, damage_factor=1)
        attacker.add_ship(cl)
        bb = Ship("IJN BB", "BB", "Operational", gunnery_factor=0, damage_factor=99)
        dd = Ship("IJN DD", "DD", "Operational", gunnery_factor=0, damage_factor=1)
        defender.add_ship(bb)
        defender.add_ship(dd)

        resolve_surface_combat(
            attacker,
            defender,
            die_roll_fn=lambda: 6,
            defender_positions={bb: POSITION_GUNNERY, dd: POSITION_GUNNERY},
            attacker_gunnery_targets={cl: bb},
        )
        self.assertNotEqual(bb.status, "Sunk")


class TestBreakthrough(unittest.TestCase):
    def test_breakthrough_triggers_at_3_to_1(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        for i in range(3):
            attacker.add_ship(Ship(f"USS BB{i}", "BB", "Operational", gunnery_factor=10, damage_factor=10))

        def_ca = Ship("IJN CA", "CA", "Operational", gunnery_factor=10, damage_factor=99)
        def_screen = Ship("IJN Screen", "DD", "Operational", gunnery_factor=0, damage_factor=99)
        defender.add_ship(def_ca)
        defender.add_ship(def_screen)

        result = resolve_surface_combat(
            attacker,
            defender,
            attacker_die=2,
            defender_die=2,
            die_roll_fn=lambda: 1,
            defender_positions={def_ca: POSITION_GUNNERY, def_screen: POSITION_SCREEN},
        )
        self.assertIsNotNone(result["breakthrough"])
        self.assertEqual(result["breakthrough"]["side"], "attacker")

    def test_no_breakthrough_when_ratio_not_met(self):
        attacker = TaskForce(1, side="Allied")
        defender = TaskForce(2, side="Japanese")
        attacker.add_ship(Ship("USS BB", "BB", "Operational", gunnery_factor=10, damage_factor=10))
        defender.add_ship(Ship("IJN CA", "CA", "Operational", gunnery_factor=10, damage_factor=10))

        result = resolve_surface_combat(attacker, defender, attacker_die=2, defender_die=2, die_roll_fn=lambda: 1)
        self.assertIsNone(result["breakthrough"])


if __name__ == "__main__":
    unittest.main()
