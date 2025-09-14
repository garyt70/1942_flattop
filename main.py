from flattop.ui.desktop.desktop_ui import DesktopUI # Import the DesktopUI class from the module
from flattop.hex_board_game_model import HexBoardModel, Hex, Piece  # Adjust import as needed
from flattop.operations_chart_models import AlliedShipFactory, AirOperationsChart, Base, AirOperationsConfiguration, Aircraft, AircraftOperationsStatus, JapaneseShipFactory, TaskForce, Carrier, Ship, AirFormation, AircraftFactory, AircraftType


LAND_HEXES_BOARD_ONE =  {
        (0, 9), (1, 9),  
        (0, 10), (1, 10), (2, 10), (3, 10), 
        (0, 11), (1, 11), (2, 11), (3, 11), 
        (0, 12), (1, 12), (2, 12), (3, 12), 
        (0, 13), (1, 13), (2, 13),  
        (0, 14), (1, 14), (2,14),
        (0, 15), (1, 15), (2,15),
        (0, 16), (1, 16), (2,16), (3,16),
        (0, 17), (1, 17), (2,17), (3, 17), (4, 17), (5, 17),
        (0, 18), (1, 18), (2, 18), (3, 18), (4, 18), (5, 18),
        (0, 19), (1, 19), (2, 19), (3, 19), (4, 19), (5, 19),
        (0, 20), (1, 20), (2, 20), (3, 20), (4, 20), (5, 20), (6, 20),
        (0, 21), (1, 21), (2, 21), (3, 21), (4, 21), (5, 21), (6, 21), (7, 21), (8, 21), (9, 21), (10, 21),
        (0, 22), (1, 22), (2, 22), (3, 22), (4, 22), (5, 22), (6, 22), (7, 22), (8, 22), (9, 22),
        (0, 23), (1, 23), (2, 23), (3, 23), (4, 23), (5, 23), (6, 23), (7, 23), (8, 23), (9, 23), (10, 23), (11,23),
                                    (3,24), (4, 24), (5, 24), (6, 24), (7, 24), (8, 24), (9, 24), (10, 24), (11, 24), (12, 24), (13, 24),
                                            (4, 25), (5, 25), (6, 25), (7, 25), (8, 25), (9, 25), (10, 25), (11, 25), (12, 25),   
                                             (4, 26), (5, 26), (6, 26), (7, 26), (8, 26), (9, 26), (10, 26), (11, 26), (12, 26), (13, 26), (14, 26), (15, 26), (16, 26), (17, 26), (18, 26), (19, 26), (20, 26),
                                                               (6, 28), (7, 27), (8, 27), (9, 27), (10, 27), (11, 27), (12, 27), (13, 27), (14, 27), (15, 27), (16, 27), (17, 27), (18, 27), (19, 27), (20, 27),
        (3,7),                                                (13,6),
        (22,0), (23,0), (23,1), (24,2), (25,2), (25,3), (25,4), (26,3), (26,4), 
                                                                                                                        (21,3),       ( 23,3),
                                                                                                                        (21,4), (22,4), (23,4),       
        (4,8), (5,8),                                          (14,5),                                                   (21,5), (22,5), (2,5),
                                                       (14,6),                                                   (21,6), (22,6), (23,6),
                (7,7), (8,7),                       (12,7), (13,7), (14,7), (15,7), (16,7), (17,7), (18,7),(19,7),(20,7), (21,7),(22,7), (23,7), 
        (6,8), (7,8), (8,8), (9,8), (10,8), (11,8), (12,8), (13,8), (14,8), (15,8), (16,8), (17,8), (18,8), (19,8),(20,8), (21,8), (22,8),
                       (8,9), (9,9), (10,9), (11,9), (12,9), (13,9), (14,9), (15,9), (16,9),(17,9),(18,9), (19,9), (20,9),(21,9),  (22,9),
                              (9,10), (10,10), (11,10), (12,10), (13,10), (14,10), (15,10), (16,10), 
                       

        (33,6), 
        (33,7),
            (34,8),
            (34,9), (35,9),
            (34,10), (35,10),
            (34,11), (35,11), (36,11), 
            (34,12), (35,12), (36,12), 
                     (35,13), (36,13), (37,13), 
                    (35,14), (36,14), (37,14),
    }  

