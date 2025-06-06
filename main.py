from flattop.ui.desktop.desktop_ui import DesktopUI # Import the DesktopUI class from the module
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed
from flattop.operations_chart_models import AirOperationsChart, Base, AirOperationsConfiguration, AirCraft, AircraftStatus, TaskForce, Carrier, Ship


def scenario_one_setup(hexboard_model):

    chartJapanase = AirOperationsChart(name="Japanese", description="Japanese Rings around Rabul", side="Japanese") 
    chartJapanase.bases["Rabul"] = Base("Rabul")
    
    baseRahulJapanese = chartJapanase.bases["Rabul"]
    baseRahulJapanese.air_operations_configuration = AirOperationsConfiguration(
        name="Rabul",
        description="Configuration for air operations at Rabul",
        maximum_capacity=9999,
        launch_factors=12,
        ready_factors=7,
        plane_handling_type="Base"
    )
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Zero", count=10),AircraftStatus.READY)
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Val", count=8),AircraftStatus.READY)
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Kate", count=10),AircraftStatus.READY)
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Mavis", count=8),AircraftStatus.READY)
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Rufe", count=1),AircraftStatus.READY)
    baseRahulJapanese.air_operations.set_operations_status(AirCraft("Nell", count=12),AircraftStatus.READY)

    hexboard_model.add_piece(Piece("Japanese Rabul Base", Hex(0, 0), gameModel=baseRahulJapanese))  # Add a piece for Japanese base


    chartAllied = AirOperationsChart(name="Allied", description="Allied Rings around Rabul", side="Allied")
    chartAllied.bases["Port Moresby"] = Base("Port Moresby")
    basePortMoresbyAllied = chartAllied.bases["Port Moresby"]
    basePortMoresbyAllied.air_operations_configuration = AirOperationsConfiguration(
        name="Port Moresby",
        description="Configuration for air operations at Port Moresby",
        maximum_capacity=9999,
        launch_factors=20,
        ready_factors=8,
        plane_handling_type="LP"
    )
    basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("P-40", count=12),AircraftStatus.READY)
    basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("Catalina", count=4),AircraftStatus.READY)
    
    hexboard_model.add_piece(Piece("Allied Port Morseby", Hex(5, 3), gameModel=basePortMoresbyAllied))  # Add a piece for Allied base

    taskForce = TaskForce(1, "Allied Task Force 1", "Allied")
    taskForce.add_ship(Carrier("Lexington", "CV", "operational",1,4,2))


    taskForce.add_ship(Ship("Pensecola", "CA", "operational",5,2,2))
    taskForce.add_ship(Ship("Minneapolis", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("San Francisco", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("Indianapolis", "CA", "operational",4,2,2))
    for i in range(10):
        taskForce.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2))
    
    chartAllied.task_forces[1] = taskForce
    hexboard_model.add_piece(Piece("Allied Task Force 1", Hex(3, 2), gameModel=taskForce))  # Add a piece for Allied Task Force


    print("Japanese Chart:", chartJapanase)
    print("Allied Chart:", chartAllied)
    print("Allied Task Force 1 Ships:", chartAllied.task_forces[1])

def load_hexboard_model():
    """
    Load the hexagonal board game model.
    
    Returns:
        HexBoardModel: An instance of the HexBoardModel class.
    """
    model = HexBoardModel(60, 30)  # Example dimensions, adjust as needed    
    scenario_one_setup(model)  # Set up the scenario on the board model

    return model 

def main():
    """
    Main function to initialize the hexagonal board game model and start the desktop UI.
    """
    boardModel = load_hexboard_model() # Create a board model with specified dimensions
    desktopUI = DesktopUI(boardModel)  # Initialize the DesktopUI with the board model
    desktopUI.initialize()  # Set up the UI
    desktopUI.run()  # Start the UI event loop
    

if __name__ == "__main__":
    main()  # Run the main function to start the application
# This code initializes a hexagonal board game model and starts the desktop UI for interaction.