import cv2
import time
import numpy as np
import mediapipe as mp

# -----------------------------
# Open palm detection via MediaPipe Hands
# -----------------------------

mp_hands = mp.solutions.hands

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def normalized_to_pixel_coords(landmarks, w, h):
    pts = np.zeros((len(landmarks), 2), dtype=np.float32)
    for i, lm in enumerate(landmarks):
        pts[i] = (lm.x * w, lm.y * h)
    return pts


def is_finger_extended(pts, tip_idx, pip_idx, mcp_idx):
    # Compare distances to wrist: if tip is farther than PIP and MCP, finger is likely extended.
    wrist = pts[0]
    tip = pts[tip_idx]
    pip = pts[pip_idx]
    mcp = pts[mcp_idx]
    return np.linalg.norm(tip - wrist) > np.linalg.norm(pip - wrist) > np.linalg.norm(mcp - wrist)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

    SHOW_DEBUG = True
    open_palm_count = 0
    open_palm_active = False

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
        results = hands.process(rgb)
        rgb.flags.writeable = True

        is_open_palm = False

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            pts = normalized_to_pixel_coords(lm, w, h)

            # Finger indices (tip, pip, mcp)
            fingers = [
                (8, 6, 5),   # index
                (12, 10, 9), # middle
                (16, 14, 13),# ring
                (20, 18, 17) # pinky
            ]

            extended = 0
            for tip, pip, mcp in fingers:
                if is_finger_extended(pts, tip, pip, mcp):
                    extended += 1

            # Thumb check (tip 4, ip 3, mcp 2) using wrist distance heuristic
            thumb_extended = np.linalg.norm(pts[4] - pts[0]) > np.linalg.norm(pts[3] - pts[0]) > np.linalg.norm(pts[2] - pts[0])

            if extended >= 3 and thumb_extended:
                is_open_palm = True

            # Draw landmarks
            for p in pts:
                cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 0), -1)

        if is_open_palm and not open_palm_active:
            open_palm_count += 1
            open_palm_active = True
        elif not is_open_palm:
            open_palm_active = False

        now = time.time()
        dt = now - fps_t
        if dt > 0:
            fps = 1.0 / dt
        fps_t = now

        cv2.putText(frame, f"Open Palm: {'YES' if is_open_palm else 'NO'}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Count: {open_palm_count}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        if SHOW_DEBUG:
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("MediaPipe Open Palm Detector (press q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
