import sys
import os
import pygame

# Ensure the parent directory is in sys.path for module discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..','..')))

from flattop.operations_chart_models import Base, AirOperationsTracker, AirOperationsConfiguration, Aircraft, AircraftOperationsStatus, AircraftCombatData, AircraftFactory, AircraftType, AirOperationsChart, AirFormation

# Color constants
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GRAY = (220, 220, 220)
COLOR_YELLOW = (200, 200, 0)
COLOR_GREEN = (0, 200, 0)
COLOR_DARK_GREEN = (0, 100, 200)
COLOR_BG = (50, 50, 50)
COLOR_BORDER = (200, 200, 200)
COLOR_BTN_TEXT = (0, 0, 0)
COLOR_BTN_BG = (200, 200, 0)
COLOR_BTN_BORDER = (255, 255, 255)
COLOR_BTN_CLOSE_BG = (200, 200, 0)
COLOR_BTN_CLOSE_BORDER = (255, 255, 255)
COLOR_BTN_CLOSE_TEXT = (0, 0, 0)
COLOR_BTN_READY_FACTOR_BG = (200, 200, 0)
COLOR_BTN_READY_FACTOR_BORDER = (255, 255, 255)
COLOR_BTN_READY_FACTOR_TEXT = (0, 0, 0)
COLOR_FONT_HEADER = (255, 255, 255)
COLOR_FONT_HEADER_BOLD = (255, 255, 0)
COLOR_FONT_AIRCRAFT = (180, 220, 255)
COLOR_FONT_COUNT = (255, 255, 0)
COLOR_FONT_COMBAT = (255, 255, 255)
COLOR_FONT_MOVE = (255, 255, 255)
COLOR_FONT_RANGE = (255, 255, 255)
COLOR_FONT_ARMAMENT = (255, 255, 255)
COLOR_FONT_BG = (50, 50, 50)

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

        if self.to_aircraft is None:
                self.to_aircraft = self.from_aircraft.copy()
                self.to_aircraft.count = 0

        if self.to_aircraft.count < self.from_aircraft.count:
            # Update counts.  Don't want to update from_count until action to create airformation performed
            #self.from_aircraft.count -= 1
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
 
class AircraftAirFormationCommandWidget:
    def __init__(self, surface, aircraft:Aircraft, x, y):
        self.aircraft=aircraft
        self.pos_x = x
        self.pos_y = y
        self.surface = surface
        self._height_btn_rect = None
        self._attach_type_btn_rect = None

    def draw(self):
        columns = [self.pos_x, self.pos_x + 60, self.pos_x + 100]
        self._height_btn_rect = pygame.Rect(columns[1], self.pos_y, 40, 20)
        self._attach_type_btn_rect = pygame.Rect(columns[2], self.pos_y, 40, 20)
        font = pygame.font.SysFont(None, 18)

       #armament display
        self.surface.blit(font.render(str(self.aircraft.armament), True, COLOR_FONT_ARMAMENT), (columns[0], self.pos_y))
       
        # Draw the height button
        pygame.draw.rect(self.surface, (0, 200, 0), self._height_btn_rect)
        
        btn_label = font.render(f"{self.aircraft.height}", True, (255, 255, 255))
        self.surface.blit(btn_label, (columns[1], self.pos_y + 2))

        #draw button for attack type
        attack_type = self.aircraft.attack_type
        pygame.draw.rect(self.surface, (0, 200, 0), self._attach_type_btn_rect)
        font = pygame.font.SysFont(None, 18)
        btn_label = font.render(f"{attack_type}", True, (255, 255, 255))
        self.surface.blit(btn_label, (columns[2], self._attach_type_btn_rect.y + 2))

    def _handle_height_click(self):
        if self.aircraft.height == "High":
            self.aircraft.height = "Low"
        else:
            self.aircraft.height = "High"

    def _handle_attack_type_click(self):
        # torpedo attach is handled by armament type in combat resolution
        if self.aircraft.attack_type == "Dive":
            self.aircraft.attack_type = "Level"
        elif self.aircraft.attack_type == "Level":
            self.aircraft.attack_type = "Dive"

    def handle_click(self, event=None):

        mx, my = pygame.mouse.get_pos()

        #check which button was clicked
        if self._height_btn_rect.collidepoint(mx, my):
            self._handle_height_click()
        elif self._attach_type_btn_rect.collidepoint(mx, my):
            self._handle_attack_type_click()

        self.draw()


    def collidepoint(self, mx, my):
        # Returns True if either button is clicked
        return self._height_btn_rect.collidepoint(mx, my) or self._attach_type_btn_rect.collidepoint(mx, my)

