from flattop.ui.desktop.desktop_ui import DesktopUI # Import the DesktopUI class from the module
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed
from flattop.operations_chart_models import AirOperationsChart, Base, AirOperationsConfiguration, AirCraft, AircraftStatus, TaskForce, Carrier, Ship, AirFormation


def scenario_one_setup():



    """
    Set up the first scenario for the hexagonal board game model.
    This function initializes the game model with specific bases, air formations, and task forces for both Japanese and Allied sides.
    Returns:
        HexBoardModel: An instance of the HexBoardModel class with the scenario set up.
    """
    

    ###########################################
    ## setup the land hexes for the scenario
    land_hexes =  {
        (0, 0), (0, 1), 0, (0, 2), (1, 0), (1, 1), (1, 2), 
        (2, 0), (2, 1), (2, 2), (3, 0), (3, 1), (3, 2),
        (4, 0), (4, 1), (4, 2), (5, 0), (5, 1), (5, 2),
        (6, 0), (6, 1), (6, 2), (7, 0), (7, 1), (7, 2)
        }  # Example land hexes, adjust as needed

    hexboard_model = HexBoardModel(60, 30, land_hexes)  # Example dimensions, adjust as needed   


    ####################
    ## setup Japanese base at Rabul and Japanese Air Formation
    chartJapanase = AirOperationsChart(name="Japanese", description="Japanese Rings around Rabul", side="Japanese") 
    
    #setup Japanese base at Rabul
    
    baseRahulJapanese = Base("Rabul",side="Japanese")  # Create a base for the Japanese side
    baseRahulJapanese.air_operations_config = AirOperationsConfiguration(
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
    
    chartJapanase.bases[baseRahulJapanese.name] = baseRahulJapanese  # Add the base to the Japanese chart
    
    hexboard_model.add_piece(Piece("Japanese Rabul Base", side="Japanese", position=Hex(0, 0), gameModel=baseRahulJapanese))  # Add a piece for Japanese base

    #add a test AirFormation to the Japanese chart
    airFormationOneJapanese = AirFormation("Japanese Air Formation 1", "Japanese")
    airFormationOneJapanese.add_aircraft(AirCraft("Zero", count=6))
    airFormationOneJapanese.add_aircraft(AirCraft("Val", count=4))

    chartJapanase.air_formations[1] = airFormationOneJapanese  # Add the air formation to the Japanese chart

    hexboard_model.add_piece(Piece(name="Japanese Air Formation 1", side="Japanese", position=Hex(10, 10), gameModel=airFormationOneJapanese))  # Add a piece for Japanese Air Formation

    ###########################################
    ## setup Allied base at Port Moresby and Allied Task Force
    chartAllied = AirOperationsChart(name="Allied", description="Allied Rings around Rabul", side="Allied")
    basePortMoresbyAllied = Base("Port Moresby",side="Allied")  # Create a base for the Allied side
    basePortMoresbyAllied.air_operations_config = AirOperationsConfiguration(
        name="Port Moresby",
        description="Configuration for air operations at Port Moresby",
        maximum_capacity=9999,
        launch_factors=20,
        ready_factors=8,
        plane_handling_type="LP"
    )
    basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("P-40", count=12),AircraftStatus.READY)
    basePortMoresbyAllied.air_operations.set_operations_status(AirCraft("Catalina", count=4),AircraftStatus.READY)
    chartAllied.bases[basePortMoresbyAllied.name] = basePortMoresbyAllied  # Add the base to the Allied chart

    hexboard_model.add_piece(Piece("Allied Port Morseby", "Allied", Hex(20, 25), gameModel=basePortMoresbyAllied))  # Add a piece for Allied base

    taskForce = TaskForce(1, "Allied Task Force 1", "Allied")
    carrierLexington = Carrier("Lexington", "CV", "operational", 1, 4, 2)
    carrierLexington.air_operations_config = AirOperationsConfiguration(
        name="Lexington",
        description="Configuration for air operations on Lexington",
        maximum_capacity=20,
        launch_factors=12,
        ready_factors=6,
        plane_handling_type="SP"
    )
    carrierLexington.air_operations.set_operations_status(AirCraft("Wildcat", count=8),AircraftStatus.READY)
    carrierLexington.air_operations.set_operations_status(AirCraft("Dauntless", count=12),AircraftStatus.READY)
    carrierLexington.air_operations.set_operations_status(AirCraft("Devastator", count=4),AircraftStatus.READY)

    taskForce.add_ship(carrierLexington)  # Add the carrier to the task force
    taskForce.add_ship(Ship("Pensecola", "CA", "operational",5,2,2))
    taskForce.add_ship(Ship("Minneapolis", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("San Francisco", "CA", "operational",4,2,2))
    taskForce.add_ship(Ship("Indianapolis", "CA", "operational",4,2,2))
    for i in range(10):
        taskForce.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2))
    
    chartAllied.task_forces[1] = taskForce
    hexboard_model.add_piece(Piece(name="Allied Task Force 1", side="Allied", position=Hex(30, 20), gameModel=taskForce))  # Add a piece for Allied Task Force


    print("Japanese Chart:", chartJapanase)
    print("Allied Chart:", chartAllied)
    print("Allied Task Force 1 Ships:", chartAllied.task_forces[1])

    return hexboard_model  # Return the hexagonal board model with the scenario set up

def load_hexboard_model():
    """
    Load the hexagonal board game model.
    
    Returns:
        HexBoardModel: An instance of the HexBoardModel class.
    """ 
    model = scenario_one_setup()  # Set up the scenario on the board model

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