import unittest
from flattop.operations_chart_models import AirOperationsConfiguration

from flattop.operations_chart_models import (
    AirOperationsChart,
    TaskForce,
    AirFormation,
    AirCraft,
    Ship,
    Carrier,
    AirOperationsTracker,
    Base,
    AircraftOperationsStatus,
    AircraftType,
    AircraftFactory
)

class TestAirOperationsChart(unittest.TestCase):
    def test_init(self):
        chart = AirOperationsChart(name="Test Chart", description="Test Desc")
        self.assertEqual(chart.name, "Test Chart")
        self.assertEqual(chart.description, "Test Desc")
        self.assertEqual(len(chart.air_formations), 35)
        self.assertEqual(len(chart.task_forces), 14)
        self.assertEqual(chart.side, "Allied")
        chart1 = AirOperationsChart(name="Test Chart", description="Test Desc", side="Axis")
        self.assertEqual(chart1.side, "Axis")

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

    def test_bases_dict(self):
        chart = AirOperationsChart()
        base = Base("TestBase")
        chart.bases["TestBase"] = base
        self.assertIn("TestBase", chart.bases)
        self.assertIs(chart.bases["TestBase"], base)

class TestAircraftFactory(unittest.TestCase):
    def test_type(self):
        test_aircraft = AircraftFactory.create(AircraftType.A20, 19)
        self.assertTrue(test_aircraft.type , "A20")

class TestTaskForce(unittest.TestCase):
    def test_add_ship(self):
        tf = TaskForce(1)
        ship = Ship("Destroyer", "Destroyer", status="operational")
        tf.add_ship(ship)
        self.assertIn(ship, tf.ships)

    def test_add_carrier_limit(self):
        tf = TaskForce(1)
        carrier1 = Carrier("Enterprise", "CV", "operational")
        carrier2 = Carrier("Hornet", "CVL", "operational")
        tf.add_ship(carrier1)
        with self.assertRaises(ValueError):
            tf.add_ship(carrier2)

    def test_get_carriers(self):
        tf = TaskForce(1)
        carrier = Carrier("Enterprise", "CV", "operational")
        ship = Ship("Destroyer", "Destroyer", "operational")
        tf.add_ship(carrier)
        tf.add_ship(ship)
        carriers = tf.get_carriers()
        self.assertIn(carrier, carriers)
        self.assertNotIn(ship, carriers)

    def test_remove_ship(self):
        tf = TaskForce(1)
        ship = Ship("Destroyer", "Destroyer", "operational")
        tf.add_ship(ship)
        tf.remove_ship(ship)
        self.assertNotIn(ship, tf.ships)

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

    def test_remove_aircraft(self):
        af = AirFormation(1)
        ac = AirCraft("Fighter")
        af.add_aircraft(ac)
        af.remove_aircraft(ac)
        self.assertNotIn(ac, af.aircraft)

    def test_airformation_repr(self):
        af = AirFormation(1)
        self.assertIn("Air Formation", repr(af))

class TestAirOperationsTracker(unittest.TestCase):
    def setUp(self):
        self.tracker = AirOperationsTracker("Test Tracker", "Test Desc", AirOperationsConfiguration(("Test")))
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
        carrier = Carrier("Enterprise", "CV", "operational")
        self.assertEqual(carrier.type, "CV")
        self.assertEqual(carrier.status, "operational")
        self.assertIsInstance(carrier.air_operations, AirOperationsTracker)

    def test_carrier_add_aircraft(self):
        carrier = Carrier("Enterprise", "CV", "operational")
        ac = AirCraft("Fighter")
        carrier.air_operations.set_operations_status(ac, 'ready')
        self.assertIn(ac, carrier.air_operations.ready)


