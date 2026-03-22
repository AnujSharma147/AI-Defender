import os

# current backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# model path
MODEL_PATH = os.path.join(BASE_DIR, "models", "object_model.pt")

_model = None
_model_error = None


def load_model():
    global _model, _model_error

    if _model is not None:
        return _model

    if _model_error is not None:
        return None

    if not os.path.exists(MODEL_PATH):
        _model_error = f"Model file not found: {MODEL_PATH}"
        print(_model_error)
        return None

    try:
        from ultralytics import YOLO

        print(f"[INFO] Loading YOLO model from {MODEL_PATH}")

        _model = YOLO(MODEL_PATH)

        print("[INFO] YOLO model loaded successfully")

        return _model

    except Exception as e:
        _model_error = str(e)
        print("[ERROR] Model loading failed:", e)
        return None


def detect_objects(image_path: str):

    model = load_model()

    if model is None:
        return [
            {
                "object": "model_unavailable",
                "confidence": 0.0,
                "reason": _model_error
            }
        ]

    try:

        results = model(image_path)

        detections = []

        for r in results:

            if r.boxes is None:
                continue

            for box in r.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                detections.append({
                    "object": model.names[class_id],
                    "confidence": round(confidence, 3)
                })

        # अगर कुछ detect नहीं हुआ
        if len(detections) == 0:
            return [{
                "object": "no_objects_detected",
                "confidence": 0.0
            }]

        # --------------------------------
        # REMOVE DUPLICATE OBJECTS
        # --------------------------------

        cleaned = {}

        for det in detections:

            obj = det["object"]
            conf = det["confidence"]

            if obj not in cleaned or conf > cleaned[obj]:
                cleaned[obj] = conf

        final_detections = []

        for obj, conf in cleaned.items():
            final_detections.append({
                "object": obj,
                "confidence": conf
            })

        return final_detections

    except Exception as e:

        return [{
            "object": "inference_failed",
            "confidence": 0.0,
            "reason": str(e)
        }]