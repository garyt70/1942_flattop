
import sys
import pygame

from flattop.hex_board_game_model import Hex, Piece
from flattop.operations_chart_models import AirFormation, Base, TaskForce
from flattop.ui.desktop.airformation_ui import AirFormationUI
from flattop.ui.desktop.base_ui import BaseUIDisplay
from flattop.ui.desktop.taskforce_ui import TaskForceScreen
from flattop.weather_model import CloudMarker
from flattop.game_engine import perform_turn_start_actions

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

def show_turn_change_popup(desktop_ui):
    # Display a scrollable popup listing all pieces that can move but have not moved yet,
    # and allow the user to advance the phase or turn only if all phases are complete.
    win_width, win_height = desktop_ui.screen.get_size()
    margin = 16
    font = pygame.font.SysFont(None, 24)
    header_font = pygame.font.SysFont(None, 28, bold=True)

    # Get current phase and phase list from TurnManager
    current_phase = desktop_ui.turn_manager.current_phase
    phase_list = desktop_ui.turn_manager.PHASES
    phase_idx = phase_list.index(current_phase) if current_phase in phase_list else 0

    # Filter pieces that can move and have not moved (for this phase, if applicable)
    unmoved = desktop_ui._get_pieces_for_turn_change()
    lines = [
    f"{i+1}: {getattr(piece, 'name', str(piece))} | {piece.game_model.__class__.__name__} | {getattr(piece, 'side', '')}"
    for i, piece in enumerate(unmoved)
    ]
    if not lines:
        lines = ["No pieces can act this phase."]

    text_surfaces = [font.render(line, True, (255, 255, 255)) for line in lines]
    header_surf = header_font.render(f"Phase: {current_phase}", True, (255, 255, 0))
    # Button text depends on whether this is the last phase
    if phase_idx == len(phase_list) - 1:
        next_phase_text = "Advance Turn"
    else:
        next_phase_text = f"Advance Phase ({phase_list[phase_idx+1]})"
    next_phase_surf = header_font.render(next_phase_text, True, (0, 255, 0))

    # Add Combat Results button
    combat_results_text = "Combat Results"
    combat_results_surf = header_font.render(combat_results_text, True, (0, 180, 255))

    popup_width = max([header_surf.get_width(), next_phase_surf.get_width(), combat_results_surf.get_width()] + [ts.get_width() for ts in text_surfaces]) + 2 * margin
    visible_lines = min(10, len(text_surfaces))
    line_height = font.get_height() + 4
    popup_height = header_surf.get_height() + next_phase_surf.get_height() + combat_results_surf.get_height() + visible_lines * line_height + 6 * margin
    popup_rect = pygame.Rect(
    win_width // 2 - popup_width // 2,
    win_height // 2 - popup_height // 2,
    popup_width,
    popup_height
    )
    scroll_offset = 0

    needs_redraw = True
    running = True
    while running:
        if needs_redraw:
            desktop_ui.draw()  # Redraw board behind popup
            pygame.draw.rect(desktop_ui.screen, (50, 50, 50), popup_rect)
            pygame.draw.rect(desktop_ui.screen, (200, 200, 200), popup_rect, 2)
            # Draw header
            y = popup_rect.top + margin
            desktop_ui.screen.blit(header_surf, (popup_rect.left + margin, y))
            y += header_surf.get_height() + margin // 2

            # Draw Advance Phase/Turn button (disabled if unmoved pieces remain)
            next_phase_rect = next_phase_surf.get_rect(topleft=(popup_rect.left + margin, y))
            if unmoved:
                pygame.draw.rect(desktop_ui.screen, (80, 80, 80), next_phase_rect.inflate(12, 8))  # Disabled look
                desktop_ui.screen.blit(next_phase_surf, next_phase_rect.topleft)
            else:
                pygame.draw.rect(desktop_ui.screen, (30, 80, 30), next_phase_rect.inflate(12, 8))
                desktop_ui.screen.blit(next_phase_surf, next_phase_rect.topleft)
            y += next_phase_rect.height + margin // 2

            # Draw Combat Results button
            combat_results_rect = combat_results_surf.get_rect(topleft=(popup_rect.left + margin, y))
            pygame.draw.rect(desktop_ui.screen, (30, 30, 120), combat_results_rect.inflate(12, 8))
            desktop_ui.screen.blit(combat_results_surf, combat_results_rect.topleft)
            y += combat_results_rect.height + margin // 2

            # Draw visible lines with scrolling
            for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
                ts = text_surfaces[i]
                text_rect = ts.get_rect()
                text_rect.topleft = (popup_rect.left + margin, y)
                desktop_ui.screen.blit(ts, text_rect)
                y += line_height

            # Draw scroll indicators if needed
            if scroll_offset > 0:
                up_arrow = font.render("^", True, (255, 255, 255))
                desktop_ui.screen.blit(up_arrow, (popup_rect.right - margin - up_arrow.get_width(), popup_rect.top + margin))
            if scroll_offset + visible_lines < len(text_surfaces):
                down_arrow = font.render("v", True, (255, 255, 255))
                desktop_ui.screen.blit(down_arrow, (popup_rect.right - margin - down_arrow.get_width(), popup_rect.bottom - margin - down_arrow.get_height()))

            pygame.display.flip()
            needs_redraw = False

        event = pygame.event.wait()
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return
            elif event.key == pygame.K_DOWN and scroll_offset + visible_lines < len(text_surfaces):
                scroll_offset += 1
                needs_redraw = True
            elif event.key == pygame.K_UP and scroll_offset > 0:
                scroll_offset -= 1
                needs_redraw = True
            elif pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1 + scroll_offset
                if 0 <= idx < len(unmoved):
                    desktop_ui.show_piece_menu(unmoved[idx], (popup_rect.left + margin, popup_rect.top + margin))
                    return
            elif event.key == pygame.K_c:
                # Keyboard shortcut for Combat Results
                desktop_ui._show_combat_results_list()
                needs_redraw = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # Check if click is on Advance Phase/Turn button (only if no unmoved pieces)
            if next_phase_rect.collidepoint(mx, my):
                # Advance to next phase, this will also handle turn change if at last phase
                desktop_ui.turn_manager.next_phase()
                match desktop_ui.turn_manager.current_phase_index:
                    case 0:
                        print("Starting a new turn")
                        perform_turn_start_actions(board=desktop_ui.board, turn_manager=desktop_ui.turn_manager, weather_manager=desktop_ui.weather_manager)
                        desktop_ui.computer_opponent.start_new_turn()
                        desktop_ui.computer_opponent.perform_observation()
                        desktop_ui.computer_opponent.perform_turn()
                        print("Air Operations Phase")
                    case 1:
                        print("Task Force Movement Phase")
                        desktop_ui.computer_opponent.perform_turn()
                    case 2:
                        print("Plane Movement Phase")
                        desktop_ui.computer_opponent.perform_turn()
                    case 3:
                        print("Combat Phase")
                        desktop_ui.turn_manager.last_combat_result = None
                        desktop_ui.computer_opponent.perform_turn()
                        desktop_ui.show_combat_results(desktop_ui.turn_manager.last_combat_result, event.pos)
                return
            # Check if click is on Combat Results button
            if combat_results_rect.collidepoint(mx, my):
                desktop_ui._show_combat_results_list()
                needs_redraw = True
                continue
            # Check if click is on a piece line
            for i in range(scroll_offset, min(scroll_offset + visible_lines, len(text_surfaces))):
                ts = text_surfaces[i]
                text_rect = ts.get_rect(topleft=(popup_rect.left + margin, popup_rect.top + margin + header_surf.get_height() + margin // 2 + next_phase_rect.height + margin // 2 + combat_results_rect.height + margin // 2 + (i - scroll_offset) * line_height))
                if text_rect.collidepoint(mx, my) and len(unmoved) > 1:
                    desktop_ui.show_piece_menu(unmoved[i], event.pos)
                    return
            # Scroll up/down if click on arrows
            if scroll_offset > 0:
                up_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.top + margin, 20, 20)
                if up_arrow_rect.collidepoint(mx, my):
                    scroll_offset -= 1
                    needs_redraw = True
            if scroll_offset + visible_lines < len(text_surfaces):
                down_arrow_rect = pygame.Rect(popup_rect.right - margin - 20, popup_rect.bottom - margin - 20, 20, 20)
                if down_arrow_rect.collidepoint(mx, my):
                    scroll_offset += 1
                    needs_redraw = True

from flattop.ui.desktop.combat_results_ui import CombatResultsList
def _show_combat_results_list(desktop_ui):
    # Show the CombatResultsList popup (if available)
    try:
        ui = CombatResultsList(desktop_ui.turn_manager.combat_results_history, desktop_ui.screen)
        ui.run()
    except Exception as e:
        print("CombatResultsList not available or error:", e)
