import os
import time
import threading
import queue
import control_panel
import pygame
from EAS2Text import EAS2Text

# Command queue
command_queue = queue.Queue()

# Pages
defaultPages = [["EMERGENCY ALERT DETAILS", "", "", "", "", "", "", "", "", "", "", "", "1/1"]]
alertPages = []

# Page and style tracking
current_page = 0
num_pages = len(defaultPages)
page_display_duration = 7

# Styles
class Style:
    def __init__(self, background, text, border, margin, font):
        self.background = background
        self.text = text
        self.border = border
        self.margin = margin
        self.font = font

style1 = Style((46, 50, 81), (255, 255, 255), (108, 29, 35), (0, 0, 0), "luximb.ttf")
styles = [style1]
current_style_index = 0

# Initialize Pygame hidden at startup
pygame.init()
screen_width, screen_height = 1000, 720
# Do not create window yet
screen = None
pygame.font.init()
font_size = 40
try:
    font = pygame.font.Font(style1.font, font_size)
except:
    font = pygame.font.Font(None, font_size)

# Helper to format pages
def format_eas_message(eas_text):
    import re
    MAX_LINE_LENGTH = 32
    MAX_LINES_PER_PAGE = 13
    eas_text = re.sub(r'; ', '\n', eas_text)
    lines = eas_text.split('\n')
    formatted_lines = []
    for line in lines:
        words = line.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= MAX_LINE_LENGTH:
                current_line += (" " if current_line else "") + word
            else:
                formatted_lines.append(current_line)
                current_line = word
        if current_line:
            formatted_lines.append(current_line)
    pages = []
    total_pages = (len(formatted_lines) + (MAX_LINES_PER_PAGE - 1) - 1) // (MAX_LINES_PER_PAGE - 1)
    for i in range(0, len(formatted_lines), MAX_LINES_PER_PAGE - 1):
        page_content = formatted_lines[i:i + (MAX_LINES_PER_PAGE - 1)]
        while len(page_content) < (MAX_LINES_PER_PAGE - 1):
            page_content.append("")
        page_content.append(f"{len(pages)+1}/{total_pages}")
        pages.append(page_content)
    return pages

# Handle commands
def handle_commands():
    global alertPages, current_page, num_pages
    try:
        while True:
            command = command_queue.get_nowait()
            if command[0] == "DISPLAY_ALERT":
                try:
                    msg = EAS2Text(command[1]["headers"])
                    desc = command[1]["description"]
                    orgText = msg.orgText.replace("An EAS Participant", "A broadcast or cable system")
                    msgFrom = ".\n"
                    if "Message from" not in desc:
                        msgFrom = ".\nMessage from " + msg.callsign + ".\n"
                    text = (str.upper(orgText) + 
                            "\nhas issued " + str.upper(msg.evntText) + 
                            "\nfor the following counties or\nareas:\n" + 
                            ";\n".join(msg.FIPSText) + 
                            ";\nat " + msg.startTime.strftime("%I:%M %p") + 
                            "\non " + str.upper(msg.startTime.strftime("%b %d, %Y")) + 
                            "\nEffective until " + 
                            msg.endTime.strftime("%I:%M %p") + 
                            msgFrom + desc)
                    alertPages = format_eas_message(text)
                    num_pages = len(alertPages)
                    current_page = 0
                    return "ALERT_STARTED"
                except Exception as e:
                    print("Error parsing EAS message:", e)
            elif command[0] == "CLEAR_ALERT":
                return "ALERT_CLEARED"
            command_queue.task_done()
    except queue.Empty:
        pass
    return None

# Start control panel
control_panel.start_control_panel(command_queue)

# Main loop
while True:
    action = handle_commands()
    if action == "ALERT_STARTED":
        # Create windowed screen only when alert starts
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("DASDEC")
        pygame.mouse.set_visible(False)
        last_page_switch_time = time.time()
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            # Page switching
            if time.time() - last_page_switch_time >= page_display_duration:
                current_page = (current_page + 1) % num_pages
                last_page_switch_time = time.time()

            # Check for cleared alert
            action2 = handle_commands()
            if action2 == "ALERT_CLEARED":
                running = False
                break

            # Draw alert
            screen.fill((0, 0, 0))
            inner_rect_x, inner_rect_y = 120, 40
            inner_rect_width, inner_rect_height = screen_width - 240, screen_height - 80
            pygame.draw.rect(screen, style1.background, (inner_rect_x, inner_rect_y, inner_rect_width, inner_rect_height))
            pygame.draw.rect(screen, style1.border, (inner_rect_x, inner_rect_y, inner_rect_width, inner_rect_height), 5)

            line_spacing = 5
            for i, line in enumerate(alertPages[current_page]):
                text_surface = font.render(line, True, style1.text)
                text_rect = text_surface.get_rect(centerx=screen_width // 2, y=inner_rect_y + i * (font_size + line_spacing))
                screen.blit(text_surface, text_rect)

            pygame.display.flip()
            time.sleep(0.01)

        # Close window and return to desktop/login
        pygame.display.quit()
        print("Alert ended, window hidden.")
    time.sleep(0.5)