class AircraftOperationChartCommandWidgetWithArmament(AircraftOperationChartCommandWidget):
    """
    Extends AircraftOperationChartCommandWidget to add an armament button for aircraft.
    The armament button allows the user to select or display the armament of the aircraft.
    Now supports cycling through GP, AP, and Torpedo.
    """

    ARMAMENT_OPTIONS = ["GP", "AP", "Torpedo", None]  # None represents no armament

    def __init__(self, surface, x, y, aircraft: Aircraft):
        super().__init__(surface, x, y, aircraft)
        # Place the armament button to the right of the main button
        self.armament_btn_rect = pygame.Rect(x + 40, y, 30, 30)
        self.selected_armament = getattr(aircraft, "armament", None)
        if self.selected_armament not in self.ARMAMENT_OPTIONS:
            self.selected_armament = self.ARMAMENT_OPTIONS[0]


        
    def draw(self):
        # Draw the main button and count
        super().draw()
        # Draw the armament button
        pygame.draw.rect(self.surface, (0, 100, 200), self.armament_btn_rect)
        font = pygame.font.SysFont(None, 20)
        arm_label = font.render("-", True, (255, 255, 255))
        # Optionally, display selected armament
        if self.selected_armament:
            arm_label = font.render(str(self.selected_armament), True, (255, 255, 0))
        # Draw the armament label on the button
        self.surface.blit(arm_label, (self.armament_btn_rect.x + 8, self.armament_btn_rect.y + 5))

    def handle_armament_click(self):
        # Cycle through the armament options
        idx = self.ARMAMENT_OPTIONS.index(self.selected_armament)
        idx = (idx + 1) % len(self.ARMAMENT_OPTIONS)
        self.selected_armament = self.ARMAMENT_OPTIONS[idx]
        # Update the aircraft's armament attribute 
        if self.to_aircraft is not None:
            self.to_aircraft.armament = self.selected_armament
        if self.selected_armament:
            # Redraw the armament button with the new selection
            font = pygame.font.SysFont(None, 20)
            arm_text = font.render(str(self.selected_armament)[:4], True, (255, 255, 0), (50, 50, 50))
            self.surface.blit(arm_text, (self.armament_btn_rect.x + 8, self.armament_btn_rect.y + 5))
            pygame.display.flip()
        

    def handle_click(self, mx=None, my=None):
        # If coordinates are provided, check which button was clicked
        if mx is not None and my is not None:
            if self.armament_btn_rect.collidepoint(mx, my):
                self.handle_armament_click()
                return 0
            elif self.btn_rect.collidepoint(mx, my):
                if self.to_aircraft and self.selected_armament:
                    # Update the armament of the to_aircraft
                    self.to_aircraft.armament = self.selected_armament
                return super().handle_click()
            return 0
        # Default: just handle main button
        return super().handle_click()

    def collidepoint(self, mx, my):
        # Returns True if either button is clicked
        return self.btn_rect.collidepoint(mx, my) or self.armament_btn_rect.collidepoint(mx, my)


