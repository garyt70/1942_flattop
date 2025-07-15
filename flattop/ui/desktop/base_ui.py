import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from flattop.operations_chart_models import Base, AirOperationsTracker, AirOperationsConfiguration, Aircraft, AircraftOperationsStatus, AircraftCombatData, AircraftFactory, AircraftType, AirOperationsChart, AirFormation

class AircraftOperationChartCommandWidget:
    def __init__(self, surface, x, y, aircraft:Aircraft):
        self.from_aircraft = aircraft
        self.to_aircraft :Aircraft = None
        self.pos_x = x
        self.pos_y = y
        self.surface = surface
        self.btn_rect = pygame.Rect(x, y, 30, 30)

    def draw(self):
        """
        Draws a button and counter.
        The button adds one to_aircraft.count and subtracts one from from_aircraft.count.
        If to_aircraft does not exist then create a copy of from_aircraft and set count to one.
        to_aircraft_list: list to hold destination aircraft (optional, for updating)
        to_aircraft_type: AircraftType to match in to_aircraft_list (optional)
        """
        # Draw the button
        pygame.draw.rect(self.surface, (0, 200, 0), self.btn_rect)
        font = pygame.font.SysFont(None, 24)
        btn_label = font.render("+", True, (255, 255, 255))
        self.surface.blit(btn_label, (self.pos_x + 8, self.pos_y + 2))

        # Draw the current count
        if self.to_aircraft is not None:
            count_label = font.render(str(self.to_aircraft.count), True, (255, 255, 0))
            self.surface.blit(count_label, (self.pos_x + 35, self.pos_y + 5))

    def handle_click(self):

        change_value = 0

        if self.from_aircraft.count > 0:
            # Find or create to_aircraft
            if self.to_aircraft is None:
                self.to_aircraft = self.from_aircraft.copy()
                self.to_aircraft.count = 0

            # Update counts
            self.from_aircraft.count -= 1
            self.to_aircraft.count += 1
            change_value = 1
        
        # Draw the current count
        if self.to_aircraft is not None:
            font = pygame.font.SysFont(None, 24)
            count_label = font.render(str(self.to_aircraft.count), True, (255, 255, 0), (50, 50, 50))
            self.surface.blit(count_label, (self.pos_x + 35, self.pos_y + 5))
        
        return change_value

    def collidepoint(self, mx, my):
        return self.btn_rect.collidepoint(mx, my)
 

class AircraftDisplay:
    columns = [260, 320, 380, 440, 500, 560, 620, 680, 740, 800, 860, 920, 980, 1040, 1100, 1160]

    def __init__(self):
        pass

    @staticmethod
    def draw_aircraft(surface, aircraft: Aircraft, x, y):
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
        surface.blit(font.render(f"{aircraft.range_factor} ({aircraft.range_remaining})", True, (255, 255, 255)), (x + columns[15], y))
        
        y += 20

        return y + 22 
    
    @staticmethod
    def draw_command_btn(surface, aircraft, x, y):
        btn = AircraftOperationChartCommandWidget(surface, x, y, aircraft)
        btn.draw()
        return btn

    @staticmethod
    def draw_aircraft_with_command_btn(surface, aircraft, x, y):
        #this is drawn button first because drawing the aircraft increment y by number of 
        # aircraft which will result in button being in wrong place
        btn = AircraftDisplay.draw_command_btn(surface, aircraft, x + AircraftDisplay.columns[15] + 60 , y)
        y = AircraftDisplay.draw_aircraft(surface, aircraft, x, y)
        return y, btn

    @staticmethod
    def draw_aircraft_list_header(surface, aircraft: Aircraft, x, y):
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
    

    @staticmethod  
    def draw_aircraft_list_with_btn(surface, aircraft_list, x, y):
        
        """
        Draws a list of AirCraft objects on the surface at the specified position.
        """
        btn_list = []
        for ac in aircraft_list:
            y, btn = AircraftDisplay.draw_aircraft_with_command_btn(surface, ac, x, y)
            btn_list.append(btn)
        return y, btn_list

