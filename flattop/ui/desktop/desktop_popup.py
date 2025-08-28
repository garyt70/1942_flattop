
import sys
import pygame

from flattop.hex_board_game_model import Hex, Piece
from flattop.operations_chart_models import AirFormation, Base, TaskForce
from flattop.ui.desktop.airformation_ui import AirFormationUI
from flattop.ui.desktop.base_ui import BaseUIDisplay
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.weather_model import CloudMarker

def show_observation_report_popup(desktop, report, pos=None):
    """
    Displays a popup window with the observation report result.
    Args:
        desktop: The desktop UI object (must have .screen attribute)
        report: The dict returned by report_observation()
        pos: Optional (x, y) tuple for popup position. Defaults to center.
    """
    screen = desktop.screen
    win_width, win_height = screen.get_size()
    margin = 16
    font = pygame.font.SysFont(None, 24)

    # Prepare lines for display
    lines = []
    if not report or not isinstance(report, dict):
        lines = ["No observation data."]
    else:
        for key, value in report.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    if isinstance(item, (tuple, list)):
                        lines.append("  - " + ", ".join(str(x) for x in item))
                    else:
                        lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")

    text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
    popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
    popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2

    # Default to center if no pos
    if pos is None:
        popup_rect = pygame.Rect(
            win_width // 2 - popup_width // 2,
            win_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )
    else:
        x, y = pos
        popup_rect = pygame.Rect(
            x,
            y,
            popup_width,
            popup_height
        )

    # Draw popup background and border
    pygame.draw.rect(screen, (50, 50, 50), popup_rect)
    pygame.draw.rect(screen, (200, 200, 200), popup_rect, 2)

    # Render each line of text
    y = popup_rect.top + margin
    for ts in text_surfaces:
        text_rect = ts.get_rect()
        text_rect.topleft = (popup_rect.left + margin, y)
        screen.blit(ts, text_rect)
        y += ts.get_height() + margin // 2

    pygame.display.flip()

    # Wait for user to click or press a key to close popup
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False



def draw_turn_info_popup(desktop):
    # Draws the current day, hour, phase, and initiative in the bottom right corner
        font = pygame.font.SysFont(None, 28)
        day = desktop.turn_manager.current_day
        hour = desktop.turn_manager.current_hour
        phase = desktop.turn_manager.current_phase if hasattr(desktop.turn_manager, "current_phase") else ""
        initiative = getattr(desktop.turn_manager, "side_with_initiative", None)
        initiative_text = f"Initiative: {initiative}" if initiative else ""
        text = f"Day: {day}  Hour: {hour:02d}:00"
        phase_text = f"Phase: {phase}"

        text_surf = font.render(text, True, (255, 255, 255))
        phase_surf = font.render(phase_text, True, (255, 255, 0))
        initiative_surf = font.render(initiative_text, True, (0, 255, 255)) if initiative_text else None

        text_rect = text_surf.get_rect()
        phase_rect = phase_surf.get_rect()
        initiative_rect = initiative_surf.get_rect() if initiative_surf else None

        win_width, win_height = desktop.screen.get_size()
        margin = 24
        spacing = 6

        # Stack initiative above phase, phase above time
        if initiative_surf:
            initiative_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing - phase_rect.height - spacing)
            phase_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing)
        else:
            phase_rect.bottomright = (win_width - margin, win_height - margin - text_rect.height - spacing)
        text_rect.bottomright = (win_width - margin, win_height - margin)

        # Draw semi-transparent backgrounds for readability
        bg_rects = []
        if initiative_surf:
            bg_rect_initiative = pygame.Rect(
            initiative_rect.left - 8, initiative_rect.top - 4,
            initiative_rect.width + 16, initiative_rect.height + 8
            )
            bg_rects.append(bg_rect_initiative)
        bg_rect_phase = pygame.Rect(
            phase_rect.left - 8, phase_rect.top - 4,
            phase_rect.width + 16, phase_rect.height + 8
        )
        bg_rect_time = pygame.Rect(
            text_rect.left - 8, text_rect.top - 4,
            text_rect.width + 16, text_rect.height + 8
        )
        bg_rects.extend([bg_rect_phase, bg_rect_time])

        for bg_rect in bg_rects:
            pygame.draw.rect(desktop.screen, (30, 30, 30, 180), bg_rect)

        if initiative_surf:
            desktop.screen.blit(initiative_surf, initiative_rect)
        desktop.screen.blit(phase_surf, phase_rect)
        desktop.screen.blit(text_surf, text_rect)

        # Save for click detection (use the union of all rects)
        rects = [text_rect, phase_rect]
        if initiative_rect:
            rects.append(initiative_rect)
        desktop._turn_info_rect = rects[0].unionall(rects[1:])