class AircraftDisplay:
    columns = [260, 320, 370, 420, 470, 520, 570, 620, 670, 720, 770, 820, 870, 920, 980, 1040, 1100, 1160, 1300, 1360, 1420]

    def __init__(self):
        pass

    @staticmethod
    def draw_aircraft(surface, aircraft: Aircraft, x, y, show_armament=False):
        """
        Draws a single AirCraft object on the surface at the specified position.
        """
        columns = AircraftDisplay.columns
        font = pygame.font.SysFont(None, 22)
             
        ac_type = aircraft.type.name if isinstance(aircraft.type, AircraftType) else str(aircraft.type)
        ac_move=aircraft.move_factor
        ac_text = font.render(f"{ac_type} (#: {aircraft.count} )", True, COLOR_FONT_AIRCRAFT)
        surface.blit(ac_text, (x + 20, y))

        # If the aircraft has a combat data object, display its combat data
        # This includes air-to-air combat, high level bombing, low level bombing, dive bombing
        acd = aircraft.combat_data
        if acd is not None: 
            #air to air
            surface.blit(font.render(str(acd.air_to_air), True, COLOR_FONT_COMBAT), (x + columns[0], y))
            #high Level GP, AP
            surface.blit(font.render(str(acd.level_bombing_high_base_gp), True, COLOR_FONT_COMBAT), (x + columns[1], y))
            surface.blit(font.render(str(acd.level_bombing_high_base_ap), True, COLOR_FONT_COMBAT), (x + columns[2], y))
            #low Level GP, AP
            surface.blit(font.render(str(acd.level_bombing_low_base_gp), True, COLOR_FONT_COMBAT), (x + columns[3], y))
            surface.blit(font.render(str(acd.level_bombing_low_base_ap), True, COLOR_FONT_COMBAT), (x + columns[4], y))
            #dive GP, AP
            surface.blit(font.render(str(acd.dive_bombing_base_gp), True, COLOR_FONT_COMBAT), (x + columns[5], y))
            surface.blit(font.render(str(acd.dive_bombing_base_ap), True, COLOR_FONT_COMBAT), (x + columns[6], y))
            #high Level Ship GP, AP
            surface.blit(font.render(str(acd.level_bombing_high_ship_gp), True, COLOR_FONT_COMBAT), (x + columns[7], y))
            surface.blit(font.render(str(acd.level_bombing_high_ship_ap), True, COLOR_FONT_COMBAT), (x + columns[8], y))
            #low Level Ship GP, AP
            surface.blit(font.render(str(acd.level_bombing_low_ship_gp), True, COLOR_FONT_COMBAT), (x + columns[9], y))
            surface.blit(font.render(str(acd.level_bombing_low_ship_ap), True, COLOR_FONT_COMBAT), (x + columns[10], y))
            #dive Ship GP, AP
            surface.blit(font.render(str(acd.dive_bombing_ship_gp), True, COLOR_FONT_COMBAT), (x + columns[11], y))
            surface.blit(font.render(str(acd.dive_bombing_ship_ap), True, COLOR_FONT_COMBAT), (x + columns[12], y))
            #Torpedo Ship
            surface.blit(font.render(str(acd.torpedo_bombing_ship), True, COLOR_FONT_COMBAT), (x + columns[13], y))
           
        #movement details of aircraft
        surface.blit(font.render(str(aircraft.move_factor), True, COLOR_FONT_MOVE), (x + columns[14], y))
        surface.blit(font.render(f"{aircraft.range_factor} ({aircraft.range_remaining})", True, COLOR_FONT_RANGE), (x + columns[15], y))

        if show_armament:
            surface.blit(font.render(str(aircraft.armament), True, COLOR_FONT_ARMAMENT), (x + columns[17], y))

        #display height - this is done via a widget for AirFormations.
        #surface.blit(font.render(str(aircraft.height), True, COLOR_FONT_ARMAMENT), (x + columns[17], y))

        #display attack type - this is done via a widget for AirFormations.
        
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
        y = AircraftDisplay.draw_aircraft(surface, aircraft, x, y, show_armament= True)
        return y, btn

    @staticmethod
    def draw_aircraft_list_header(surface, aircraft: Aircraft, x, y):
        columns = AircraftDisplay.columns
        font = pygame.font.SysFont(None, 22)

        surface.blit(font.render("vs Base", True, COLOR_FONT_HEADER), (x + columns[1], y))
        surface.blit(font.render("vs Ship", True, COLOR_FONT_HEADER), (x + columns[7], y))
        y += 20

        # Draw headers for the tracker display
        # The headers are for the different types of operations and aircraft combat data
        surface.blit(font.render("Air2Air", True, COLOR_FONT_HEADER), (x + columns[0], y))
        #Base headers
        surface.blit(font.render("High", True, COLOR_FONT_HEADER), (x + columns[1], y))
        surface.blit(font.render("Low", True, COLOR_FONT_HEADER), (x + columns[3], y))
        surface.blit(font.render("Dive", True, COLOR_FONT_HEADER), (x + columns[5], y))

        #Ship headers
        surface.blit(font.render("High ", True, COLOR_FONT_HEADER), (x + columns[7], y))
        surface.blit(font.render("Low ", True, COLOR_FONT_HEADER), (x + columns[9], y))
        surface.blit(font.render("Dive", True, COLOR_FONT_HEADER), (x + columns[11], y))
        surface.blit(font.render("Torpedo", True, COLOR_FONT_HEADER), (x + columns[13], y))
        y += 20

        #now display the GP and AP header text
        #high Level GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[1], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[2], y))
        #low Level GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[3], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[4], y))
        #dive GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[5], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[6], y))
        
        #high Level Ship GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[7], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[8], y))
        #low Level Ship GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[9], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[10], y))
        #dive Ship GP, AP
        surface.blit(font.render("GP", True, COLOR_FONT_HEADER), (x + columns[11], y))
        surface.blit(font.render("AP", True, COLOR_FONT_HEADER), (x + columns[12], y))
        #Torpedo Ship
        surface.blit(font.render("Torpedo", True, COLOR_FONT_HEADER), (x + columns[13], y))
        #movement
        surface.blit(font.render("Move", True, COLOR_FONT_HEADER), (x + columns[14], y))
        surface.blit(font.render("Range", True, COLOR_FONT_HEADER), (x + columns[15], y))

        #armament handled by widget
        #surface.blit(font.render("Armed", True, COLOR_FONT_HEADER), (x + columns[16], y))
        #height handled by widget
        #surface.blit(font.render("Height", True, COLOR_FONT_HEADER), (x + columns[17], y))
        #attack type
        #surface.blit(font.render("Attack", True, COLOR_FONT_HEADER), (x + columns[18], y))

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
    
    @staticmethod  
    def draw_aircraft_list_with_armament_btn(surface, aircraft_list, x, y):
        """
        Draws a list of AirCraft objects on the surface at the specified position.
        """
        btn_list = []
        for ac in aircraft_list:
            btn = AircraftOperationChartCommandWidgetWithArmament(surface, x + AircraftDisplay.columns[15] + 60 , y, ac)
            btn.draw()
            btn_list.append(btn)
            y = AircraftDisplay.draw_aircraft(surface, ac, x, y)

        return y, btn_list
    
    @staticmethod
    def draw_aircraft_list_with_height_btn (surface, aircraft_list, x, y):
        btn_list = []
        for ac in aircraft_list:
            btn = AircraftAirFormationCommandWidget(surface, ac, x + AircraftDisplay.columns[17], y)
            btn.draw()
            btn_list.append(btn)
            y = AircraftDisplay.draw_aircraft(surface, ac, x, y)
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
        self.readying_btn_list = []
        self.used_launch_factor = 0
        self.used_ready_factor = 0


    def draw_aircraft_list(self, aircraft_list, x, y):
        return AircraftDisplay.draw_aircraft_list(self.surface, aircraft_list, x, y)

    def draw_aircraft(self, aircraft: Aircraft, x, y):
        return AircraftDisplay.draw_aircraft(self.surface, aircraft, x, y)

    def draw(self, pos = (10, 90)):
        columns = self.columns
        self.pos = pos
        x, y = self.pos
        title = self.font.render("Air Operations Tracker", True, COLOR_FONT_HEADER)
        self.surface.blit(title, (x, y))
        y += 30

        y = AircraftDisplay.draw_aircraft_list_header(self.surface, None, x, y)   

        self.surface.blit(self.font.render("Ready", True, COLOR_YELLOW), (x, y))
        y += 25
        if self.used_launch_factor < self.config.launch_factor_max:
            y, btn_list = AircraftDisplay.draw_aircraft_list_with_btn(self.surface, self.tracker.ready, x, y )
        else:
            y = AircraftDisplay.draw_aircraft_list(self.surface, self.tracker.ready, x, y )
            btn_list = []   
        self.ready_btn_list = btn_list
        
        self.surface.blit(self.font.render("Readying", True, COLOR_YELLOW), (x, y))
        y += 25
        if self.used_ready_factor < self.config.ready_factors:
            y, btn_list = AircraftDisplay.draw_aircraft_list_with_armament_btn(self.surface, self.tracker.readying, x, y )
        else:
            y = AircraftDisplay.draw_aircraft_list(self.surface, self.tracker.readying, x, y )
            btn_list = []   
        self.readying_btn_list = btn_list
        
        self.surface.blit(self.font.render("Just Landed", True, COLOR_YELLOW), (x, y))
        y += 25
        if self.used_ready_factor < self.config.ready_factors:
            y, btn_list = AircraftDisplay.draw_aircraft_list_with_btn(self.surface, self.tracker.just_landed, x, y )
        else:
            y = AircraftDisplay.draw_aircraft_list(self.surface, self.tracker.just_landed, x, y )
            btn_list = []
        self.just_landed_btn_list = btn_list

        self.surface.blit(self.font.render("In Flight", True, COLOR_YELLOW), (x, y))
        y += 25
        y = self.draw_aircraft_list(self.tracker.in_flight, x, y)

