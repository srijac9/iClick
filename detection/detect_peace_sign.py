import cv2
import sys
import numpy as np
import mediapipe as mp


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


def main(camera_index=0):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam. Try changing VideoCapture index (0/1/2).")

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cv2.namedWindow("Peace Sign Detector (press q to quit)", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Peace Sign Detector (press q to quit)", 960, 540)

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            hand_results = hands.process(rgb)
            rgb.flags.writeable = True

            peace = False
            if hand_results.multi_hand_landmarks:
                lm = hand_results.multi_hand_landmarks[0].landmark
                pts = normalized_to_pixel_coords(lm, w, h)
                peace = (
                    is_finger_extended(pts, 8, 6, 5)
                    and is_finger_extended(pts, 12, 10, 9)
                    and not is_finger_extended(pts, 16, 14, 13)
                    and not is_finger_extended(pts, 20, 18, 17)
                )
                for p in pts:
                    cv2.circle(frame, (int(p[0]), int(p[1])), 2, (0, 255, 0), -1)

            if peace:
                cv2.putText(frame, "PEACE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            cv2.imshow("Peace Sign Detector (press q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    idx = 0
    if len(sys.argv) > 1:
        try:
            idx = int(sys.argv[1])
        except ValueError:
            idx = 0
    main(idx)
