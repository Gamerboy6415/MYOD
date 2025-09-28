# main_pygame.py
import pygame
import time
import threading
import queue
import control_panel 
import os
from EAS2Text import EAS2Text
import re

import socket
import subprocess





# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 1280
screen_height = 720
pygame.display.set_caption("dasdec renderer")

if os.name == "posix":
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    os.environ["SDL_AUDIODRIVER"] = "pulseaudio"
    # os.system("sudo systemctl start endec.service")
    
else:
    screen = pygame.display.set_mode((screen_width, screen_height))

pygame.mouse.set_visible(False)
    

# Constants for commands (avoiding enums)
SWITCH_STYLE = "SWITCH_STYLE"
SWITCH_PAGE = "SWITCH_PAGE"
QUIT = "QUIT"

# --- style Definitions  ---
class Style:
    def __init__(self, background, text, border, margin, font):
        self.background = background
        self.text = text
        self.border = border
        self.margin = margin
        self.font = font

style1 = Style((46, 50, 81), (255, 255, 255), (108, 29, 35), (0, 0, 0), "luximb.ttf")  # Original
style2 = Style((0, 0, 0), (255, 255, 255), (0, 0, 0), (0, 0, 0), "luximb.ttf")        # All Black/White
style3 = Style((0, 1, 228), (255, 255, 255), (0, 1, 228), (0, 0, 0), "arialbd.ttf") # Black Background, Blue Box/Border

styles = [style1, style2, style3]  # List of styles
current_style_index = 0          # Start with the first style

def set_style(style):
    global background_color, text_color, border_color, margin_color, font
    background_color = style.background
    text_color = style.text
    border_color = style.border
    margin_color = style.margin
    try:
        font = pygame.font.Font(style.font, font_size)
    except FileNotFoundError:
        print(f"Font '{style.font}' not found. Using default font.")
        font = pygame.font.Font(None, font_size)

# --- End style Definitions ---

# Margin widths
margin_width_vertical = 40  # Top and bottom margin
margin_width_horizontal = 120  # Left and right margin

# Border width
border_width = 5

# Font
font_size = 40
try:
    font = pygame.font.Font("luximb.ttf", font_size)
except FileNotFoundError:
    print("Font 'luximb.ttf' not found. Using default font.")
    font = pygame.font.Font(None, font_size)

# Default page
defaultPages = [
    [
        "Emergency Alert Details",
        "", "", "", "", "", "", "", "", "", "", "", "1/1"
    ]
]


# Text content for each page
#test example
alertPages = [
    [
        "THE PRIMARY ENTRY POINT EAS SYSTEM",
        "has issued A NATIONAL PERIODIC TEST",
        "for the following counties or",
        "areas:",
        "United States;",
        "District of Columbia, DC;",
        "at 1:20 PM",
        "on AUG 7, 2019",
        "Effective until 1:50 PM.",
        "Message from WBAP 1.",
        "",
        "",
        "1/3",
    ],
    [
        "This is page 2 of the EAS test.",
        "This test is designed to ensure the",
        "Emergency Alert System is functioning",
        "correctly.",
        "",
        "Remember, this is only a test.",
        "",
        "More information can be found at",
        "www.fcc.gov/eas",
        "",
        "",
        "",
        "2/3",
    ],
    [
        "This is page 3 of the EAS test.",
        "In a real emergency, follow the",
        "instructions provided by local",
        "authorities.",
        "",
        "Stay safe and be prepared.",
        "",
        "Thank you for your attention.",
        "",
        "",
        "",
        "",
        "3/3",
    ],
]

pages = defaultPages # starts with the Alert pages, press 'd' to switch to default


num_pages = len(pages)
current_page = 0
page_display_duration = 5  # Seconds to display each page

last_page_switch_time = time.time()  # Track when the page was last switched

audio_finished = False

info_visible = False
info_display_time = 0
info_lines = []

