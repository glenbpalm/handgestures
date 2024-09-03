import os
import threading
import cv2
from tensorflow.keras.models import load_model
import pyautogui
import time

from src.config import recheck, mouse, stay_on_top, keystrokes  # Import keystrokes from config
from src.handTrackerMod import handDetector

# Load the gesture recognizer model
path = os.path.join(os.getcwd(), 'model')
model = load_model(path)

# Load class names
class_name_path = os.path.join(os.path.dirname(path), 'gesture.names')
with open(class_name_path, 'r') as f:
    classNames = f.read().split('\n')

print("Loaded Class Names:", classNames)

# FPS
fps_start_time = time.time()
fps = 0
frame_count = 0

current_gesture = None

def show_frames(className, classNames, frame, target, args):
    global mouse
    global current_gesture

    # Handle the gesture logic to toggle mouse control mode
    if className == 'stop':
        mouse = True
    elif className == 'rock':
        mouse = False

    if className in classNames:
        current_gesture = className

    # Show the prediction on the frame
    cv2.putText(frame, current_gesture, (10, 50), cv2.FONT_HERSHEY_SIMPLEX,
                1, (0, 0, 255), 2, cv2.LINE_AA)

    if recheck:
        t = threading.Thread(target=target, args=args)
        t.start()

    mode = "Cursor Mode" if mouse else "Gesture Mode"
    cv2.putText(frame, mode, (10, 100), cv2.FONT_HERSHEY_SIMPLEX,
                1, (255, 0, 0), 2, cv2.LINE_AA)

    # Resize and display the frame
    x, y, _ = frame.shape
    frame = cv2.resize(frame, (int(x / 1.5), int(y / 2.5)))

    # Maintain aspect ratio when resizing
    # height, width = frame.shape[:2]
    # aspect_ratio = width / height
    # new_width = int(640 * aspect_ratio)  # 640 is the desired width, adjust as needed
    # frame = cv2.resize(frame, (new_width, 640))

    cv2.imshow("Hand Tracking", frame)

    if stay_on_top:
        cv2.setWindowProperty("Hand Tracking", cv2.WND_PROP_TOPMOST, 1)

    return frame


if __name__ == "__main__":
    cap = cv2.VideoCapture(0)

    # Get your screen resolution
    screen_width, screen_height = pyautogui.size()

    detector = handDetector(cap, screen_width, screen_height)

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to capture a frame.")
            break

        frame_count += 1
        if frame_count >= 10:
            fps_end_time = time.time()
            fps = int(frame_count / (fps_end_time - fps_start_time))
            frame_count = 0
            fps_start_time = fps_end_time

        x, y, c = frame.shape

        frame = cv2.flip(frame, 1)
        cv2.putText(frame, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Detect hand gestures
        className = detector.findHands(frame, model, classNames, x, y)

        if mouse:
            args = (x, y, frame)
            frame = detector.mouse_control_function(*args)
            frame = show_frames(className, classNames, frame, detector.mouse_control_function, args)
        else:
            args = (className,)
            show_frames(className, classNames, frame, detector.check_gesture, args)

        # Test mouse click functionality independently
        if className == "test_click":  # Add a test gesture name for testing clicks
            pyautogui.moveTo(screen_width // 2, screen_height // 2)  # Move to center
            pyautogui.mouseDown(button='left')
            time.sleep(0.1)
            pyautogui.mouseUp(button='left')

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()