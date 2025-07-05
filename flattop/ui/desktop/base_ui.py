import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from flattop.operations_chart_models import Base, AirOperationsTracker, AirOperationsConfiguration, AirCraft, AircraftOperationsStatus, AircraftCombatData, AircraftFactory, AircraftType



class AircraftDisplay:
    columns = [260, 320, 380, 440, 500, 560, 620, 680, 740, 800, 860, 920, 980, 1040, 1100, 1160]

    def __init__(self):
        pass

    @staticmethod
    def draw_aircraft(surface, aircraft: AirCraft, x, y):
        """
        Draws a single AirCraft object on the surface at the specified position.
        """
        columns = AircraftDisplay.columns
        font = pygame.font.SysFont(None, 24)
             
        ac_type = aircraft.type.name if isinstance(aircraft.type, AircraftType) else str(aircraft.type)
        ac_move=aircraft.move_factor
        ac_text = font.render(f"{ac_type} (#: {aircraft.count} )", True, (180, 220, 255))
        surface.blit(ac_text, (x + 20, y))

        # If the aircraft has a combat data object, display its combat data
        # This includes air-to-air combat, high level bombing, low level bombing, dive bombing
        acd = aircraft.combat_data
        if acd is not None: 
            #air to air
            surface.blit(font.render(str(acd.air_to_air), True, (255, 255, 255)), (x + columns[0], y))
            #high Level GP, AP
            surface.blit(font.render(str(acd.level_bombing_high_base_gp), True, (255, 255, 255)), (x + columns[1], y))
            surface.blit(font.render(str(acd.level_bombing_high_base_ap), True, (255, 255, 255)), (x + columns[2], y))
            #low Level GP, AP
            surface.blit(font.render(str(acd.level_bombing_low_base_gp), True, (255, 255, 255)), (x + columns[3], y))
            surface.blit(font.render(str(acd.level_bombing_low_base_ap), True, (255, 255, 255)), (x + columns[4], y))
            #dive GP, AP
            surface.blit(font.render(str(acd.dive_bombing_base_gp), True, (255, 255, 255)), (x + columns[5], y))
            surface.blit(font.render(str(acd.dive_bombing_base_ap), True, (255, 255, 255)), (x + columns[6], y))
            #high Level Ship GP, AP
            surface.blit(font.render(str(acd.level_bombing_high_ship_gp), True, (255, 255, 255)), (x + columns[7], y))
            surface.blit(font.render(str(acd.level_bombing_high_ship_ap), True, (255, 255, 255)), (x + columns[8], y))
            #low Level Ship GP, AP
            surface.blit(font.render(str(acd.level_bombing_low_ship_gp), True, (255, 255, 255)), (x + columns[9], y))
            surface.blit(font.render(str(acd.level_bombing_low_ship_ap), True, (255, 255, 255)), (x + columns[10], y))
            #dive Ship GP, AP
            surface.blit(font.render(str(acd.dive_bombing_ship_gp), True, (255, 255, 255)), (x + columns[11], y))
            surface.blit(font.render(str(acd.dive_bombing_ship_ap), True, (255, 255, 255)), (x + columns[12], y))
            #Torpedo Ship
            surface.blit(font.render(str(acd.torpedo_bombing_ship), True, (255, 255, 255)), (x + columns[13], y))
           
        #movement details of aircraft
        surface.blit(font.render(str(aircraft.move_factor), True, (255, 255, 255)), (x + columns[14], y))
        surface.blit(font.render(str(aircraft.range_factor), True, (255, 255, 255)), (x + columns[15], y))
        
        y += 20

        return y + 22 

    @staticmethod
    def draw_aircraft_list_header(surface, aircraft: AirCraft, x, y):
        columns = AircraftDisplay.columns
        font = pygame.font.SysFont(None, 24)

        surface.blit(font.render("vs Base", True, (255, 255, 255)), (x + columns[1], y))
        surface.blit(font.render("vs Ship", True, (255, 255, 255)), (x + columns[7], y))
        y += 20

        # Draw headers for the tracker display
        # The headers are for the different types of operations and aircraft combat data
        surface.blit(font.render("Air2Air", True, (255, 255, 255)), (x + columns[0], y))
        #Base headers
        surface.blit(font.render("High", True, (255, 255, 255)), (x + columns[1], y))
        surface.blit(font.render("Low", True, (255, 255, 255)), (x + columns[3], y))
        surface.blit(font.render("Dive", True, (255, 255, 255)), (x + columns[5], y))

        #Ship headers
        surface.blit(font.render("High ", True, (255, 255, 255)), (x + columns[7], y))
        surface.blit(font.render("Low ", True, (255, 255, 255)), (x + columns[9], y))
        surface.blit(font.render("Dive", True, (255, 255, 255)), (x + columns[11], y))
        surface.blit(font.render("Torpedo", True, (255, 255, 255)), (x + columns[13], y))
        y += 20

        #now display the GP and AP header text
        #high Level GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[1], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[2], y))
        #low Level GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[3], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[4], y))
        #dive GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[5], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[6], y))
        
        #high Level Ship GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[7], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[8], y))
        #low Level Ship GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[9], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[10], y))
        #dive Ship GP, AP
        surface.blit(font.render("GP", True, (255, 255, 255)), (x + columns[11], y))
        surface.blit(font.render("AP", True, (255, 255, 255)), (x + columns[12], y))
        #Torpedo Ship
        surface.blit(font.render("Torpedo", True, (255, 255, 255)), (x + columns[13], y))
        #movement
        surface.blit(font.render("Move", True, (255, 255, 255)), (x + columns[14], y))
        surface.blit(font.render("Range", True, (255, 255, 255)), (x + columns[15], y))

        y += 20
        return y

    @staticmethod  
    def draw_aircraft_list(surface, aircraft_list, x, y):
        
        """
        Draws a list of AirCraft objects on the surface at the specified position.
        """
        for ac in aircraft_list:
            y = AircraftDisplay.draw_aircraft(surface, ac, x, y)
        return y