class AirOperationsConfigurationDisplay:
    def __init__(self, config: AirOperationsConfiguration, surface, pos=(10, 10)):
        self.config = config
        self.surface = surface
        self.pos = pos
        self.font = pygame.font.SysFont(None, 24)

    def draw(self, pos=(10, 10)):
        self.pos = pos
        x, y = self.pos
        title = self.font.render("Air Operations Configuration", True, (255, 255, 255))
        self.surface.blit(title, (x, y))
        y += 30

        # Render config headers max capacity, ready_factors, launch_factor_normal, launch_factor_min, launch_factor_max
        self.surface.blit(self.font.render("Max Capacity", True, COLOR_YELLOW), (x, y))
        self.surface.blit(self.font.render("Ready Factors", True, COLOR_YELLOW), (x + 200, y))
        self.surface.blit(self.font.render("LF (Normal)", True, COLOR_YELLOW), (x + 400, y))
        self.surface.blit(self.font.render("LF (Min)", True, COLOR_YELLOW), (x + 600, y))
        self.surface.blit(self.font.render("LF (Max)", True, COLOR_YELLOW), (x + 800, y))
        y += 25

        # Render config values
        self.surface.blit(self.font.render(str(self.config.maximum_capacity), True, (255, 255, 255)), (x, y))
        self.surface.blit(self.font.render(str(self.config.ready_factors), True, (255, 255, 255)), (x + 200, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_normal), True, (255,   255, 255)), (x + 400, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_min), True, (255, 255, 255)), (x + 600, y))
        self.surface.blit(self.font.render(str(self.config.launch_factor_max), True, (255, 255, 255)), (x + 800, y))