def draw_game_model_popup(desktop, piece, pos):
    """
    Draws a popup for the given piece at the specified position.
    """
    #TODO: consider using pygame menu for popups and dialogs as well as menu option
        # Calculate maximum popup size (20% of display area, but allow up to 90% of height)
    win_width, win_height = desktop.screen.get_size()
    margin = 10

    if isinstance(piece.game_model, Base):
        # If the piece is a Base, use the BaseUIDisplay to render it
        # This allows for a more detailed and interactive display of the Base piece
        
        baseUI = BaseUIDisplay( piece.game_model, desktop.screen)
        baseUI.air_op_chart = desktop.board.players[piece.side]
        baseUI.turn_manager = desktop.turn_manager
        baseUI.draw()
        baseUI.handle_events()
        for af in baseUI.created_air_formations:
            desktop.board.add_piece(Piece(
                name=f"AF#{af.number}",  #need to fix this or decide if AirFormation number are needed
                side=piece.game_model.side,
                position=piece.position,
                gameModel=af))
        return
    
    
    elif isinstance(piece.game_model, TaskForce):
        # If the piece is a TaskForce, use the TaskForceScreen to render it
        # This allows for a more detailed and interactive display of the TaskForce piece
        try:
            tf_screen = TaskForceScreen(piece.game_model)
            tf_screen.air_ops_chart = desktop.board.players[piece.side]
            tf_screen.draw(desktop.screen)
            pygame.display.flip()
            # Wait for user to close the TaskForce screen
            waiting = True
            while waiting:
                for popup_event in pygame.event.get():
                    tf_screen.handle_event(popup_event)
                    if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                        waiting = False
                        if popup_event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
            #create a piece for any created air formations
            if tf_screen.base_dialog:
                for af in tf_screen.base_dialog.created_air_formations:
                    desktop.board.add_piece(Piece(
                        name=f"AF#{af.number}",  #TODO: need to fix this or decide if AirFormation number are needed
                        side=piece.game_model.side,
                        position=piece.position,
                        gameModel=af))
                    
            return
        except ImportError:
            pass  # Fallback to default popup if import fails
    elif isinstance(piece.game_model, AirFormation):
        # If the piece is an AirFormation, use the AircraftDisplay to render it
        # This allows for a more detailed and interactive display of the AirFormation piece
        airformation_ui = AirFormationUI(piece.game_model, desktop.screen)
        airformation_ui.draw()
        airformation_ui.handle_events()
        
        return
        
    else:
        # Prepare text for popup
        text= f"{piece}"

        # Prepare font
        font = pygame.font.SysFont(None, 24)
        lines = text.split('\n')
        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]

        # Calculate popup size based on the widest line and total height
        popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
        popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2

        # Position popup at top right
        popup_rect = pygame.Rect(
            win_width - popup_width - margin,
            margin,
            popup_width,
            popup_height
        )

        # Draw popup background and border
        pygame.draw.rect(desktop.screen, (50, 50, 50), popup_rect)
        pygame.draw.rect(desktop.screen, (200, 200, 200), popup_rect, 2)

        # Render each line of text
        y = popup_rect.top + margin
        for ts in text_surfaces:
            text_rect = ts.get_rect()
            text_rect.topleft = (popup_rect.left + margin, y)
            desktop.screen.blit(ts, text_rect)
            y += ts.get_height() + margin // 2

    pygame.display.flip()

    # Wait for user to click or press a key to close popup
    waiting = True
    while waiting:
        for popup_event in pygame.event.get():
            if popup_event.type == pygame.MOUSEBUTTONDOWN or popup_event.type == pygame.KEYDOWN or popup_event.type == pygame.QUIT:
                waiting = False
                if popup_event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

def draw_piece_selection_popup(surface, pieces:list[Piece], pos:Hex):
        # Display a popup with a list of pieces and let the user select one
        win_width, win_height = surface.get_size()
        margin = 10
        font = pygame.font.SysFont(None, 24)
        # Show: Piece name, type, and side
        # Filter out CloudMarker pieces
        filtered_pieces = [piece for piece in pieces if not isinstance(piece, CloudMarker)]
        lines = [
            f"{i+1}: {getattr(piece, 'name', str(piece))} | {piece.game_model.__class__.__name__} | {getattr(piece, 'side', '')}"
            for i, piece in enumerate(filtered_pieces)
        ]
        pieces = filtered_pieces  # Update pieces to match lines for selection logic below
        text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
        popup_width = max(ts.get_width() for ts in text_surfaces) + 2 * margin
        popup_height = sum(ts.get_height() for ts in text_surfaces) + (len(text_surfaces) + 1) * margin // 2
        popup_rect = pygame.Rect(
            win_width // 2 - popup_width // 2,
            win_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )
        pygame.draw.rect(surface, (50, 50, 50), popup_rect)
        pygame.draw.rect(surface, (200, 200, 200), popup_rect, 2)
        y = popup_rect.top + margin
        for ts in text_surfaces:
            text_rect = ts.get_rect()
            text_rect.topleft = (popup_rect.left + margin, y)
            surface.blit(ts, text_rect)
            y += ts.get_height() + margin // 2
        pygame.display.flip()

        # Wait for user to click on a line or press a number key
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(pieces):
                            return pieces[idx]
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if popup_rect.collidepoint(mx, my):
                        rel_y = my - popup_rect.top - margin
                        line_height = text_surfaces[0].get_height() + margin // 2
                        idx = rel_y // line_height
                        if 0 <= idx < len(pieces):
                            return pieces[idx]
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return None