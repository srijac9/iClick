import cv2
import time
import sys
import subprocess
import numpy as np
import mediapipe as mp

from cursor_actions.functions import left_click, right_click

# -----------------------------
# Shortcuts controller:
# - Double blink -> left click
# - Blink hold -> right click
# - Open palm -> start STT typing (stream_stt.py)
# - Hand wave -> no action (placeholder)
# -----------------------------

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def _dist(a, b):
    return np.linalg.norm(a - b)


def eye_aspect_ratio(landmarks_px, eye_idx):
    p1 = landmarks_px[eye_idx[0]]
    p2 = landmarks_px[eye_idx[1]]
    p3 = landmarks_px[eye_idx[2]]
    p4 = landmarks_px[eye_idx[3]]
    p5 = landmarks_px[eye_idx[4]]
    p6 = landmarks_px[eye_idx[5]]

    numerator = _dist(p2, p6) + _dist(p3, p5)
    denominator = 2.0 * _dist(p1, p4)
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def normalized_to_pixel_coords(landmarks, w, h):
    pts = np.zeros((len(landmarks), 2), dtype=np.float32)
    for i, lm in enumerate(landmarks):
        pts[i] = (lm.x * w, lm.y * h)
    return pts


def is_finger_extended(pts, tip_idx, pip_idx, mcp_idx):
    wrist = pts[0]
    tip = pts[tip_idx]
    pip = pts[pip_idx]
    mcp = pts[mcp_idx]
    return np.linalg.norm(tip - wrist) > np.linalg.norm(pip - wrist) > np.linalg.norm(mcp - wrist)


def start_stt(stt_proc):
    if stt_proc and stt_proc.poll() is None:
        return stt_proc
    try:
        return subprocess.Popen([sys.executable, "-u", "stream_stt.py"])
    except Exception:
        return stt_proc


class GestureController:
    def __init__(self, camera_index=0, show_debug=True, show_window=False):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

        self.show_debug = show_debug
        self.show_window = show_window

        # Tunable parameters
        self.ear_threshold = 0.21
        self.consec_frames = 2
        self.click_cooldown = 0.5
        self.hold_seconds = 0.7
        self.double_blink_window = 0.8

        # State
        self.frames_below = 0
        self.blink_in_progress = False
        self.blink_count = 0
        self.last_blink_time = 0.0
        self.closed_start = None
        self.hold_fired = False
        self.last_action_time = 0.0

        self.open_palm_active = False
        self.stt_proc = None

        # Action map (customizable)
        self.actions = {
            "double_blink": left_click,
            "blink_hold": right_click,
            "open_palm": "start_stt",
            "wave": None,
        }

        def _noop():
            return None

        def _handle_start_stt():
            self.stt_proc = start_stt(self.stt_proc)

        self.dispatch = {
            "start_stt": _handle_start_stt,
            "noop": _noop,
        }

    def run_action(self, key: str):
        action = self.actions.get(key)
        if action is None:
            return
        if callable(action):
            action()
            return
        handler = self.dispatch.get(action)
        if handler:
            handler()

    def step(self):
        ok, frame = self.cap.read()
        if not ok:
            return False

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        face_results = face_mesh.process(rgb)
        hand_results = hands.process(rgb)
        rgb.flags.writeable = True

        ear = None
        is_open_palm = False
        gesture_active = False

        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0].landmark
            pts = normalized_to_pixel_coords(face_landmarks, w, h)

            left_ear = eye_aspect_ratio(pts, LEFT_EYE)
            right_ear = eye_aspect_ratio(pts, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            if ear < self.ear_threshold:
                self.frames_below += 1
                gesture_active = True
                if self.closed_start is None:
                    self.closed_start = time.time()
                if self.frames_below >= self.consec_frames and not self.blink_in_progress:
                    self.blink_in_progress = True
                    now = time.time()
                    # Double-blink detection
                    if now - self.last_blink_time <= self.double_blink_window:
                        self.blink_count += 1
                    else:
                        self.blink_count = 1
                    self.last_blink_time = now

                    if self.blink_count >= 2 and (now - self.last_action_time >= self.click_cooldown):
                        self.run_action("double_blink")
                        self.last_action_time = now
                        self.blink_count = 0
                # Hold detection
                if not self.hold_fired and self.closed_start and (time.time() - self.closed_start) >= self.hold_seconds:
                    if (time.time() - self.last_action_time) >= self.click_cooldown:
                        self.run_action("blink_hold")
                        self.last_action_time = time.time()
                    self.hold_fired = True
            else:
                self.frames_below = 0
                self.blink_in_progress = False
                self.closed_start = None
                self.hold_fired = False

            if self.show_debug:
                for idx in LEFT_EYE + RIGHT_EYE:
                    x, y = pts[idx].astype(int)
                    cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        if hand_results.multi_hand_landmarks:
            lm = hand_results.multi_hand_landmarks[0].landmark
            pts = normalized_to_pixel_coords(lm, w, h)

            fingers = [
                (8, 6, 5),    # index
                (12, 10, 9),  # middle
                (16, 14, 13), # ring
                (20, 18, 17), # pinky
            ]
            extended = 0
            for tip, pip, mcp in fingers:
                if is_finger_extended(pts, tip, pip, mcp):
                    extended += 1
            thumb_extended = np.linalg.norm(pts[4] - pts[0]) > np.linalg.norm(pts[3] - pts[0]) > np.linalg.norm(pts[2] - pts[0])

            if extended >= 3 and thumb_extended:
                is_open_palm = True
                gesture_active = True

            if self.show_debug:
                for p in pts:
                    cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 0), -1)

        if is_open_palm and not self.open_palm_active:
            self.run_action("open_palm")
        self.open_palm_active = is_open_palm

        if self.show_window:
            cv2.imshow("Shortcut Controller (press q to quit)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                raise KeyboardInterrupt()
        else:
            time.sleep(0.01)

        return gesture_active

    def close(self):
        if self.cap:
            self.cap.release()
        if self.show_window:
            cv2.destroyAllWindows()
        if self.stt_proc and self.stt_proc.poll() is None:
            self.stt_proc.terminate()


def main():
    controller = GestureController(show_debug=True, show_window=False)
    try:
        while True:
            controller.step()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()


if __name__ == "__main__":
    main()
