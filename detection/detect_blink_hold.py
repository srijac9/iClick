import cv2
import time
import numpy as np
import mediapipe as mp

# -----------------------------
# Blink + Blink-Hold detection via EAR using MediaPipe Face Mesh
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


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

    # ---- Tunable parameters ----
    EAR_THRESHOLD = 0.21
    CONSEC_FRAMES = 2
    HOLD_SECONDS = 0.7   # closed-eye duration to count as "blink-hold"
    SHOW_DEBUG = True

    blink_count = 0
    hold_count = 0
    frames_below = 0
    blink_in_progress = False
    hold_fired = False
    closed_start = None

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
        results = face_mesh.process(rgb)
        rgb.flags.writeable = True

        ear = None

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0].landmark
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
                    blink_count += 1
                # Hold detection
                if not hold_fired and closed_start:
                    if (time.time() - closed_start) >= HOLD_SECONDS:
                        hold_count += 1
                        hold_fired = True
            else:
                frames_below = 0
                blink_in_progress = False
                closed_start = None
                hold_fired = False

            for idx in LEFT_EYE + RIGHT_EYE:
                x, y = pts[idx].astype(int)
                cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

        now = time.time()
        dt = now - fps_t
        if dt > 0:
            fps = 1.0 / dt
        fps_t = now

        cv2.putText(frame, f"Blinks: {blink_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(frame, f"Holds: {hold_count}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        if SHOW_DEBUG:
            if ear is not None:
                cv2.putText(frame, f"EAR: {ear:.3f}  (thr={EAR_THRESHOLD:.2f})", (20, 120),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, 160),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("MediaPipe Blink+Hold Detector (press q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