LAND_HEXES_BOARD_TWO =  {
        (40, 14), (41, 14),(42, 15),
(38, 16), (39, 16), 

                                                                  (47,16),
                                                                    (47,17),
                         (44,16),                                (48,18),  #Tulagi - 44,16
                                                                    (49,18),
       (41,16), (42,17), (43,17), (44,18), (45,18),                (49,19),  # Henderson - 43,17
        (41,17), (42,18), (43,18), (44,19), (45,19),

                  (47,21), (48, 22), (48,23), (49,23),                        (78, 35), (79, 35), # Indeni
                                                                               (78,36),  
}

def scenario_one_setup():



    """
    Set up the first scenario for the hexagonal board game model.
    This function initializes the game model with specific bases, air formations, and task forces for both Japanese and Allied sides.
    Returns:
        HexBoardModel: An instance of the HexBoardModel class with the scenario set up.
    """
    

    ###########################################
    ## setup the land hexes for the scenario
    hexboard_model = HexBoardModel(44, 50, LAND_HEXES_BOARD_ONE)  # Example dimensions, adjust as needed   


    ####################
    ## setup Japanese base at Rabul and Japanese Air Formation
    chartJapanase = AirOperationsChart(name="Japanese", description="Japanese Rings around Rabul", side="Japanese") 
    
    #setup Japanese base at Rabul


    air_operations_config_rabaul = AirOperationsConfiguration(
        name="Rabaul",
        description="Configuration for air operations at Rabaul",
        maximum_capacity=9999,
        launch_factor_min=6,
        launch_factor_normal=12,
        launch_factor_max=24,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=8
    )
    baseRabaulJapanese = Base("Rabaul",side="Japanese", air_operations_config=air_operations_config_rabaul)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Rabul Base", side="Japanese", position=Hex(23, 4, "land"), gameModel=baseRabaulJapanese))  # Add a piece for Japanese base

    air_operations_config_gasmata = AirOperationsConfiguration(
        name="Gasmata",
        description="Configuration for air operations at Gasmata",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseGasmataJapanese = Base("Gasmata",side="Japanese", air_operations_config=air_operations_config_gasmata)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Gasmata Base", side="Japanese", position=Hex(14, 10, "land"), gameModel=baseGasmataJapanese))  # Add a piece for Japanese base

    air_operations_config_kavieng = AirOperationsConfiguration(
        name="Kavieng",
        description="Configuration for air operations at Kavieng",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseKaviengJapanese = Base("Kavieng",side="Japanese", air_operations_config=air_operations_config_kavieng)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Kavieng Base", side="Japanese", position=Hex(12, 0, "land"), gameModel=baseKaviengJapanese))  # Add a piece for Japanese base

    air_operations_config_truk = AirOperationsConfiguration(
        name="Truk",
        description="Configuration for air operations at Truk",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseTrukJapanese = Base("Truk",side="Japanese", air_operations_config=air_operations_config_truk)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Truk Base", side="Japanese", position=Hex(17, 0, "land"), gameModel=baseTrukJapanese))  # Add a piece for Japanese base


    baseRabaulJapanese.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.ZERO, count=10),AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.VAL, count=8)
    ac.armament = "AP"
    ac.height = "Low"
    baseRabaulJapanese.air_operations_tracker.set_operations_status(ac,AircraftOperationsStatus.READY)
    baseRabaulJapanese.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.KATE, count=10),AircraftOperationsStatus.READYING)
    baseRabaulJapanese.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.MAVIS, count=8),AircraftOperationsStatus.READYING)
    baseRabaulJapanese.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.RUFE, count=1),AircraftOperationsStatus.READYING)
    baseRabaulJapanese.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.NELL, count=12),AircraftOperationsStatus.READYING)

    chartJapanase.bases[baseRabaulJapanese.name] = baseRabaulJapanese  # Add the base to the Japanese chart
    
    
    #add a test AirFormation to the Japanese chart
    airFormationOneJapanese = AirFormation("Japanese Air Formation 1", "Japanese")
    airFormationOneJapanese.add_aircraft(AircraftFactory.create(AircraftType.ZERO, count=6))
    ac:Aircraft = AircraftFactory.create(AircraftType.VAL, count=4)
    ac.armament = "AP"
    ac.height = "Low"
    airFormationOneJapanese.add_aircraft(ac)

    chartJapanase.air_formations[1] = airFormationOneJapanese  # Add the air formation to the Japanese chart

    hexboard_model.add_piece(Piece(name="Japanese Air Formation 1", side="Japanese", position=Hex(10, 10), gameModel=airFormationOneJapanese))  # Add a piece for Japanese Air Formation

    ###########################################
    ## setup Allied base at Port Moresby and Allied Task Force
    chartAllied = AirOperationsChart(name="Allied", description="Allied Rings around Rabul", side="Allied")
    
    air_operations_config = AirOperationsConfiguration(
        name="Port Moresby",
        description="Configuration for air operations at Port Moresby",
        maximum_capacity=9999,
        launch_factor_min=10,
        launch_factor_normal=20,
        launch_factor_max=40,
        ready_factors=8,
        plane_handling_type="LP"
    )
    basePortMoresbyAllied = Base("Port Moresby",side="Allied" ,air_operations_config = air_operations_config)  # Create a base for the Allied side

    basePortMoresbyAllied.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.P40, count=12),AircraftOperationsStatus.READY)
    basePortMoresbyAllied.air_operations_tracker.set_operations_status(AircraftFactory.create(AircraftType.CATALINA, count=4),AircraftOperationsStatus.READY)
    chartAllied.bases[basePortMoresbyAllied.name] = basePortMoresbyAllied  # Add the base to the Allied chart

    hexboard_model.add_piece(Piece("Allied Port Morseby", "Allied", Hex(3, 23), gameModel=basePortMoresbyAllied))  # Add a piece for Allied base

    taskForce = TaskForce(1, "Allied Task Force 1", "Allied")
    carrierLexington : Carrier = AlliedShipFactory.create("Lexington")
    carrierLexington.air_operations.set_operations_status(AircraftFactory.create(AircraftType.WILDCAT, count=8),AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.DAUNTLESS, count=12)
    ac.armament = "GP"
    carrierLexington.air_operations.set_operations_status(ac,AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.DEVASTATOR, count=4)
    ac.armament = "GP"
    carrierLexington.air_operations.set_operations_status(ac,AircraftOperationsStatus.READY)

    # Add ships to the task force with damage values based on Avalon Hill's Flattop boardgame
    # CL (Light Cruiser): damage_factor = 3 (as per AlliedShipFactory implementation)
    # CV (Carrier): damage_factor = 4
    # DD (Destroyer): damage_factor = 1

    taskForce.add_ship(carrierLexington)  # CV Lexington, damage_factor=4 (already set above)
    taskForce.add_ship(AlliedShipFactory.create("Pensacola"))      # CL Pensacola, damage_factor=3
    taskForce.add_ship(AlliedShipFactory.create("Minneapolis"))    # CL Minneapolis, damage_factor=3
    taskForce.add_ship(AlliedShipFactory.create("San Francisco"))  # CL San Francisco, damage_factor=3
    taskForce.add_ship(AlliedShipFactory.create("Indianapolis"))   # CL Indianapolis, damage_factor=3
    for i in range(10):
        taskForce.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))
    
    chartAllied.task_forces[1] = taskForce
    hexboard_model.add_piece(Piece(name="Allied Task Force 1", side="Allied", position=Hex(20, 10), gameModel=taskForce))  # Add a piece for Allied Task Force


    print("Japanese Chart:", chartJapanase)
    print("Allied Chart:", chartAllied)
    print("Allied Task Force 1 Ships:", chartAllied.task_forces[1])

    hexboard_model.players[chartAllied.side] = chartAllied
    hexboard_model.players[chartJapanase.side] = chartJapanase

    return hexboard_model  # Return the hexagonal board model with the scenario set up