class AirOperationsTrackerDisplay:
    columns = [200, 260, 320, 380, 440, 500, 560, 620, 680, 740, 800, 860, 920, 980]

    def __init__(self, tracker: AirOperationsTracker, surface, pos=(10, 90)):
        self.tracker = tracker
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw_aircraft_list(self, aircraft_list, x, y):
        return AircraftDisplay.draw_aircraft_list(self.surface, aircraft_list, x, y)

    def draw_aircraft(self, aircraft: AirCraft, x, y):
        return AircraftDisplay.draw_aircraft(self.surface, aircraft, x, y)

    def draw(self):
        columns = self.columns
        x, y = self.pos
        title = self.font.render("Air Operations Tracker", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30

        y = AircraftDisplay.draw_aircraft_list_header(self.surface, None, x, y)   
    
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
        self.base = base
        self.config_display = AirOperationsConfigurationDisplay(base.air_operations_config, surface)
        self.tracker_display = AirOperationsTrackerDisplay(base.air_operations_tracker, surface)
        self.create_af_button_rect = None  # Button rect for creating air formation
        self.last_airformation = None      # Store the last created air formation
        self.created_air_formations = []  # store the created AirFormations so that the calling code can implement pieces for them

    def draw(self):
        self.surface.fill((0, 0, 40))
        self.config_display.draw()
        self.tracker_display.draw()


         # Draw the "Create Air Formation" button
        font = pygame.font.SysFont(None, 28)
        button_text = "Create Air Formation"
        btn_surf = font.render(button_text, True, (0, 0, 0))
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = 30, self.surface.get_height() - btn_height - 30
        self.create_af_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, (200, 200, 0), self.create_af_button_rect)
        pygame.draw.rect(self.surface, (255, 255, 255), self.create_af_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))


        pygame.display.flip()

        waiting = True
        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = popup_event.pos
                    if self.create_af_button_rect.collidepoint(mx, my) and len(self.base.air_operations_tracker.ready) > 0:
                        # Create an air formation using the next available number
                        af_number = self._get_next_airformation_number()
                        if af_number is not None:
                            airformation = self.base.create_air_formation(af_number)
                            self.created_air_formations.append(airformation)
                        else:
                            self.last_airformation = None
                        self.draw()  # Redraw to show the new air formation
                        return
                    else:
                        waiting = False
                elif popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()


    def _get_next_airformation_number(self):
            return 1
    

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