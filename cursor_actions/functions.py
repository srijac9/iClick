import pyautogui
import time

pyautogui.FAILSAFE = True

def move_cursor(x, y, duration=0.05):
    pyautogui.moveTo(x, y, duration=duration)

def left_click():
    pyautogui.leftClick()
    print(f"left click performed")

def right_click():
    pyautogui.rightClick()
    print("Right click performed")
    