import cv2
import time
import numpy as np
import mediapipe as mp

# -----------------------------
# Hand wave detection via MediaPipe Hands
# Detects left-right oscillation of the hand center.
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


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

    # ---- Tunable parameters ----
    WAVE_MIN_AMPLITUDE_PX = 80   # min left-right travel to consider a wave
    WAVE_MIN_OSCILLATIONS = 2    # number of direction changes
    WINDOW_SECONDS = 1.2         # time window to detect oscillations
    SHOW_DEBUG = True

    wave_count = 0

    # Tracking buffers
    positions = []  # list of (t, x)
    last_dir = 0
    dir_changes = 0

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

        hand_center = None

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            pts = normalized_to_pixel_coords(lm, w, h)

            # Use palm center approximation: average of wrist + MCP joints.
            # Landmarks: 0=wrist, 5=index_mcp, 9=middle_mcp, 13=ring_mcp, 17=pinky_mcp
            palm_idx = [0, 5, 9, 13, 17]
            palm_pts = pts[palm_idx]
            hand_center = palm_pts.mean(axis=0)

            x, y = int(hand_center[0]), int(hand_center[1])
            cv2.circle(frame, (x, y), 6, (0, 255, 255), -1)

            # Draw landmarks
            for p in pts:
                cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 0), -1)

        now = time.time()

        if hand_center is not None:
            positions.append((now, hand_center[0]))
            # Keep only recent positions
            positions = [(t, x) for (t, x) in positions if (now - t) <= WINDOW_SECONDS]

            if len(positions) >= 2:
                # Detect direction changes
                _, x_prev = positions[-2]
                x_curr = positions[-1][1]
                dx = x_curr - x_prev
                dir_now = 1 if dx > 2 else (-1 if dx < -2 else 0)
                if dir_now != 0 and last_dir != 0 and dir_now != last_dir:
                    dir_changes += 1
                if dir_now != 0:
                    last_dir = dir_now

                # Check amplitude
                xs = [x for (_, x) in positions]
                if (max(xs) - min(xs)) >= WAVE_MIN_AMPLITUDE_PX and dir_changes >= WAVE_MIN_OSCILLATIONS:
                    wave_count += 1
                    dir_changes = 0
                    last_dir = 0
                    positions.clear()

        # FPS calculation
        dt = now - fps_t
        if dt > 0:
            fps = 1.0 / dt
        fps_t = now

        # Overlay text
        cv2.putText(frame, f"Waves: {wave_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        if SHOW_DEBUG:
            cv2.putText(frame, f"Dir changes: {dir_changes}", (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("MediaPipe Hand Wave Detector (press q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