def render_text(lines):
    """Renders the given lines of text to surfaces and rects."""
    text_positions = []
    line_spacing = 5
    start_y = 50

    for i, line in enumerate(lines):
        text_surface = font.render(line, True, text_color)
        text_rect = text_surface.get_rect(centerx=screen_width // 2, y=start_y + i * (font_size + line_spacing))
        text_positions.append((text_surface, text_rect))
    return text_positions

def audio_finished_callback():
    """Callback function executed when the audio finishes playing."""
    global audio_finished
    audio_finished = True
    print("Audio finished playing.")


import re

def format_eas_message(eas_text):
    MAX_LINE_LENGTH = 35
    MAX_LINES_PER_PAGE = 13
    
    # Ensure areas are split into separate lines
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
    
    # Split into pages
    pages = []
    total_pages = (len(formatted_lines) + (MAX_LINES_PER_PAGE - 1) - 1) // (MAX_LINES_PER_PAGE - 1)
    
    for i in range(0, len(formatted_lines), MAX_LINES_PER_PAGE - 1):
        page_content = formatted_lines[i:i + (MAX_LINES_PER_PAGE - 1)]
        while len(page_content) < (MAX_LINES_PER_PAGE - 1):
            page_content.append("")  # Fill empty lines if necessary
        page_content.append(f"{len(pages) + 1}/{total_pages}")
        pages.append(page_content)
    
    return pages

def get_system_info():
    """Gathers network information and returns it as a list of strings."""
    lines = []
    try:
        hostname = socket.gethostname()
        lines.append(f"Hostname: {hostname}")
        # reliable way to get the primary IP address
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.1)
            s.connect(("8.8.8.8", 80)) # Connect to a public DNS server
            ip_address = s.getsockname()[0]
        lines.append(f"IP Address: {ip_address}")
    except Exception:
        lines.append("Network Info: Could not determine IP.")

    # Get gateway on Linux systems
    if os.name == "posix":
        try:
            result = subprocess.check_output("ip route | grep default", shell=True, text=True)
            gateway = result.split(' ')[2]
            lines.append(f"Gateway: {gateway}")
        except Exception:
            lines.append("Gateway: N/A")
    return lines
    

# ----  Command Queue and Handling  ----

command_queue = queue.Queue()

def handle_commands():
    global current_style_index, pages, num_pages, current_page
    try:
        while True:
            command = command_queue.get_nowait()  # Non-blocking get

            if command[0] == SWITCH_STYLE:
                current_style_index = (command[1]) % len(styles)
                set_style(styles[current_style_index])
                print(f"GUI: Switched to style {current_style_index}")

            elif command[0] == SWITCH_PAGE:
                if command[1] == "default":
                    pages = defaultPages
                elif command[1] == "alert":
                    pages = alertPages
                num_pages = len(pages)
                current_page = 0
                print(f"GUI: Switched to page {command[1]}")

            elif command[0] == "ORIGINATE_ALERT":
                #Do not use
                pass

            elif command[0] == "DISPLAY_ALERT":
                print("GUI: Displaying Alert")
                try: 
                    msg = EAS2Text(command[1]["headers"])
                except:
                    print("Error parsing EAS message")
                    return

                desc = command[1]["description"]

                orgText = msg.orgText
                orgText = orgText.replace("An EAS Participant", "A broadcast or cable system")

                msgFrom = ".\n"

                if "Message from" not in desc:
                    msgFrom = ".\nMessage from "+msg.callsign+".\n"

                text = (str.upper(orgText) + 
                        "\nhas issued " + str.upper(msg.evntText) + 
                        "\nfor the following counties or\nareas:\n" + 
                        ";\n".join(msg.FIPSText) + 
                        ";\nat " + msg.startTime.strftime("%I:%M %p") + 
                        "\non " + str.upper(msg.startTime.strftime("%b %d, %Y")) + 
                        "\nEffective until " + 
                        msg.endTime.strftime("%I:%M %p") + 
                        msgFrom + 
                        desc)
                print(text)
                pages = format_eas_message(text)
                print(pages)
                num_pages = len(pages)
                current_page = 0
                last_page_switch_time = time.time()

            elif command[0] == "CLEAR_ALERT":
                print("GUI: Clearing Alert")
                threading.Timer(3.0, lambda: clear_alert()).start()



                
            elif command[0] == QUIT:
              print("GUI: Quitting application")
              pygame.quit()
              exit()
            elif command[0] == "SHUTDOWN":
              print("GUI: Shutting down system")
              os.system("sudo shutdown now")

              

            command_queue.task_done() # Mark as handled
    except queue.Empty:
        pass # No commands, continue


