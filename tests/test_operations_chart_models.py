import unittest

from flattop.operations_chart_models import (
    AirOperationsChart,
    TaskForce,
    AirFormation,
    AirCraft,
    Ship,
    Carrier,
    AirOperationsTracker
)

class TestAirOperationsChart(unittest.TestCase):
    def test_init(self):
        chart = AirOperationsChart(name="Test Chart", description="Test Desc")
        self.assertEqual(chart.name, "Test Chart")
        self.assertEqual(chart.description, "Test Desc")
        self.assertEqual(len(chart.air_formations), 35)
        self.assertEqual(len(chart.task_forces), 14)

    def test_get_air_formation(self):
        chart = AirOperationsChart()
        af = chart.get_air_formation(1)
        self.assertIsInstance(af, AirFormation)
        self.assertEqual(af.number, 1)

    def test_get_task_force(self):
        chart = AirOperationsChart()
        tf = chart.get_task_force(1)
        self.assertIsInstance(tf, TaskForce)
        self.assertEqual(tf.number, 1)

class TestTaskForce(unittest.TestCase):
    def test_add_ship(self):
        tf = TaskForce(1)
        ship = Ship("Destroyer", "operational")
        tf.add_ship(ship)
        self.assertIn(ship, tf.ships)

    def test_add_carrier_limit(self):
        tf = TaskForce(1)
        carrier1 = Carrier("CV", "operational")
        carrier2 = Carrier("CVL", "operational")
        tf.add_ship(carrier1)
        with self.assertRaises(ValueError):
            tf.add_ship(carrier2)

    def test_get_carriers(self):
        tf = TaskForce(1)
        carrier = Carrier("CV", "operational")
        ship = Ship("Destroyer", "operational")
        tf.add_ship(carrier)
        tf.add_ship(ship)
        carriers = tf.get_carriers()
        self.assertIn(carrier, carriers)
        self.assertNotIn(ship, carriers)

class TestAirFormation(unittest.TestCase):
    def test_add_aircraft(self):
        af = AirFormation(1)
        ac = AirCraft("Fighter")
        af.add_aircraft(ac)
        self.assertIn(ac, af.aircraft)

    def test_add_aircraft_type_error(self):
        af = AirFormation(1)
        with self.assertRaises(TypeError):
            af.add_aircraft("not an aircraft")

class TestAirOperationsTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = AirOperationsTracker("Test Tracker", "Test Desc")
        self.ac = AirCraft("Fighter")

    def test_set_operations_status(self):
        self.tracker.set_operations_status(self.ac, 'in_flight')
        self.assertIn(self.ac, self.tracker.in_flight)
        self.tracker.set_operations_status(self.ac, 'just_landed')
        self.assertIn(self.ac, self.tracker.just_landed)
        self.tracker.set_operations_status(self.ac, 'readying')
        self.assertIn(self.ac, self.tracker.readying)
        self.tracker.set_operations_status(self.ac, 'ready')
        self.assertIn(self.ac, self.tracker.ready)

    def test_set_operations_status_type_error(self):
        with self.assertRaises(TypeError):
            self.tracker.set_operations_status("not an aircraft", 'in_flight')

    def test_set_operations_status_invalid_status(self):
        with self.assertRaises(ValueError):
            self.tracker.set_operations_status(self.ac, 'invalid_status')

class TestCarrier(unittest.TestCase):
    def test_carrier_init(self):
        carrier = Carrier("CV", "operational")
        self.assertEqual(carrier.type, "CV")
        self.assertEqual(carrier.status, "operational")
        self.assertIsInstance(carrier.air_operations, AirOperationsTracker)

if __name__ == "__main__":
    unittest.main()