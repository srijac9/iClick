import cv2
import mediapipe as mp

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    refine_landmarks=True,  # REQUIRED for iris tracking
    max_num_faces=1
)

cap = cv2.VideoCapture(0)