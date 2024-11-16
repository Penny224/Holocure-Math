import pyautogui
import tkinter as tk
import keyboard
import json
from sympy import sympify
import cv2
import numpy as np
import os

# Dictionary of interchangable terms
template_to_symbol = {
    "plus": "+",
    "minus": "-",
    "multiply": "*",
    "divide": "/",
    "modulus": "%",
    "equals": "=",
    "0": "0", "1": "1", "2": "2", "3": "3", "4": "4",
    "5": "5", "6": "6", "7": "7", "8": "8", "9": "9",
    "openp": "(",   
    "closedp": ")"   
   
}

# config creation
CONFIG_FILE = "config.txt"

# try catch for config
try:
    #with - cleans up file after, open(a,b) opens a in b mode (read,write), store in f
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        x, y, width, height = config["x"], config["y"], config["width"], config["height"]
except FileNotFoundError:
    # stops program from freaking out if it breaks
    x, y, width, height = 200, 100, 600, 150

def save_config():
    #Save the current region configuration to a file.
    config = {"x": x, "y": y, "width": width, "height": height}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def create_overlay(x, y, width, height):
    
    #Make box for easier number getting
    #create tkinter gui
    overlay = tk.Tk()
    overlay.overrideredirect(True)  # no borders
    overlay.attributes('-topmost', True)  # stay on top
    overlay.attributes('-alpha', 0.3)  # see through
    overlay.configure(background='red')
    update_overlay_position(overlay, x, y, width, height)
    return overlay

def update_overlay_position(overlay, x, y, width, height):
    #change overlay spot
    overlay.geometry(f"{width}x{height}+{x}+{y}")

# load template images because font is a heck
def load_templates(folder_path="templates"):
    templates = {}
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            key = filename.split('.')[0]  # get first part of file
            img = cv2.imread(os.path.join(folder_path, filename), 0)  # load image, 0 for greyscale and ez reading
            templates[key] = img
    return templates

def match_templates(screenshot, templates, default_threshold=0.8, custom_thresholds=None, min_distance=10):
   #match the templates
    if custom_thresholds is None:
        custom_thresholds = {}

    detected_chars = []
    
    for char, template in templates.items():
        #threshold i have to play with probably
        threshold = custom_thresholds.get(char, default_threshold)
        #cv2 match template to screenshots and see whats closer
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= threshold)

        #this part hurts my brain but google told me to
        for pt in zip(*loc[::-1]):
            x_coord = pt[0]
            symbol = template_to_symbol.get(char, "")

            # possible duplication protection
            if symbol and (not detected_chars or abs(x_coord - detected_chars[-1][0]) > min_distance or detected_chars[-1][1] != symbol):
                detected_chars.append((x_coord, symbol))  # Save the x-coordinate and character

    # sort the screenshots by x value
    detected_chars.sort(key=lambda x: x[0])

    # duplicate protection
    filtered_chars = []
    for i in range(len(detected_chars)):
        if i == 0 or abs(detected_chars[i][0] - detected_chars[i - 1][0]) > min_distance:
            filtered_chars.append(detected_chars[i])

    # combine the boys
    equation = "".join([char for _, char in filtered_chars])
    return equation



def capture_and_solve_screenshot(x, y, width, height, templates):
    #screenshot, extract the equation, solve the guy
    
    region = (x, y, width, height)
    screenshot = pyautogui.screenshot(region=region)
    screenshot = np.array(screenshot.convert("L")) 

    # match templates
    equation_text = match_templates(screenshot, templates)
    print(f"Extracted Equation (raw): {equation_text}")

    # remove = and ???
    if '=' in equation_text:
        equation_text = equation_text.split('=')[0].strip()
    print(f"Cleaned Equation: {equation_text}")

    try:
        # sympy the equation
        equation = sympify(equation_text)
        result = equation.evalf()
        print(f"Solution: {result}")
    except Exception as e:
        print(f"Could not solve the equation: {e}")


def main():
    global x, y, width, height

    
    templates = load_templates()

    
    overlay = create_overlay(x, y, width, height)

    print("arrow keys to move")
    print("+/- for width")
    print("[/] for height")
    print("F5 to screenshot")
    print("ESC to exit")
    print("control q to panic")

    # move around the boy
    def move_up():
        global y
        y -= 5
        update_overlay_position(overlay, x, y, width, height)

    def move_down():
        global y
        y += 5
        update_overlay_position(overlay, x, y, width, height)

    def move_left():
        global x
        x -= 5
        update_overlay_position(overlay, x, y, width, height)

    def move_right():
        global x
        x += 5
        update_overlay_position(overlay, x, y, width, height)

    def increase_width():
        global width
        width += 5
        update_overlay_position(overlay, x, y, width, height)

    def decrease_width():
        global width
        width = max(5, width - 5)  # cannot be below 5
        update_overlay_position(overlay, x, y, width, height)

    def increase_height():
        global height
        height += 5
        update_overlay_position(overlay, x, y, width, height)

    def decrease_height():
        global height
        height = max(5, height - 5)  # same
        update_overlay_position(overlay, x, y, width, height)

    def take_screenshot_and_solve():
        capture_and_solve_screenshot(x, y, width, height, templates)

    def exit_program():
        print("kbye")
        save_config()
        overlay.destroy()

    # hotkeys
    keyboard.add_hotkey('up', move_up)
    keyboard.add_hotkey('down', move_down)
    keyboard.add_hotkey('left', move_left)
    keyboard.add_hotkey('right', move_right)
    keyboard.add_hotkey('+', increase_width)
    keyboard.add_hotkey('-', decrease_width)
    keyboard.add_hotkey(']', increase_height)
    keyboard.add_hotkey('[', decrease_height)
    keyboard.add_hotkey('f5', take_screenshot_and_solve)
    keyboard.add_hotkey('esc', exit_program)

    # mainloop to keep the boy open
    overlay.mainloop()

    # make sure its actually closed
    keyboard.clear_all_hotkeys()

if __name__ == "__main__":
    main()
