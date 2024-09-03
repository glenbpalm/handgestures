import os
import json
from time import sleep
import cv2
import mediapipe as mp
import numpy as np
import pyautogui
from pynput.mouse import Button, Controller

mouse_controller = Controller()

from src.config import recheck, mouse, keystrokes

pyautogui.FAILSAFE = False

class handDetector:
    def __init__(self, cap, screen_width, screen_height):
        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            max_num_hands=1, min_detection_confidence=0.8)
        self.mpDraw = mp.solutions.drawing_utils
        self.cap = cap
        self.results = None  # Initialize results var
        self.mouse_down_state = False
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.frame_count = 0

    def findHands(self, frame, model, classNames, x, y, draw=False):
        framergb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(framergb)

        className = ''

        if self.results.multi_hand_landmarks:
            landmarks = []
            for handLms in self.results.multi_hand_landmarks:
                for lm in handLms.landmark:
                    lmx = int((1 - lm.x) * y)
                    lmy = int(lm.y * x)
                    landmarks.append([lmx, lmy])

            if draw:
                self.mpDraw.draw_landmarks(frame, handLms, self.mpHands.HAND_CONNECTIONS, self.mpDraw.DrawingSpec(
                    color=(250, 44, 250), thickness=2, circle_radius=2))
            else:
                self.mpDraw.draw_landmarks(
                    frame, handLms, self.mpHands.HAND_CONNECTIONS)

                self.frame_count += 1

                if self.frame_count == 5:
                    self.frame_count = 0

                    prediction = model.predict([landmarks])
                    print(prediction)
                    classID = np.argmax(prediction)
                    className = classNames[classID]

        return className

    def check_gesture(self, className):
        global recheck
        global mouse

        if className == 'rock' and recheck == True:
            recheck = False
            sleep(keystrokes['sleep'])
            recheck = True
        elif className == 'thumbs down' and recheck == True:
            pyautogui.press(keystrokes['thumbs_down'])
            recheck = False
            sleep(keystrokes['sleep'])
            recheck = True
        elif (className == 'thumbs up' or className == 'call me') and recheck == True: 
            pyautogui.press(keystrokes['thumbs_up'])
            recheck = False
            sleep(keystrokes['sleep'])
            recheck = True
        elif className in ('okay', 'stop', 'live long', 'fist', 'smile', 'peace') and recheck == True: 
            recheck = False
            sleep(keystrokes['sleep'])
            recheck = True

    def mouse_control_function(self, x, y, frame):
        quadrant_width = x // 2
        quadrant_height = y // 2

        if self.results.multi_hand_landmarks:
            for handLandmarks in self.results.multi_hand_landmarks:
                palmfingertip = handLandmarks.landmark[self.mpHands.HandLandmark.MIDDLE_FINGER_MCP]
                indexfingertip = handLandmarks.landmark[self.mpHands.HandLandmark.INDEX_FINGER_TIP]
                thumbfingertip = handLandmarks.landmark[self.mpHands.HandLandmark.THUMB_TIP]

                if palmfingertip.x * x > quadrant_width and palmfingertip.y * y < quadrant_height:
                    indexfingertip_x, indexfingertip_y = int(indexfingertip.x * x), int(indexfingertip.y * y)
                    thumbfingertip_x, thumbfingertip_y = int(thumbfingertip.x * x), int(thumbfingertip.y * y)

                    screen_width, screen_height = pyautogui.size()

                    cursor_x = int((palmfingertip.x - 0.5) * 2 * screen_width)
                    cursor_y = int(palmfingertip.y * 2 * screen_height)

                    cursor_x = max(0, min(cursor_x, screen_width - 1))
                    cursor_y = max(0, min(cursor_y, screen_height - 1))

                    # Move the mouse using pynput
                    mouse_controller.position = (cursor_x, cursor_y)

                    Distance_x = abs(indexfingertip_x - thumbfingertip_x)
                    Distance_y = abs(indexfingertip_y - thumbfingertip_y)

                    if Distance_x < 20 and Distance_y < 20:
                        if not self.mouse_down_state:
                            print("CLICK DOWN")
                            mouse_controller.press(Button.left)
                            self.mouse_down_state = True

                            cv2.putText(frame, "CLICK DOWN", (10, 150), cv2.FONT_HERSHEY_SIMPLEX,
                                        1, (0, 255, 0), 2, cv2.LINE_AA)
                    
                    elif self.mouse_down_state:
                        print("MOUSE UP")
                        mouse_controller.release(Button.left)
                        self.mouse_down_state = False

        return frame