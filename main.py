from flattop.ui.desktop.desktop_ui import DesktopUI # Import the DesktopUI class from the module
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed


def load_hexboard_model():
    """
    Load the hexagonal board game model.
    
    Returns:
        HexBoardModel: An instance of the HexBoardModel class.
    """
    model = HexBoardModel(100, 200)  # Example dimensions, adjust as needed
    model.add_piece(Piece("Player1", Hex(0, 0)))  # Add a piece for demonstration
    model.add_piece(Piece("Player2", Hex(5, 3)))  # Add another piece for demonstration
    
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