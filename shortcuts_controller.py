import cv2
import time
import sys
import os
import json
import subprocess
import numpy as np
import mediapipe as mp
from pathlib import Path

from cursor_actions.functions import left_click, right_click

# -----------------------------
# Shortcuts controller:
# - Double blink -> left click
# - Blink hold -> right click
# - Open palm -> start STT typing (stream_stt.py)
# - Hand wave -> no action (placeholder)
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "desktop-pet" / "config" / "gesture_map.json"

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


def _load_action_map():
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return {}
        out = {}
        for item in data:
            gesture = item.get("gesture")
            action = item.get("action")
            if gesture and action:
                out[gesture] = action
        return out
    except Exception:
        return {}


def _resolve_action(action_key):
    if action_key == "left_click":
        return left_click
    if action_key == "right_click":
        return right_click
    if action_key == "typing":
        return "start_stt"
    if action_key == "open_buddy":
        return "open_buddy"
    return None


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

    # ---- Tunable parameters ----
    EAR_THRESHOLD = 0.21
    CONSEC_FRAMES = 2
    CLICK_COOLDOWN = 0.5
    HOLD_SECONDS = 0.7
    DOUBLE_BLINK_WINDOW = 0.8
    SHOW_DEBUG = True
    SHOW_WINDOW = True

    frames_below = 0
    blink_in_progress = False
    blink_count = 0
    last_blink_time = 0.0
    closed_start = None
    hold_fired = False
    last_action_time = 0.0

    open_palm_active = False
    stt_proc = None

    # Action map (customizable)
    # Values can be callables or string keys resolved by DISPATCH.
    ACTIONS = {
        "double_blink": left_click,
        "blink_hold": right_click,
        "open_palm": "start_stt",
        "wave": None,
    }

    # Override from config app if present.
    configured = _load_action_map()
    if configured:
        for gesture, action_key in configured.items():
            # Map UI gesture labels to controller keys.
            if gesture == "blink_twice":
                gesture = "double_blink"
            elif gesture == "hold":
                gesture = "blink_hold"
            ACTIONS[gesture] = _resolve_action(action_key)

    log_path = BASE_DIR / "shortcuts_log.txt"
    print("[shortcuts] ACTIONS map:", flush=True)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[shortcuts] ACTIONS map:\n")
    except Exception:
        pass
    for k, v in ACTIONS.items():
        if callable(v):
            name = getattr(v, "__name__", "callable")
            line = f"  {k}: {name}"
            print(line, flush=True)
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
        else:
            line = f"  {k}: {v}"
            print(line, flush=True)
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass

    def _noop():
        return None

    def _handle_start_stt():
        nonlocal stt_proc
        stt_proc = start_stt(stt_proc)

    def _handle_open_buddy():
        app_path = BASE_DIR / "desktop-pet" / "config_app.py"
        if app_path.exists():
            try:
                subprocess.Popen([sys.executable, str(app_path)])
            except Exception:
                return

    DISPATCH = {
        "start_stt": _handle_start_stt,
        "open_buddy": _handle_open_buddy,
        "noop": _noop,
    }

    def run_action(key: str):
        action = ACTIONS.get(key)
        if action is None:
            return
        if callable(action):
            action()
            return
        # Resolve string actions via DISPATCH
        handler = DISPATCH.get(action)
        if handler:
            handler()

    fps_t = time.time()
    fps = 0.0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        face_results = face_mesh.process(rgb)
        hand_results = hands.process(rgb)
        rgb.flags.writeable = True

        ear = None
        is_open_palm = False

        if face_results.multi_face_landmarks:
            face_landmarks = face_results.multi_face_landmarks[0].landmark
            pts = normalized_to_pixel_coords(face_landmarks, w, h)

            left_ear = eye_aspect_ratio(pts, LEFT_EYE)
            right_ear = eye_aspect_ratio(pts, RIGHT_EYE)
            ear = (left_ear + right_ear) / 2.0

            if ear < EAR_THRESHOLD:
                frames_below += 1
                if closed_start is None:
                    closed_start = time.time()
                if frames_below >= CONSEC_FRAMES and not blink_in_progress:
                    blink_in_progress = True
                    now = time.time()
                    # Double-blink detection
                    if now - last_blink_time <= DOUBLE_BLINK_WINDOW:
                        blink_count += 1
                    else:
                        blink_count = 1
                    last_blink_time = now

                    if blink_count >= 2 and (now - last_action_time >= CLICK_COOLDOWN):
                        run_action("double_blink")
                        last_action_time = now
                        blink_count = 0
                # Hold detection
                if not hold_fired and closed_start and (time.time() - closed_start) >= HOLD_SECONDS:
                    if (time.time() - last_action_time) >= CLICK_COOLDOWN:
                        run_action("blink_hold")
                        last_action_time = time.time()
                    hold_fired = True
            else:
                frames_below = 0
                blink_in_progress = False
                closed_start = None
                hold_fired = False

            if SHOW_DEBUG:
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

            if SHOW_DEBUG:
                for p in pts:
                    cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 0), -1)

        if is_open_palm and not open_palm_active:
            run_action("open_palm")
        open_palm_active = is_open_palm

        now = time.time()
        dt = now - fps_t
        if dt > 0:
            fps = 1.0 / dt
        fps_t = now

        if SHOW_DEBUG:
            if ear is not None:
                cv2.putText(frame, f"EAR: {ear:.3f} (thr={EAR_THRESHOLD:.2f})", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Open Palm: {'YES' if is_open_palm else 'NO'}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        if SHOW_WINDOW:
            cv2.imshow("Shortcut Controller (press q to quit)", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
        else:
            time.sleep(0.01)

    cap.release()
    if SHOW_WINDOW:
        cv2.destroyAllWindows()

    if stt_proc and stt_proc.poll() is None:
        stt_proc.terminate()


if __name__ == "__main__":
    main()