def clear_alert():
    global pages, num_pages, current_page, last_page_switch_time
    pages = defaultPages
    num_pages = len(pages)
    current_page = 0
    last_page_switch_time = time.time()

# Initialize colors based on the starting style
set_style(styles[current_style_index])

#start Control Panel in a thread.
control_panel.start_control_panel(command_queue)

# main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.USEREVENT + 1:  # Audio finished event
            audio_finished_callback()
        elif event.type == pygame.KEYDOWN: # Switch Style
            if event.key == pygame.K_SPACE:  # Press space to switch styles
                current_style_index = (current_style_index + 1) % len(styles)
                set_style(styles[current_style_index]) # Update global colors
            elif event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_i:
                info_lines = get_system_info()
                info_display_time = time.time()
                info_visible = True



    # Check if it's time to switch to the next page
    current_time = time.time()
    if current_time - last_page_switch_time >= page_display_duration:
        current_page = (current_page + 1) % num_pages  # Cycle through pages
        last_page_switch_time = current_time

    # ---- Handle commands from the GUI  ----
    handle_commands()

    # Clear the screen with margin color
    screen.fill(margin_color)

    # Calculate the inner rectangle's coordinates with different margins
    inner_rect_x = margin_width_horizontal
    inner_rect_y = margin_width_vertical
    inner_rect_width = screen_width - 2 * margin_width_horizontal
    inner_rect_height = screen_height - 2 * margin_width_vertical

    # Draw the background color inside the margin
    pygame.draw.rect(screen, background_color, (inner_rect_x, inner_rect_y, inner_rect_width, inner_rect_height))

    # Draw the border
    pygame.draw.rect(screen, border_color, (inner_rect_x, inner_rect_y, inner_rect_width, inner_rect_height), border_width)

    # Render and blit the text for the current page
    text_positions = render_text(pages[current_page])  # Get text for current page
    for text_surface, text_rect in text_positions:
        screen.blit(text_surface, text_rect)

    if info_visible:
        # Hide the overlay after 10 seconds
        if time.time() - info_display_time > 10:
            info_visible = False
        else:
            # Set up font for the info text
            info_font_size = 28
            try:
                info_font = pygame.font.Font("luximb.ttf", info_font_size)
            except FileNotFoundError:
                info_font = pygame.font.Font(None, info_font_size)

            # Calculate overlay size based on number of lines
            line_height = info_font_size + 5
            num_lines = len(info_lines)
            overlay_width = 600
            overlay_height = 20 + num_lines * line_height + 20  # 20px padding top/bottom

            overlay = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)
            overlay.fill((10, 10, 10, 210)) # Dark, semi-transparent background

            # Render each line of info text onto the overlay
            line_y = 20
            for line in info_lines:
                text_surf = info_font.render(line, True, (255, 255, 255))
                overlay.blit(text_surf, (20, line_y))
                line_y += line_height

            # Position and draw the overlay in the center of the screen
            overlay_x = (screen_width - overlay_width) // 2
            overlay_y = (screen_height - overlay_height) // 2
            screen.blit(overlay, (overlay_x, overlay_y))
  

    # Update the display
    pygame.display.flip()

    time.sleep(0.01)  # Small delay to prevent excessive CPU usage

    

# Quit Pygame
pygame.quit()