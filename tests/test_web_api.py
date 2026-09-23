"""
Smoke tests for the web application API (see flattop/api/app.py and
docs/design/WEB_ARCHITECTURE.md). These exercise the in-memory game store
end-to-end: scenario catalog, game creation, phase advancement, movement,
and air operations commands.
"""

import unittest

from fastapi.testclient import TestClient

from flattop.api.app import GAMES, app


class TestScenarioCatalog(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_scenarios_returns_published_scenarios(self):
        response = self.client.get("/api/scenarios")
        self.assertEqual(response.status_code, 200)
        ids = [s["id"] for s in response.json()]
        self.assertIn("scenario-one", ids)
        self.assertIn("scenario-two", ids)

    def test_get_scenario_detail(self):
        response = self.client.get("/api/scenarios/scenario-one")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "scenario-one")

    def test_get_unknown_scenario_returns_404(self):
        response = self.client.get("/api/scenarios/does-not-exist")
        self.assertEqual(response.status_code, 404)


class TestGameLifecycle(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        GAMES.clear()

    def _create_game(self, side="Allied"):
        response = self.client.post(
            "/api/games",
            json={"scenario_id": "scenario-one", "player_side": side, "opponent": "computer"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_create_game_returns_side_filtered_projection(self):
        projection = self._create_game("Allied")
        units = projection["units"]
        sides = {unit["side"] for unit in units}
        self.assertIn("Allied", sides)
        # Airbases are fixed installations and are always visible, but the
        # Japanese air formation/task force should not be until observed.
        japanese_units = [unit for unit in units if unit["side"] == "Japanese"]
        self.assertTrue(japanese_units)
        self.assertTrue(all(unit["kind"] == "Base" for unit in japanese_units))

    def test_advance_phase_changes_turn_state(self):
        projection = self._create_game()
        game_id = projection["game_id"]
        response = self.client.post(f"/api/games/{game_id}/advance-phase", params={"side": "Allied"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["turn"]["phase"], "Air Operations")

    def test_move_task_force_within_range_succeeds(self):
        projection = self._create_game()
        game_id = projection["game_id"]
        response = self.client.post(
            f"/api/games/{game_id}/move",
            json={"side": "Allied", "piece_id": "allied-tf-1", "q": 20, "r": 11},
        )
        body = response.json()
        self.assertTrue(body["accepted"])
        moved_unit = next(u for u in body["projection"]["units"] if u["id"] == "allied-tf-1")
        self.assertEqual(moved_unit["position"], [20, 11])

    def test_move_beyond_movement_factor_is_rejected(self):
        projection = self._create_game()
        game_id = projection["game_id"]
        response = self.client.post(
            f"/api/games/{game_id}/move",
            json={"side": "Allied", "piece_id": "allied-tf-1", "q": 20, "r": 40},
        )
        body = response.json()
        self.assertFalse(body["accepted"])
        self.assertEqual(body["error"]["code"], "INSUFFICIENT_MOVEMENT")

    def test_reachable_hexes_are_within_movement_factor(self):
        projection = self._create_game()
        game_id = projection["game_id"]
        response = self.client.get(f"/api/games/{game_id}/units/allied-tf-1/reachable")
        self.assertEqual(response.status_code, 200)
        hexes = response.json()["hexes"]
        self.assertTrue(hexes)
        tf_unit = next(u for u in projection["units"] if u["id"] == "allied-tf-1")
        origin_q, origin_r = tf_unit["position"]
        max_distance = tf_unit["movement_factor"]
        for q, r in hexes:
            self.assertLessEqual(max(abs(q - origin_q), abs(r - origin_r)), max_distance + 1)

    def test_readiness_move_and_create_formation(self):
        projection = self._create_game()
        game_id = projection["game_id"]
        readiness_response = self.client.post(
            f"/api/games/{game_id}/air-ops/readiness",
            json={
                "side": "Allied",
                "base_id": "allied-tf-1",
                "aircraft_type": "Wildcat",
                "from_status": "readying",
                "to_status": "ready",
                "count": 4,
            },
        )
        self.assertTrue(readiness_response.json()["accepted"])
        response = self.client.post(
            f"/api/games/{game_id}/air-ops/formation",
            json={
                "side": "Allied",
                "base_id": "allied-tf-1",
                "formation_number": 3,
                "aircraft": [{"type": "Wildcat", "count": 4}],
            },
        )
        body = response.json()
        self.assertTrue(body["accepted"])
        formation = next(u for u in body["projection"]["units"] if u["kind"] == "AirFormation")
        self.assertEqual(sum(ac["count"] for ac in formation["aircraft"]), 4)


if __name__ == "__main__":
    unittest.main()
