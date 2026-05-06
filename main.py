import cv2
import mediapipe as mp
import pyautogui
import time
import math

pyautogui.FAILSAFE = False

# Initialize
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7,
                       min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

screen_w, screen_h = pyautogui.size()

# Timing
last_action_time = 0
cooldown = 1

# Mode
mode = "media"

# Cursor smoothing
prev_x, prev_y = 0, 0

# Scroll tracking
prev_scroll_y = 0

# Click flag
click_flag = False

# Dead zone threshold
dead_zone = 5

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = hands.process(img_rgb)

    action_text = f"Mode: {mode}"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks = []
            for id, lm in enumerate(hand_landmarks.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                landmarks.append((cx, cy))

            # -------- Finger Detection --------
            tips = [4, 8, 12, 16, 20]
            fingers = []

            if landmarks[4][0] < landmarks[3][0]:
                fingers.append(1)
            else:
                fingers.append(0)

            for i in range(1, 5):
                if landmarks[tips[i]][1] < landmarks[tips[i] - 2][1] - 10:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # -------- Pinch Distance --------
            x1, y1 = landmarks[4]
            x2, y2 = landmarks[8]
            distance = math.hypot(x2 - x1, y2 - y1)

            current_time = time.time()

            # ==========================
            # 🖱️ IMPROVED MOUSE MODE
            # ==========================
            if mode == "mouse":

                frame_margin = 120

                # Map camera to screen
                x_cam = max(frame_margin, min(w - frame_margin, landmarks[8][0]))
                y_cam = max(frame_margin, min(h - frame_margin, landmarks[8][1]))

                x = int((x_cam - frame_margin) * screen_w / (w - 2 * frame_margin))
                y = int((y_cam - frame_margin) * screen_h / (h - 2 * frame_margin))

                # Dead zone (ignore small movement)
                if abs(x - prev_x) < dead_zone:
                    x = prev_x
                if abs(y - prev_y) < dead_zone:
                    y = prev_y

                # Smooth movement
                curr_x = prev_x + (x - prev_x) / 5
                curr_y = prev_y + (y - prev_y) / 5

                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y

                action_text = "Mouse Move"

                # -------- CLICK --------
                if distance < 25 and current_time - last_action_time > 0.6:
                    pyautogui.click()
                    action_text = "Click"
                    last_action_time = current_time

                # -------- SCROLL --------
                elif fingers == [0,1,1,0,0] and distance > 40:

                    if prev_scroll_y != 0:
                        if curr_y < prev_scroll_y - 25:
                            pyautogui.scroll(250)
                            action_text = "Scroll Up"
                        elif curr_y > prev_scroll_y + 25:
                            pyautogui.scroll(-250)
                            action_text = "Scroll Down"

                    prev_scroll_y = curr_y

                # -------- MODE SWITCH --------
                if sum(fingers) >= 4 and current_time - last_action_time > 1:
                    mode = "media"
                    last_action_time = current_time

            # ==========================
            # 🎵 MEDIA MODE
            # ==========================
            else:

                if distance < 25:
                    pyautogui.press("down")
                    action_text = "Volume Down"
                    time.sleep(0.2)

                elif current_time - last_action_time > cooldown:

                    if sum(fingers) == 0:
                        pyautogui.press("space")
                        action_text = "Play / Pause"

                    elif fingers == [0,1,0,0,0]:
                        pyautogui.press("k")
                        action_text = "Play"

                    elif fingers == [0,1,1,0,0]:
                        pyautogui.press("up")
                        action_text = "Volume Up"

                    elif sum(fingers) >= 4:
                        mode = "mouse"
                        action_text = "Switch to Mouse"

                    last_action_time = current_time

    # Display
    cv2.putText(img, action_text, (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

    cv2.imshow("Gesture Control System ", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()