class AirOperationsTrackerDisplay:
    columns = [200, 260, 320, 380, 440, 500, 560, 620, 680, 740, 800, 860, 920, 980]

    def __init__(self, tracker: AirOperationsTracker, config: AirOperationsConfiguration ,surface, pos=(10, 90)):
        self.tracker = tracker
        self.config = config
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)
        self.ready_btn_list = []
        self.just_landed_btn_list = []


    def draw_aircraft_list(self, aircraft_list, x, y):
        return AircraftDisplay.draw_aircraft_list(self.surface, aircraft_list, x, y)

    def draw_aircraft(self, aircraft: Aircraft, x, y):
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
        #y = self.draw_aircraft_list(self.tracker.ready, x, y)
        y, btn_list = AircraftDisplay.draw_aircraft_list_with_btn(self.surface, self.tracker.ready, x, y )
        self.ready_btn_list = btn_list
        
        self.surface.blit(self.font.render("Readying", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.readying, x, y)
        
        self.surface.blit(self.font.render("Just Landed", True, (200, 200, 0)), (x, y))
        y += 25
        y, btn_list = AircraftDisplay.draw_aircraft_list_with_btn(self.surface, self.tracker.just_landed, x, y )
        self.just_landed_btn_list = btn_list
        

        self.surface.blit(self.font.render("In Flight", True, (200, 200, 0)), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.in_flight, x, y)

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
        self.tracker_display = AirOperationsTrackerDisplay(base.air_operations_tracker, base.air_operations_config, surface)
        self.create_af_button_rect = None  # Button rect for creating air formation
        self.ready_btn_list = [] #list of button for the ready plan list. This is used in create airformation
        self.just_landed_btn_list = [] #list of button for the just landed plan list. This is used to move planes from just landed to readying.
        self.last_airformation = None      # Store the last created air formation
        self.created_air_formations = []  # store the created AirFormations so that the calling code can implement pieces for them
        self.air_op_chart: AirOperationsChart = None #this is required to enable access to the dictionary of air formations.

    def _handle_create_airformation_click(self):
        # Create an air formation using the next available number
        af_number = self._get_next_airformation_number()
        if af_number is not None:
            #airformation = self.base.create_air_formation(af_number)
            airformation = AirFormation(af_number, f"{self.base.name} airformation {af_number}", side=self.base.side)

            btn:AircraftOperationChartCommandWidget
            for btn in self.ready_btn_list:
                if btn.to_aircraft:
                    airformation.add_aircraft(btn.to_aircraft)
                if btn.from_aircraft.count <= 0:
                    self.base.air_operations_tracker.ready.remove(btn.from_aircraft)

            if len(airformation.aircraft) > 0:
                self.created_air_formations.append(airformation)
                self.air_op_chart.air_formations[af_number] = airformation
                self.last_airformation = airformation
                # Reset the temporary launch factor
                self.base.used_launch_factor += self.temp_launch_factor
            self.temp_launch_factor = 0
        else:
            self.last_airformation = None
    
    def _handle_button_click(self, event):
        mx, my = event.pos
        exit :bool = False
        if self.create_af_button_rect.collidepoint(mx, my) and self.base.used_launch_factor + self.temp_launch_factor <= self.base.air_operations_config.launch_factor_max:
            self._handle_create_airformation_click()
            # # Redraw to show the new air formation  
            pygame.display.flip()
            exit = True      
        elif self.action_ready_factor_button_rect.collidepoint(mx, my) and self.base.used_ready_factor + self.temp_ready_factor <= self.base.air_operations_config.ready_factors:
            # Handle action ready factor button click
            # This button is used to handle the logic for moving aircraft from just landed to readying.
            #loop through the just landed btns and move aircraft to readying
            for btn in self.just_landed_btn_list:
                if btn.to_aircraft:
                    #move the aircraft from just landed to readying
                    self.base.air_operations_tracker.readying.append(btn.to_aircraft)
                    if btn.from_aircraft.count <=0:
                        self.base.air_operations_tracker.just_landed.remove(btn.from_aircraft)
                    btn.to_aircraft = None

            self.base.used_ready_factor = self.base.used_ready_factor + self.temp_ready_factor
            pygame.display.flip()
            exit = True
        else:
            exit = True # assume exiting the screen unless button is clicked.
            #see if any of the ready button have been clicked
            btn : AircraftOperationChartCommandWidget
            for btn in self.ready_btn_list:
                #need to think of a better way to handle zero ready facotr to prevent need for loop
                if btn.collidepoint(mx, my):
                    exit = False
                    if self.base.used_launch_factor + self.temp_launch_factor <= self.base.air_operations_config.launch_factor_max:
                        if btn.handle_click() > 0:
                            #reducing the available_ready_factor here causes an issue because its possible to not create an airformation 
                            # which is really where the available ready/launch factor is affected. The lauch factor is only affected when an airformation is created.
                            self.temp_launch_factor += 1
                            #redraw the launch factor
                            self.surface.blit(pygame.font.SysFont(None, 26).render(f"Used LF({self.base.used_launch_factor + self.temp_launch_factor})", 
                                                                    True, (255, 255, 255),(50, 50, 50)), (900, 65))
                            pygame.display.flip()
                    break
            #see if any of the just landed button have been clicked
            for btn in self.just_landed_btn_list:
                if btn.collidepoint(mx, my):
                    exit = False
                    if btn.handle_click()> 0:
                        self.temp_ready_factor += 1
                        #redraw the ready factor value
                        self.surface.blit(
                                pygame.font.SysFont(None, 24).render(f"({self.base.used_ready_factor + self.temp_ready_factor})", 
                                                                    True, (255, 255, 255),(50, 50, 50)), (250, 65))
                        pygame.display.flip()
                    break
        return exit

    
    def _handle_events(self):
        waiting = True
        self.temp_launch_factor = 0
        self.temp_ready_factor = 0

        while waiting:
            for popup_event in pygame.event.get():
                if popup_event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = not self._handle_button_click(popup_event)     
                elif popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                    waiting = False
                    if popup_event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
    def draw(self):

        win_width, win_height = self.surface.get_size()
        margin = 10

        # Draw a popup background for the takforce details
        font = pygame.font.SysFont(None, 24)
        header_font = pygame.font.SysFont(None, 28, bold=True)
        popup_width = int(win_width * 0.9)
        popup_height = int(win_height * 0.9)
        popup_rect = pygame.Rect(
            10,
            10,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.surface, (50, 50, 50), popup_rect)
        pygame.draw.rect(self.surface, (200, 200, 200), popup_rect, 2)

        self.config_display.draw()
        self.tracker_display.draw()
        self.surface.blit(pygame.font.SysFont(None, 26).render(f"({self.base.used_ready_factor})", 
                                                                 True, (255, 255, 255),(50, 50, 50)), (250, 65))
        self.surface.blit(pygame.font.SysFont(None, 26).render(f"Used LF({self.base.used_launch_factor})", 
                                                                 True, (255, 255, 255),(50, 50, 50)), (900, 65))
        #self.surface.blit(self.font.render("LF (Max)", True, (200, 200, 0)), (x + 800, y))
        self.ready_btn_list = self.tracker_display.ready_btn_list
        self.just_landed_btn_list = self.tracker_display.just_landed_btn_list


         # Draw the "Create Air Formation" button
        font = pygame.font.SysFont(None, 28)
        button_text = "Create Air Formation"
        btn_surf = font.render(button_text, True, (0, 0, 0))
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = popup_rect.x, popup_height - btn_height - 30
        self.create_af_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, (200, 200, 0), self.create_af_button_rect)
        pygame.draw.rect(self.surface, (255, 255, 255), self.create_af_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))

        # draw the "Action Ready Factor" button
        btn_text = "Action Ready Factor"
        btn_surf = font.render(btn_text, True, (0, 0, 0))
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = popup_rect.x + 220, popup_height - btn_height - 30
        self.action_ready_factor_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, (200, 200, 0), self.action_ready_factor_button_rect)
        pygame.draw.rect(self.surface, (255, 255, 255), self.action_ready_factor_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))


        pygame.display.flip()

        self._handle_events()

       


    def _get_next_airformation_number(self):
            return self.air_op_chart.get_empty_formation_number()
    

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