class TestAirOperationsConfiguration(unittest.TestCase):
    def test_default_init(self):
        config = AirOperationsConfiguration()
        self.assertEqual(config.name, "Air Operations Configuration")
        self.assertEqual(config.description, "")
        self.assertEqual(config.maximum_capacity, 1)
        self.assertEqual(config.launch_factor_normal, 1)
        self.assertEqual(config.ready_factors, 1)
        self.assertEqual(config.plane_handling_type, "CV")

    def test_custom_init(self):
        config = AirOperationsConfiguration(
            name="Custom Config",
            description="Test config",
            maximum_capacity=5,
            launch_factor_normal=3,
            ready_factors=2,
            plane_handling_type="Base"
        )
        self.assertEqual(config.name, "Custom Config")
        self.assertEqual(config.description, "Test config")
        self.assertEqual(config.maximum_capacity, 5)
        self.assertEqual(config.launch_factor_normal, 3)
        self.assertEqual(config.ready_factors, 2)
        self.assertEqual(config.plane_handling_type, "Base")

class TestScenarioOneSetupRingsAroundRabul(unittest.TestCase):
    def test_scenario_setup(self):
        chartJapanase = AirOperationsChart(name="Japanese", description="Japanese Rings around Rabul", side="Japanese") 
        self.assertEqual(chartJapanase.side, "Japanese")
        chartJapanase.bases["Rabul"] = Base("Rabul")
        
        baseRahulJapanese = chartJapanase.bases["Rabul"]
        baseRahulJapanese.air_operations_configuration = AirOperationsConfiguration(
            name="Rabul",
            description="Configuration for air operations at Rabul",
            maximum_capacity=9999,
            launch_factor_normal=12,
            ready_factors=7,
            plane_handling_type="Base"
        )
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Zero", count=10),AircraftOperationsStatus.READY)
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Val", count=8),AircraftOperationsStatus.READY)
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Kate", count=10),AircraftOperationsStatus.READY)
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Mavis", count=8),AircraftOperationsStatus.READY)
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Rufe", count=1),AircraftOperationsStatus.READY)
        baseRahulJapanese.air_operations.set_operations_status(AirCraft("Nell", count=12),AircraftOperationsStatus.READY)
        
        self.assertIsInstance(baseRahulJapanese, Base)
        self.assertEqual(baseRahulJapanese.name, "Rabul")
        self.assertIsInstance(chartJapanase, AirOperationsChart)
        self.assertIsInstance(baseRahulJapanese.air_operations, AirOperationsTracker)
        
        chartAllied = AirOperationsChart(name="Allied", description="Allied Rings around Rabul", side="Allied")
        self.assertEqual(chartAllied.side, "Allied")

        chartAllied.bases["Port Moresby"] = Base("Port Moresby")
        basePortMoresbyAllied = chartAllied.bases["Port Moresby"]
        basePortMoresbyAllied.air_operations_configuration = AirOperationsConfiguration(
            name="Port Moresby",
            description="Configuration for air operations at Port Moresby",
            maximum_capacity=9999,
            launch_factor_normal=20,
            ready_factors=8,
            plane_handling_type="LP"
        )
        basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("P-40", count=12),AircraftOperationsStatus.READY)
        basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("Catalina", count=4),AircraftOperationsStatus.READY)

        chartAllied.task_forces[1] = TaskForce(1)
        chartAllied.task_forces[1].add_ship(Carrier("Lexington", "CV", "operational",1,4,2))
        chartAllied.task_forces[1].add_ship(Ship("Pensecola", "CA", "operational",5,2,2))
        chartAllied.task_forces[1].add_ship(Ship("Minneapolis", "CA", "operational",4,2,2))
        chartAllied.task_forces[1].add_ship(Ship("San Francisco", "CA", "operational",4,2,2))
        chartAllied.task_forces[1].add_ship(Ship("Indianapolis", "CA", "operational",4,2,2))
        for i in range(10):
            chartAllied.task_forces[1].add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2))

        self.assertEqual(len(chartAllied.task_forces[1].ships), 15)
        self.assertIsInstance(chartAllied.task_forces[1].ships[0], Carrier)
        self.assertIsInstance(chartAllied.task_forces[1].ships[1], Ship)

        # Print statements for manual inspection (optional)
        print("Japanese Chart:", chartJapanase)
        print("Allied Chart:", chartAllied)
        print("Allied Task Force 1 Ships:", chartAllied.task_forces[1])

if __name__ == "__main__":
    unittest.main()