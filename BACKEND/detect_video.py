import cv2
import os
from ultralytics import YOLO
from transformers import pipeline
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "models", "object_model.pt")
DEEPFAKE_MODEL_ID = "Ammar2k/videomae-base-finetuned-deepfake-subset"

_deepfake_pipe = None
_yolo_model = None
_video_model_error = None


def _load_video_models():
    global _deepfake_pipe, _yolo_model, _video_model_error

    if _video_model_error is not None:
        return None, None

    if _deepfake_pipe is None:
        print("[INFO] Loading video deepfake model...")
        try:
            _deepfake_pipe = pipeline("video-classification", model=DEEPFAKE_MODEL_ID)
            print("[INFO] Video deepfake model loaded")
        except Exception as e:
            _video_model_error = f"Deepfake model load failed: {e}"
            print(f"[ERROR] {_video_model_error}")
            return None, None

    if _yolo_model is None:
        print("[INFO] Loading YOLO video object model...")
        if not os.path.exists(YOLO_MODEL_PATH):
            _video_model_error = f"YOLO model file not found: {YOLO_MODEL_PATH}"
            print(f"[ERROR] {_video_model_error}")
            return None, None
        try:
            _yolo_model = YOLO(YOLO_MODEL_PATH)
            print("[INFO] YOLO video object model loaded")
        except Exception as e:
            _video_model_error = f"YOLO model load failed: {e}"
            print(f"[ERROR] {_video_model_error}")
            return None, None

    return _deepfake_pipe, _yolo_model


def warmup_video_models():
    deepfake_pipe, yolo_model = _load_video_models()
    if deepfake_pipe is None or yolo_model is None:
        return {"ok": False, "error": _video_model_error or "video models unavailable"}
    return {"ok": True, "deepfake_model": DEEPFAKE_MODEL_ID, "object_model": YOLO_MODEL_PATH}


def get_video_model_status():
    return {
        "deepfake_loaded": _deepfake_pipe is not None,
        "yolo_loaded": _yolo_model is not None,
        "error": _video_model_error,
        "deepfake_model": DEEPFAKE_MODEL_ID,
        "object_model": YOLO_MODEL_PATH,
    }


def _normalize_verdict(label: str) -> str:
    lower = (label or "").strip().lower()
    if lower in {"bonafide", "real", "genuine", "label_0"}:
        return "REAL"
    if lower in {"fake", "deepfake", "spoof", "label_1"}:
        return "FAKE"
    if "real" in lower or "bonafide" in lower or "genuine" in lower:
        return "REAL"
    return "FAKE"

def detect_video_logic(video_path):
    try:
        deepfake_pipe, yolo_model = _load_video_models()

        if deepfake_pipe is None or yolo_model is None:
            return {"error": _video_model_error or "Video models are unavailable"}

        if not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}

        # ---- PART 1: Deepfake Detection (FAST) ----
        print("[1/2] Analyzing video for deepfake artifacts...")
        fake_results = deepfake_pipe(video_path)
        if not fake_results:
            return {"error": "Deepfake model returned empty prediction"}

        top_fake = fake_results[0]
        label = str(top_fake.get("label", ""))
        score = float(top_fake.get("score", 0.0))
        verdict = _normalize_verdict(label)
        deepfake_confidence = round(score * 100, 2)

        # ---- PART 2: Object Detection (With Progress Bar) ----
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {"error": f"Could not open video file: {video_path}"}

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            total_frames = 1

        # Process sampled frames to reduce latency while retaining object coverage.
        target_frames = min(120, total_frames)
        frame_stride = max(1, total_frames // target_frames)
        sampled_total = (total_frames + frame_stride - 1) // frame_stride
        unique_objects = {}

        print("[2/2] Scanning objects in video...")
        processed = 0
        frame_index = 0
        with tqdm(total=sampled_total, desc="Deep-Defend Scan", unit="sample") as pbar:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_index % frame_stride != 0:
                    frame_index += 1
                    continue

                h, w = frame.shape[:2]
                if w > 960:
                    scale = 960.0 / float(w)
                    resized = cv2.resize(frame, (960, int(h * scale)), interpolation=cv2.INTER_AREA)
                else:
                    resized = frame

                # verbose=False keeps per-frame spam lines hidden.
                results = yolo_model.predict(resized, verbose=False, stream=False, conf=0.35)
                
                for r in results:
                    if r.boxes is None:
                        continue
                    for box in r.boxes:
                        obj_name = yolo_model.names[int(box.cls[0])]
                        conf = float(box.conf[0])
                        # Sirf best confidence wala object store karein
                        if obj_name not in unique_objects or conf > unique_objects[obj_name]:
                            unique_objects[obj_name] = conf
                
                pbar.update(1)
                processed += 1
                frame_index += 1
        
        cap.release()

        # ---- PART 3: Format Output (Exactly like your screenshot) ----
        # Sirf high-confidence objects return karein (40% se upar)
        detections = [
            {"object": k, "confidence": round(v, 3)}
            for k, v in unique_objects.items()
            if v > 0.4
        ]
        
        return {
            "type": "video",
            "deepfake_result": {
                "verdict": verdict,
                "label": label,
                "confidence": f"{deepfake_confidence}%"
            },
            "analysis": {
                "total_frames": total_frames,
                "sampled_frames": processed,
                "frame_stride": frame_stride,
            },
            "detections": detections
        }

    except Exception as e:
        return {"error": f"Platform Error: {str(e)}"}