class BaseUIDisplay:
    POS_USED_LAUNCH_FACTOR_BOX = (900, 115)
    POS_USED_READY_FACTOR_BOX = (250, 115)
    POS_HEADER_BOX = (10, 60)
    POS_DETAILS_BOX = (10, 175)


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
            # Use base.create_air_formation to create the air formation
            aircraft_list = []
            for btn in self.ready_btn_list:
                if btn.to_aircraft:
                    aircraft_list.append(btn.to_aircraft)
                    # reduce the count of the from_aircraft by to_aircraft.count
                    #btn.from_aircraft.count -= btn.to_aircraft.count
                    self.temp_launch_factor += btn.to_aircraft.count
                    btn.to_aircraft = None  # Clear the to_aircraft after adding to the formation
                    #btn.from_aircraft.count -= 1
                #if btn.from_aircraft.count <= 0:
                #    self.base.air_operations_tracker.ready.remove(btn.from_aircraft)

            if len(aircraft_list) > 0:
                airformation = self.base.create_air_formation(af_number,  aircraft_list)
                airformation.name = f"{self.base.name} airformation {af_number}",
                self.created_air_formations.append(airformation)
                self.air_op_chart.air_formations[af_number] = airformation
                self.last_airformation = airformation
                
            
        else:
            self.last_airformation = None

    def _handle_ready_factor_click(self):
        # Handle action ready factor button click
            # This button is used to handle the logic for moving aircraft from just landed to readying.
            #loop through the just landed btns and move aircraft to readying
            for btn in self.just_landed_btn_list:
                if btn.to_aircraft:
                    #move the aircraft from just landed to readying
                    self.base.air_operations_tracker.set_operations_status(btn.to_aircraft, AircraftOperationsStatus.READYING, btn.from_aircraft)
                    btn.to_aircraft = None

            #loop through the readying btns and move aircraft to ready
            for btn in self.tracker_display.readying_btn_list:
                if btn.to_aircraft:
                    #move the aircraft from readying to ready
                    self.base.air_operations_tracker.set_operations_status(btn.to_aircraft, AircraftOperationsStatus.READY, btn.from_aircraft)
                    btn.to_aircraft = None

            self.temp_ready_factor = 0
            
    def _handle_aircraft_command_btn_click(self, mx, my):
        #see if any of the ready button have been clicked
        btn : AircraftOperationChartCommandWidget
        if self.base.used_launch_factor + self.temp_launch_factor < self.base.air_operations_config.launch_factor_max:
            for btn in self.ready_btn_list:
                #need to think of a better way to handle zero ready facotr to prevent need for loop
                if btn.collidepoint(mx, my):
                    if btn.handle_click() > 0:
                        #reducing the available_ready_factor here causes an issue because its possible to not create an airformation 
                        # which is really where the available ready/launch factor is affected. The lauch factor is only affected when an airformation is created.
                        self.temp_launch_factor += 1
                        #redraw the launch factor
                        self.surface.blit(pygame.font.SysFont(None, 26).render(f"Used LF({self.base.used_launch_factor + self.temp_launch_factor})", 
                                                                True, (255, 255, 255),(50, 50, 50)), BaseUIDisplay.POS_USED_LAUNCH_FACTOR_BOX)
                        pygame.display.flip()
                    break

        if self.base.used_ready_factor + self.temp_ready_factor < self.base.air_operations_config.ready_factors:    
            #see if any of the just landed button have been clicked
            for btn in self.just_landed_btn_list:
                if btn.collidepoint(mx, my):
                    if btn.handle_click()> 0:
                        self.temp_ready_factor += 1
                        #redraw the ready factor value
                        self.surface.blit(
                                pygame.font.SysFont(None, 24).render(f"({self.base.used_ready_factor + self.temp_ready_factor})", 
                                                                    True, (255, 255, 255),(50, 50, 50)), BaseUIDisplay.POS_USED_READY_FACTOR_BOX)
                        pygame.display.flip()
                    break
            #see if any of the readying button have been clicked
            for btn in self.tracker_display.readying_btn_list:
                if btn.collidepoint(mx, my):
                    if btn.handle_click(mx, my) > 0:
                        self.temp_ready_factor += 1
                        #redraw the ready factor value
                        self.surface.blit(
                                pygame.font.SysFont(None, 24).render(f"({self.base.used_ready_factor + self.temp_ready_factor})", 
                                                                    True, (255, 255, 255),(50, 50, 50)), BaseUIDisplay.POS_USED_READY_FACTOR_BOX)
                        pygame.display.flip()
                    break


    def _handle_button_click(self, event):
        mx, my = event.pos
        exit :bool = False
        if self.create_af_button_rect.collidepoint(mx, my) and self.base.used_launch_factor + self.temp_launch_factor <= self.base.air_operations_config.launch_factor_max:
            self._handle_create_airformation_click()
            # # Redraw to show the new air formation  
            self.draw()  # Redraw the display to reflect changes
            pygame.display.flip()     
        elif self.action_ready_factor_button_rect.collidepoint(mx, my) and self.base.used_ready_factor + self.temp_ready_factor <= self.base.air_operations_config.ready_factors:
            self._handle_ready_factor_click()
            self.draw() # Redraw the display to reflect changes
            pygame.display.flip()
        elif self.close_button_rect.collidepoint(mx, my):
            # Handle close button click
            exit = True
        else:
            self._handle_aircraft_command_btn_click(mx, my)
            # If no button was clicked, continue handling events
            
        return exit

    
    def handle_events(self):
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
        popup_width = int(win_width - margin)
        popup_height = int(win_height - margin)
        popup_rect = pygame.Rect(
            10,
            10,
            popup_width,
            popup_height
        )
        pygame.draw.rect(self.surface, COLOR_BG, popup_rect)
        pygame.draw.rect(self.surface, COLOR_BORDER, popup_rect, 2)

        #draw title
        title_text = header_font.render(f"{self.base.name} Air Operations -  (Damage {self.base.damage})", True, COLOR_FONT_HEADER, COLOR_FONT_BG)
        title_rect = title_text.get_rect(center=(popup_rect.centerx, popup_rect.top + 20))
        self.surface.blit(title_text, title_rect)

        # Draw the header text
        self.config_display.draw(pos=BaseUIDisplay.POS_HEADER_BOX)
        self.tracker_display.used_launch_factor = self.base.used_launch_factor + getattr(self, "temp_launch_factor", 0)
        self.tracker_display.used_ready_factor = self.base.used_ready_factor + getattr(self, "temp_ready_factor", 0)
        self.tracker_display.draw(pos=BaseUIDisplay.POS_DETAILS_BOX)
        self.surface.blit(pygame.font.SysFont(None, 26).render(f"({self.base.used_ready_factor})", 
                                                                 True, COLOR_FONT_HEADER, COLOR_FONT_BG), BaseUIDisplay.POS_USED_READY_FACTOR_BOX)
        self.surface.blit(pygame.font.SysFont(None, 26).render(f"Used LF({self.base.used_launch_factor})", 
                                                                 True, COLOR_FONT_HEADER, COLOR_FONT_BG), BaseUIDisplay.POS_USED_LAUNCH_FACTOR_BOX)
        #self.surface.blit(self.font.render("LF (Max)", True, COLOR_YELLOW), (x + 800, y))
        self.ready_btn_list = self.tracker_display.ready_btn_list
        self.just_landed_btn_list = self.tracker_display.just_landed_btn_list


         # Draw the "Create Air Formation" button
        font = pygame.font.SysFont(None, 28)
        button_text = "Create Air Formation"
        btn_surf = font.render(button_text, True, COLOR_BTN_TEXT)
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = popup_rect.x, popup_height - btn_height - 30
        self.create_af_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, COLOR_BTN_BG, self.create_af_button_rect)
        pygame.draw.rect(self.surface, COLOR_BTN_BORDER, self.create_af_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))

        # draw the "Action Ready Factor" button
        btn_text = "Action Ready Factor"
        btn_surf = font.render(btn_text, True, COLOR_BTN_READY_FACTOR_TEXT)
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = popup_rect.x + 220, popup_height - btn_height - 30
        self.action_ready_factor_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, COLOR_BTN_READY_FACTOR_BG, self.action_ready_factor_button_rect)
        pygame.draw.rect(self.surface, COLOR_BTN_READY_FACTOR_BORDER, self.action_ready_factor_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))

        #draw a Close button
        btn_text = "Close"
        btn_surf = font.render(btn_text, True, COLOR_BTN_CLOSE_TEXT)
        btn_width, btn_height = btn_surf.get_width() + 24, btn_surf.get_height() + 12
        btn_x, btn_y = popup_rect.x + 620, popup_height - btn_height - 30
        self.close_button_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)
        pygame.draw.rect(self.surface, COLOR_BTN_CLOSE_BG, self.close_button_rect)
        pygame.draw.rect(self.surface, COLOR_BTN_CLOSE_BORDER, self.close_button_rect, 2)
        self.surface.blit(btn_surf, (btn_x + 12, btn_y + 6))


        pygame.display.flip()



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
        ui.handle_events()
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()