def scenario_two_setup():
     ###########################################
    ## setup the land hexes for the scenario
    hexes = LAND_HEXES_BOARD_ONE.union(LAND_HEXES_BOARD_TWO)
    hexboard_model = HexBoardModel(80, 50, hexes)  # Example dimensions, adjust as needed

    ####################
    ## setup Japanese base at Rabul and Japanese Air Formation
    chartJapanese = AirOperationsChart(name="Japanese", description="Coral Sea", side="Japanese")

    air_operations_config_rabaul = AirOperationsConfiguration(
        name="Rabaul",
        description="Configuration for air operations at Rabaul",
        maximum_capacity=9999,
        launch_factor_min=6,
        launch_factor_normal=12,
        launch_factor_max=24,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=8
    )
    baseRabaulJapanese = Base("Rabaul",side="Japanese", air_operations_config=air_operations_config_rabaul)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Rabul Base", side="Japanese", position=Hex(23, 4, "land"), gameModel=baseRabaulJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseRabaulJapanese.name] = baseRabaulJapanese  # Add the base to the Japanese chart

    air_operations_config_gasmata = AirOperationsConfiguration(
        name="Gasmata",
        description="Configuration for air operations at Gasmata",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseGasmataJapanese = Base("Gasmata",side="Japanese", air_operations_config=air_operations_config_gasmata)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Gasmata Base", side="Japanese", position=Hex(14, 10, "land"), gameModel=baseGasmataJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseGasmataJapanese.name] = baseGasmataJapanese  # Add the base to the Japanese chart

    air_operations_config_kavieng = AirOperationsConfiguration(
        name="Kavieng",
        description="Configuration for air operations at Kavieng",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseKaviengJapanese = Base("Kavieng",side="Japanese", air_operations_config=air_operations_config_kavieng)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Kavieng Base", side="Japanese", position=Hex(12, 0, "land"), gameModel=baseKaviengJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseKaviengJapanese.name] = baseKaviengJapanese  # Add the base to the Japanese chart

    air_operations_config_truk = AirOperationsConfiguration(
        name="Truk",
        description="Configuration for air operations at Truk",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseTrukJapanese = Base("Truk",side="Japanese", air_operations_config=air_operations_config_truk)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Truk Base", side="Japanese", position=Hex(17, 0, "land"), gameModel=baseTrukJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseTrukJapanese.name] = baseTrukJapanese  # Add the base to the Japanese chart

    air_operations_config_lae = AirOperationsConfiguration(
        name="Lae",
        description="Configuration for air operations at Lae",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseLaeJapanese = Base("Lae",side="Japanese", air_operations_config=air_operations_config_lae)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Lae Base", side="Japanese", position=Hex(2, 13, "land"), gameModel=baseLaeJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseLaeJapanese.name] = baseLaeJapanese  # Add the base to the Japanese chart

    air_operations_config_shortland = AirOperationsConfiguration(
        name="Shortland",
        description="Configuration for air operations at Shortland",
        maximum_capacity=9999,
        launch_factor_min=4,
        launch_factor_normal=8,
        launch_factor_max=16,
        ready_factors=7,
        plane_handling_type="LP",
        aaf=5
    )
    baseShortlandJapanese = Base("Shortland",side="Japanese", air_operations_config=air_operations_config_shortland)  # Create a base for the Japanese side
    hexboard_model.add_piece(Piece("Japanese Shortland Base", side="Japanese", position=Hex(38, 16, "land"), gameModel=baseShortlandJapanese))  # Add a piece for Japanese base
    chartJapanese.bases[baseShortlandJapanese.name] = baseShortlandJapanese  # Add the base to the Japanese chart

    #setup Japanese Task Force
    taskForce1 = TaskForce(1, "Shokaku Task Force", "Japanese")
    carrierShokaku : Carrier = JapaneseShipFactory.create("Shokaku")
    ac = AircraftFactory.create(AircraftType.ZERO, count=8)
    ac.armament = None
    carrierShokaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.VAL, count=7)
    ac.armament = None
    carrierShokaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)
    ac = AircraftFactory.create(AircraftType.KATE, count=7)
    ac.armament = None
    carrierShokaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)

    taskForce1.add_ship(carrierShokaku)  # CV Shokaku, damage_factor=4 (already set above)
    taskForce1.add_ship(JapaneseShipFactory.create("Myoko"))      # CA Myoko, damage_factor=3
    taskForce1.add_ship(JapaneseShipFactory.create("Haguro"))    # CA Haguro, damage_factor=3
    taskForce1.add_ship(JapaneseShipFactory.create("Aoba"))  # CA Aoba, damage_factor=3
    taskForce1.add_ship(JapaneseShipFactory.create("Kako"))   # CA Kako, damage_factor=3
    for i in range(4):
        taskForce1.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))

    hexboard_model.add_piece(Piece(name="Shokaku Taskforce", side="Japanese", position=Hex(30, 10), gameModel=taskForce1))  # Add

    taskForce2 = TaskForce(1, "Zuikaku Task Force", "Japanese")
    carrierZuikaku : Carrier = JapaneseShipFactory.create("Zuikaku")
    ac = AircraftFactory.create(AircraftType.ZERO, count=8)
    ac.armament = None
    carrierZuikaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.VAL, count=7)
    ac.armament = None
    carrierZuikaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)
    ac = AircraftFactory.create(AircraftType.KATE, count=7)
    ac.armament = None
    carrierZuikaku.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)

    taskForce2.add_ship(carrierZuikaku)  # CV Zuikaku, damage_factor=4 (already set above)
    taskForce2.add_ship(JapaneseShipFactory.create("Kinugasa"))      # CA Kinugasa, damage_factor=3
    taskForce2.add_ship(JapaneseShipFactory.create("Furutaka"))    # CA Furutaka, damage_factor=3
    taskForce2.add_ship(JapaneseShipFactory.create("Yubari"))  # CA Yubari, damage_factor=3
    taskForce2.add_ship(JapaneseShipFactory.create("Tenryu"))   # CA Tenryu, damage_factor=3

    for i in range(4):
        taskForce2.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))

    hexboard_model.add_piece(Piece(name="Zuikaku Taskforce", side="Japanese", position=Hex(32, 10), gameModel=taskForce2))  # Add a piece for Japanese Task Force

    taskForce3 = TaskForce(3, "Shoho Task Force", "Japanese")
    carrierShoho : Carrier = JapaneseShipFactory.create("Shoho")
    carrierShoho.air_operations.set_operations_status(AircraftFactory.create(AircraftType.KATE, count=3),AircraftOperationsStatus.READYING)
    carrierShoho.air_operations.set_operations_status(AircraftFactory.create(AircraftType.DAVE, count=3),AircraftOperationsStatus.READYING)
    carrierShoho.air_operations.set_operations_status(AircraftFactory.create(AircraftType.PETE, count=4),AircraftOperationsStatus.READYING)

    taskForce3.add_ship(carrierShoho)  # CV Shoho
    taskForce3.add_ship(JapaneseShipFactory.create("Kamikawa"))      # AV Kamikawa
    for i in range(6):
        taskForce3.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))

    hexboard_model.add_piece(Piece(name="Shoho Taskforce", side="Japanese", position=Hex(28, 10), gameModel=taskForce3))  # Add a piece for Japanese Task Force

    taskForce4 = TaskForce(4, "Landing Force 1a", "Japanese")
    for i in range(6):
        taskForce4.add_ship(Ship(f"Transport {i+1}", "AP", "operational",0,0,1,1))
    for i in range(2):
        taskForce4.add_ship(Ship(f"Gunboat {i+1}", "PG", "operational",1,0,2,1))
    for i in range(1):
        taskForce4.add_ship(Ship(f"Oiler {i+1}", "AO", "operational",1,1,2,1))
    for i in range(1):
        taskForce4.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))
    hexboard_model.add_piece(Piece(name="Landing Force", side="Japanese", position=Hex(26, 5), gameModel=taskForce4))  # Add a piece for Japanese Task Force

    taskForce4b = TaskForce(5, "Landing Force 1b", "Japanese")
    for i in range(6):
        taskForce4b.add_ship(Ship(f"Transport {i+1}", "AP", "operational",0,0,1,1))
    for i in range(2):
        taskForce4b.add_ship(Ship(f"Gunboat {i+1}", "PG", "operational",1,0,2,1))
    for i in range(1):
        taskForce4b.add_ship(Ship(f"Oiler {i+1}", "AO", "operational",1,1,2,1))
    for i in range(1):
        taskForce4b.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))
    hexboard_model.add_piece(Piece(name="Landing Force", side="Japanese", position=Hex(26, 5), gameModel=taskForce4b))  # Add a piece for Japanese Task Force


    taskForce5 = TaskForce(6, "Landing Force 2", "Japanese")
    taskForce5.add_ship(JapaneseShipFactory.create("Tatsuta"))    # CL Tatsuta
    taskForce5.add_ship(Ship(f"Transport", "AP", "operational",0,0,1,1))
    for i in range(3):
        taskForce5.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))
    for i in range(4):
        taskForce5.add_ship(Ship(f"Gunboat {i+1}", "PG", "operational",1,0,2,1))

    hexboard_model.add_piece(Piece(name="Landing Force 2", side="Japanese", position=Hex(27, 10), gameModel=taskForce5))  # Add a
    
    chartJapanese.task_forces[1] = taskForce1
    chartJapanese.task_forces[2] = taskForce2
    chartJapanese.task_forces[3] = taskForce3
    chartJapanese.task_forces[4] = taskForce4
    chartJapanese.task_forces[5] = taskForce5
    chartJapanese.task_forces[6] = taskForce4b
    
     ###########################################
    ## setup Allied base at Port Moresby and Allied Task Force
    chartAllied = AirOperationsChart(name="Allied", description="Allied Rings around Rabul", side="Allied")
    
    air_operations_config = AirOperationsConfiguration(
        name="Port Moresby",
        description="Configuration for air operations at Port Moresby",
        maximum_capacity=9999,
        launch_factor_min=10,
        launch_factor_normal=20,
        launch_factor_max=40,
        ready_factors=8,
        plane_handling_type="LP"
    )
    basePortMoresbyAllied = Base("Port Moresby",side="Allied" ,air_operations_config = air_operations_config)  # Create a base for the Allied side
    hexboard_model.add_piece(Piece("Allied Port Morseby", "Allied", Hex(3, 23), gameModel=basePortMoresbyAllied))  # Add a piece for Allied base
    chartAllied.bases[basePortMoresbyAllied.name] = basePortMoresbyAllied  # Add the base to the Allied chart

    air_operations_config_australia = AirOperationsConfiguration(
        name="Australia",
        description="Configuration for air operations at Australia",
        maximum_capacity=9999,
        launch_factor_min=10,
        launch_factor_normal=20,
        launch_factor_max=40,
        ready_factors=8,
        plane_handling_type="LP"
    )
    baseAustraliaAllied = Base("Australia",side="Allied" ,air_operations_config = air_operations_config_australia)  # Create a base for the Allied side
    hexboard_model.add_piece(Piece("Allied Australia", "Allied", Hex(0, 49), gameModel=baseAustraliaAllied))  # Add a piece for Allied base
    chartAllied.bases[baseAustraliaAllied.name] = baseAustraliaAllied  # Add the base to the Allied chart

    air_operations_config_new_cal = AirOperationsConfiguration(
        name="New Caledonia",
        description="Configuration for air operations at New Caledonia",
        maximum_capacity=9999,
        launch_factor_min=10,
        launch_factor_normal=20,
        launch_factor_max=40,
        ready_factors=8,
        plane_handling_type="LP"
    )
    baseNewCaledoniaAllied = Base("New Caledonia",side="Allied" ,air_operations_config = air_operations_config_new_cal)  # Create a base for the Allied side
    hexboard_model.add_piece(Piece("Allied New Caledonia", "Allied", Hex(70, 49), gameModel=baseNewCaledoniaAllied))  # Add a piece for Allied base
    chartAllied.bases[baseNewCaledoniaAllied.name] = baseNewCaledoniaAllied  # Add the base to the Allied chart

    taskForce1 = TaskForce(1, "Lexington Task Force", "Allied")
    carrierLexington : Carrier = AlliedShipFactory.create("Lexington")
    carrierLexington.air_operations.set_operations_status(AircraftFactory.create(AircraftType.WILDCAT, count=7),AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.DAUNTLESS, count=12)
    ac.armament = None
    carrierLexington.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)
    ac = AircraftFactory.create(AircraftType.DEVASTATOR, count=4)
    ac.armament = None
    carrierLexington.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)

    taskForce1.add_ship(carrierLexington)  # CV Lexington, damage_factor=4 (already set above)
    taskForce1.add_ship(AlliedShipFactory.create("Chester"))      
    taskForce1.add_ship(AlliedShipFactory.create("New Orleans"))    
    taskForce1.add_ship(AlliedShipFactory.create("Astoria"))  
    taskForce1.add_ship(AlliedShipFactory.create("Portland"))   
    for i in range(7):
        taskForce1.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))

    for i in range(2):
        taskForce1.add_ship(Ship(f"Tanker {i+1}", "AO", "operational",0,0,2,1))

    chartAllied.task_forces[1] = taskForce1
    hexboard_model.add_piece(Piece(name="Lexington Taskforce", side="Allied", position=Hex(35, 45), gameModel=taskForce1))  # Add a piece for Allied Task Force

    taskForce2 = TaskForce(2, "Yorktown Task Force", "Allied")
    carrierYorktown : Carrier = AlliedShipFactory.create("Yorktown")
    carrierYorktown.air_operations.set_operations_status(AircraftFactory.create(AircraftType.WILDCAT, count=7),AircraftOperationsStatus.READY)
    ac = AircraftFactory.create(AircraftType.DAUNTLESS, count=12)
    ac.armament = None
    carrierYorktown.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)
    ac = AircraftFactory.create(AircraftType.DEVASTATOR, count=4)
    ac.armament = None
    carrierYorktown.air_operations.set_operations_status(ac,AircraftOperationsStatus.READYING)

    taskForce2.add_ship(carrierYorktown)  # CV Yorktown, damage_factor=4 (already set above)
    taskForce2.add_ship(AlliedShipFactory.create("Minneapolis"))      
    taskForce2.add_ship(AlliedShipFactory.create("Australia"))    
    taskForce2.add_ship(AlliedShipFactory.create("Chicago"))  
    taskForce2.add_ship(AlliedShipFactory.create("Hobart"))   
    for i in range(7):
        taskForce2.add_ship(Ship(f"Destroyer {i+1}", "DD", "operational",1,1,2,1))

    chartAllied.task_forces[2] = taskForce2
    hexboard_model.add_piece(Piece(name="Yorktown Taskforce", side="Allied", position=Hex(40, 35), gameModel=taskForce2))  # Add a piece for Allied Task Force


    hexboard_model.players[chartAllied.side] = chartAllied
    hexboard_model.players[chartJapanese.side] = chartJapanese

    return hexboard_model

    
    
    


def load_hexboard_model():
    """
    Load the hexagonal board game model.
    
    Returns:
        HexBoardModel: An instance of the HexBoardModel class.
    """ 
    #model = scenario_one_setup()  # Set up the scenario on the board model
    model = scenario_two_setup()  # Set up the scenario on the board model
    return model




def main():
    """
    Main function to initialize the hexagonal board game model and start the desktop UI.
    """
    boardModel = load_hexboard_model() # Create a board model with specified dimensions
    desktopUI = DesktopUI(boardModel)  # Initialize the DesktopUI with the board model
    desktopUI.turn_manager.current_hour = 6  # Set the current hour to 6
    desktopUI.initialize()  # Set up the UI
    desktopUI.run()  # Start the UI event loop


if __name__ == "__main__":
    main()  # Run the main function to start the application
# This code initializes a hexagonal board game model and starts the desktop UI for interaction.