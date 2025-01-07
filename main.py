import numpy as np
import cv2
import mediapipe as mp
import streamlit as st

st.title("Virtual Keyboard")
frame_placeholder = st.empty()
stop = st.button("Stop")

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Virtual keyboard layout
keys = [
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "{", "}", "[", "]"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "BackSpace"],
    ["CapsLock", "A", "S", "D", "F", "G", "H", "J", "K", "L"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M"],
    ["#", "Space", "@"]
]

cursor_visible = True  # Cursor visibility state
cursor_timer = 0       # Timer to manage cursor blinking
cursor_blink_delay = 30  # Number of frames for each blink cycle


# Keyboard settings
key_width = 100
key_height = 100
margin = 0
keyboard_origin = (350, 300)  # Top-left corner of the keyboard
output_text = ""  # To store output text


# change in size for different key
def key_sizes(r, c):
    k = keys[r][c]
    if k == "Space":
        return 100
    if k == "Tab":
        return 40
    if k == "CapsLock":
        return 70
    if k =="Shift":
        return 50
    return 20

def rect_sizes(r, c):
    k = keys[r][c]
    v = 1
    if k == "Space":
        v = 6.25
    if k == "Tab":
        v = 1.25
    if k == "CapsLock":
        v = 1.75
    if k =="Shift":
        v = 1.75
    if k == "BackSpace":
        v = 1.75
    return int(v * key_width)
    

# function to draw the virtual keyboard
def draw_keyboard(frame, hover_key=None):
    x_start, y_start = keyboard_origin
    for row_idx, row in enumerate(keys):
        for col_idx, key in enumerate(row):
            y = y_start + row_idx * (key_height + margin)
            x = x_start + sum([rect_sizes(row_idx, i) for i in range(col_idx)])
            color = (0, 255, 0) if (row_idx, col_idx) == hover_key else (255, 255, 255)
            cv2.rectangle(frame, (x, y), (x +rect_sizes(row_idx, col_idx), y + key_height), color, -1 if (row_idx, col_idx) == hover_key else 2)
            cv2.putText(frame, key, (x + key_sizes(row_idx, col_idx), y + 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)

# function to find the key being hovered
def get_hovered_key(hand_x, hand_y):
    x_start, y_start = keyboard_origin
    for row_idx, row in enumerate(keys):
        for col_idx, key in enumerate(row):
            x = x_start + sum([rect_sizes(row_idx, i) for i in range(col_idx)])
            y = y_start + row_idx * (key_height + margin)
            if x <= hand_x <= x + rect_sizes(row_idx, col_idx) and y <= hand_y <= y + key_height:
                return (row_idx, col_idx)
    return None



# Main loop
cap = cv2.VideoCapture(1)
click_delay = 10  # Delay in frames to register subsequent clicks
click_timer = 0   # Timer to control click frequency

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)  # Flip for a mirror effect
    h, w, _ = frame.shape 
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 

    # Mediapipe processing
    result = hands.process(frame)
    hover_key = None

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            # Draw landmarks
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get index and middle finger tip coordinates
            index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
            x_middle, y_middle = int(middle_tip.x * w), int(middle_tip.y * h)
            
            # Check if hovering over a key
            hover_key = get_hovered_key(x_index, y_index)
            
            # Check if index and middle fingers are close together (click condition)
            distance = np.sqrt((x_index - x_middle)**2 + (y_index - y_middle)**2)
            if distance < 40 and hover_key and click_timer == 0:
                row, col = hover_key
                key = keys[row][col] 
                
                if key == "BackSpace":
                # Remove the last character from output_text if it's not empty
                    if len(output_text) > 0:
                        output_text = output_text[:-1]
                elif key == "Space":
                    # Add a space if the "Space" key is clicked
                    output_text += " "
                else:
                    # Add the clicked key to the output text
                    output_text += key
                    click_timer = click_delay  # Reset click timer
                    
                    cv2.circle(frame, (x_index, y_index), 10, (0, 0, 255), -1)
                    cv2.circle(frame, (x_middle, y_middle), 10, (0, 0, 255), -1)

    # Reduce click timer
    if click_timer > 0:
        click_timer -= 1

    # Draw keyboard
    draw_keyboard(frame, hover_key)

    # Update cursor timer for blinking
    cursor_timer += 1
    if cursor_timer >= cursor_blink_delay:
        cursor_visible = not cursor_visible
        cursor_timer = 0


    # Display output text
    output_box_origin = (400, 800)
    cv2.rectangle(frame, output_box_origin, (1200, 1000), (255, 255, 255, 50), -1)
    output_list = []
    cnt = 0
    temp = ""
    limit = 30

    # Split text into lines of length <= limit
    for i in output_text:
        temp += i
        cnt += 1
        if cnt == limit:
            output_list.append(temp)
            cnt = 0
            temp = ""
    if len(temp) > 0:
        output_list.append(temp)

    # Add an empty line if output_text is empty
    if not output_list:
        output_list.append("")

    # Draw each line of text
    for i in range(len(output_list)):
        cv2.putText(
            frame, ("Output: " if i == 0 else " " * 8) + output_list[i],
            (output_box_origin[0] + 10, output_box_origin[1] + 50 * (i + 1)),
            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
        )

    # Draw a blinking cursor accurately
    if cursor_visible:
        last_line = output_list[-1]
        prefix = "Output: " if len(output_list) == 1 else " " * 8
        text_to_cursor = prefix + last_line

        # Calculate cursor position using text width
        text_width, text_height = cv2.getTextSize(text_to_cursor, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
        cursor_x = output_box_origin[0] + 10 + text_width
        cursor_y = output_box_origin[1] + 50 * len(output_list)

        # Draw the cursor as a small vertical rectangle
        cursor_height = 30  # Height of the cursor
        cv2.rectangle(frame, (cursor_x, cursor_y - cursor_height), (cursor_x + 2, cursor_y), (0, 0, 0), -1)

    #cv2.imshow("Virtual Keyboard", frame)
    frame_placeholder.image(frame, channels = "RGB")
    if cv2.waitKey(1) & 0xFF == 27:  # Press Esc to exit
        break


cap.release()
cv2.destroyAllWindows()
