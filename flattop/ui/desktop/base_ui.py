import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from flattop.operations_chart_models import Base, AirOperationsTracker, AirOperationsConfiguration, AirCraft, AircraftOperationsStatus, AircraftCombatData, AircraftFactory, AircraftType

class AirOperationsTrackerDisplay:
    def __init__(self, tracker: AirOperationsTracker, surface, pos=(10, 90)):
        self.tracker = tracker
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw_aircraft_list(self, aircraft_list, x, y):
        
        """
        Draws a list of AirCraft objects on the surface at the specified position.
        """
        for ac in aircraft_list:
            y = self.draw_aircraft(ac, x, y)
        return y

    def draw_aircraft(self, aircraft: AirCraft, x, y):
        """
        Draws a single AirCraft object on the surface at the specified position.
        """
             


        """
            f"AircraftCombatData("
            f"air_to_air={self.air_to_air}, "
            f"level_bombing_high_ship_gp={self.level_bombing_high_ship_gp}, "
            f"level_bombing_high_ship_ap={self.level_bombing_high_ship_ap}, "
            f"level_bombing_high_base={self.level_bombing_high_base}, "
            f"level_bombing_low_ship_gp={self.level_bombing_low_ship_gp}, "
            f"level_bombing_low_ship_ap={self.level_bombing_low_ship_ap}, "
            f"level_bombing_low_base={self.level_bombing_low_base}, "
            f"dive_bombing_ship_gp={self.dive_bombing_ship_gp}, "
            f"dive_bombing_ship_ap={self.dive_bombing_ship_ap}, "
            f"dive_bombing_base={self.dive_bombing_base}, "
            f"torpedo_bombing_ship={self.torpedo_bombing_ship})"
        """

        ac_type = aircraft.type.name if isinstance(aircraft.type, AircraftType) else str(aircraft.type)
        ac_text = self.font.render(f"{ac_type} (count: {aircraft.count})", True, (180, 220, 255))
        self.surface.blit(ac_text, (x + 20, y))

        acd = aircraft.combat_data
        if acd is not None:
            
            #air to air
            self.surface.blit(self.font.render(str(acd.air_to_air), True, (255, 255, 255)), (x + 180, y))
            #high Level GP, AP
            self.surface.blit(self.font.render(str(acd.level_bombing_high_base_gp), True, (255, 255, 255)), (x + 260, y))
            self.surface.blit(self.font.render(str(acd.level_bombing_high_base_ap), True, (255, 255, 255)), (x + 320, y))
            #low Level GP, AP
            self.surface.blit(self.font.render(str(acd.level_bombing_low_base_gp), True, (255, 255, 255)), (x + 380, y))
            self.surface.blit(self.font.render(str(acd.level_bombing_low_base_ap), True, (255, 255, 255)), (x + 440, y))
            #dive GP, AP
            self.surface.blit(self.font.render(str(acd.dive_bombing_base_gp), True, (255, 255, 255)), (x + 500, y))
            self.surface.blit(self.font.render(str(acd.dive_bombing_base_ap), True, (255, 255, 255)), (x + 560, y))
            #high Level Ship GP, AP
            self.surface.blit(self.font.render(str(acd.level_bombing_high_ship_gp), True, (255, 255, 255)), (x + 620, y))
            self.surface.blit(self.font.render(str(acd.level_bombing_high_ship_ap), True, (255, 255, 255)), (x + 680, y))
            #low Level Ship GP, AP
            self.surface.blit(self.font.render(str(acd.level_bombing_low_ship_gp), True, (255, 255, 255)), (x + 740, y))
            self.surface.blit(self.font.render(str(acd.level_bombing_low_ship_ap), True, (255, 255, 255)), (x + 800, y))
            #dive Ship GP, AP
            self.surface.blit(self.font.render(str(acd.dive_bombing_ship_gp), True, (255, 255, 255)), (x + 860, y))
            self.surface.blit(self.font.render(str(acd.dive_bombing_ship_ap), True, (255, 255, 255)), (x + 920, y))
            #Torpedo Ship
            self.surface.blit(self.font.render(str(acd.torpedo_bombing_ship), True, (255, 255, 255)), (x + 980, y))
            y += 20

        return y + 22

    def draw(self):
        x, y = self.pos
        title = self.font.render("Air Operations Tracker", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30

        self.surface.blit(self.font.render("vs Base", True, (255, 255, 255)), (x + 260, y))
        self.surface.blit(self.font.render("vs Ship", True, (255, 255, 255)), (x + 620, y))
        y += 20

        # Draw headers for the tracker display
        # The headers are for the different types of operations and aircraft combat data
        self.surface.blit(self.font.render("Air2Air", True, (255, 255, 255)), (x + 180, y))
        #Base headers
        self.surface.blit(self.font.render("High Level", True, (255, 255, 255)), (x + 260, y))
        self.surface.blit(self.font.render("Low Level", True, (255, 255, 255)), (x + 380, y))
        self.surface.blit(self.font.render("Dive", True, (255, 255, 255)), (x + 500, y))

        #Ship headers
        self.surface.blit(self.font.render("High Level", True, (255, 255, 255)), (x + 620, y))
        self.surface.blit(self.font.render("Low Level", True, (255, 255, 255)), (x + 740, y))
        self.surface.blit(self.font.render("Dive", True, (255, 255, 255)), (x + 860, y))
        self.surface.blit(self.font.render("Torpedo", True, (255, 255, 255)), (x + 980, y))
        y += 20

        #now display the GP and AP header text
        #high Level GP, AP
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 260, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 320, y))
        #low Level GP, AP
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 380, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 440, y))
        #dive GP, AP
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 500, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 560, y))
        #high Level Ship GP, AP
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 620, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 680, y))
        #low Level Ship GP, AP
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 740, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 800, y))
        #dive Ship GP, AP 
        self.surface.blit(self.font.render("GP", True, (255, 255, 255)), (x + 860, y))
        self.surface.blit(self.font.render("AP", True, (255, 255, 255)), (x + 920, y))
        #Torpedo Ship   
        self.surface.blit(self.font.render("Torpedo", True, (255, 255, 255)), (x + 980, y))
        y += 20
    
        #now display the combat data for each aircraft
        self.surface.blit(self.font.render("Ready", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.ready, x, y)
        self.surface.blit(self.font.render("Readying", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.readying, x, y)
        self.surface.blit(self.font.render("In Flight", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.in_flight, x, y)
        self.surface.blit(self.font.render("Just Landed", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.just_landed, x, y) 

class AirOperationsConfigurationDisplay:
    def __init__(self, config: AirOperationsConfiguration, surface, pos=(10, 10)):
        self.config = config
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw(self):
        x, y = self.pos
        title = self.font.render("Air Operations Configuration", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30

        # Render config headers max capacity, ready_factors, launch_factor_normal, launch_factor_min, launch_factor_max
        self.surface.blit(self.font.render("Max Capacity", True, (200, 200, 0)), (x, y))
        self.surface.blit(self.font.render("Ready Factors", True, (200, 200, 0)), (x + 200, y))
        self.surface.blit(self.font.render("LF (Normal)", True, (200, 200, 0)), (x + 400, y))
        self.surface.blit(self.font.render("LF (Min)", True, (200, 200, 0)), (x + 600, y))
        self.surface.blit(self.font.render("LF (Max)", True, (200, 200, 0)), (x + 800, y))
        y += 25

        # Render config values
        self.surface.blit(self.font.render(str(self.config.maximum_capacity), True, (255, 255, 255)), (x, y))
        self.surface.blit(self.font.render(str(self.config.ready_factors), True, (255, 255, 255)), (x + 200, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_normal), True, (255,   255, 255)), (x + 400, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_min), True, (255, 255, 255)), (x + 600, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_max), True, (255, 255, 255)), (x + 800, y))


class BaseUIDisplay:
    def __init__(self, base:Base, surface):
        self.surface = surface
        self.config_display = AirOperationsConfigurationDisplay(base.air_operations_config, surface)
        self.tracker_display = AirOperationsTrackerDisplay(base.air_operations_tracker, surface)
        

    def draw(self):
        self.surface.fill((0, 0, 40))
        self.config_display.draw()
        self.tracker_display.draw()

        pygame.display.flip()

        waiting = True
        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

# Example usage:
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1200, 600))
    pygame.display.set_caption("Flattop Air Operations")
    clock = pygame.time.Clock()

    # Replace with actual tracker and config objects
    config = AirOperationsConfiguration("Test Config", "Test description")
    tracker = AirOperationsTracker("Test", "Test Description",config)
    tracker.set_operations_status(AircraftFactory.create(AircraftType.P40, count=12),AircraftOperationsStatus.READY)
    tracker.set_operations_status(AircraftFactory.create(AircraftType.P40, count=10),AircraftOperationsStatus.READYING)
    tracker.set_operations_status(AircraftFactory.create(AircraftType.CATALINA, count=4),AircraftOperationsStatus.READY)
    tracker.set_operations_status(AircraftFactory.create(AircraftType.B17, count=6),AircraftOperationsStatus.READYING)

    base = Base("Test Base", "Test Description", tracker, config)

    ui = BaseUIDisplay(base, screen)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        ui.draw()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()