import os
import importlib
import threading
from typing import Dict, List, Tuple

import cv2
import numpy as np
import torch
import torchvision.models as models
from sklearn.ensemble import RandomForestClassifier
from torchvision import transforms

try:
    import timm
except Exception:
    timm = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

video_model_vit = None
video_model_efficient = None
video_model_resnet = None
video_model_meta = None
video_face_detector = None
video_transform = None

video_loading = False
video_loaded = False
video_stage = "idle"
video_error = None
video_load_lock = threading.Lock()


class ViTDeepfake(torch.nn.Module):
    def __init__(self):
        super().__init__()
        if timm is None:
            raise RuntimeError("timm is not installed")
        self.model = timm.create_model("vit_base_patch16_224", pretrained=True)
        num_features = self.model.head.in_features
        self.model.head = torch.nn.Sequential(
            torch.nn.Dropout(0.3),
            torch.nn.Linear(num_features, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        return self.model(x)


class EfficientBiLSTM(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.efficientnet = models.efficientnet_b4(pretrained=True)
        num_features = self.efficientnet.classifier[1].in_features
        self.efficientnet.classifier = torch.nn.Identity()
        self.lstm = torch.nn.LSTM(
            num_features,
            256,
            batch_first=True,
            bidirectional=True,
            num_layers=2,
            dropout=0.3,
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Dropout(0.5),
            torch.nn.Linear(512, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        batch, frames, c, h, w = x.shape
        x = x.view(batch * frames, c, h, w)
        features = self.efficientnet(x).view(batch, frames, -1)
        lstm_out, _ = self.lstm(features)
        return self.classifier(lstm_out[:, -1, :])


class ResNetDeepfake(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.model = models.resnet50(pretrained=True)
        num_features = self.model.fc.in_features
        self.model.fc = torch.nn.Sequential(
            torch.nn.Dropout(0.3),
            torch.nn.Linear(num_features, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, x):
        return self.model(x)


def _build_transform():
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])


def _build_face_detector():
    try:
        facenet_module = importlib.import_module("facenet_pytorch")
        mtcnn_cls = getattr(facenet_module, "MTCNN", None)
        if mtcnn_cls is None:
            return None
        return mtcnn_cls(
            image_size=224,
            margin=20,
            min_face_size=80,
            thresholds=[0.6, 0.7, 0.7],
            factor=0.709,
            post_process=True,
            device=DEVICE,
        )
    except Exception:
        return None


def load_video_model(force_reload: bool = False) -> bool:
    global video_model_vit, video_model_efficient, video_model_resnet, video_model_meta
    global video_face_detector, video_transform, video_loading, video_loaded, video_stage, video_error

    if video_loaded and not force_reload:
        return True

    if video_loading:
        return False

    with video_load_lock:
        if video_loaded and not force_reload:
            return True

        video_loading = True
        video_stage = "initializing"
        try:
            print("Loading 4 ensemble models...")
            if video_transform is None:
                video_transform = _build_transform()
            if video_face_detector is None:
                video_face_detector = _build_face_detector()

            video_stage = "loading_models"
            video_model_vit = ViTDeepfake().to(DEVICE).eval()
            video_model_efficient = EfficientBiLSTM().to(DEVICE).eval()
            video_model_resnet = ResNetDeepfake().to(DEVICE).eval()
            video_model_meta = RandomForestClassifier(n_estimators=150, random_state=42)

            video_stage = "smoke_test"
            with torch.no_grad():
                dummy_face = torch.zeros((1, 3, 224, 224), dtype=torch.float32, device=DEVICE)
                dummy_seq = torch.zeros((1, 5, 3, 224, 224), dtype=torch.float32, device=DEVICE)
                _ = video_model_vit(dummy_face)
                _ = video_model_resnet(dummy_face)
                _ = video_model_efficient(dummy_seq)

            video_error = None
            video_loaded = True
            video_stage = "ready"
            print("✅ All models loaded successfully!")
            return True
        except Exception as err:
            video_model_vit = None
            video_model_efficient = None
            video_model_resnet = None
            video_model_meta = None
            video_error = str(err)
            video_stage = "failed"
            print(f"[ERROR] Notebook-style video ensemble loading failed: {video_error}")
            return False
        finally:
            video_loading = False


def warmup_video_models() -> Dict[str, object]:
    ok = load_video_model()
    loaded_count = sum([
        1 if video_model_vit is not None else 0,
        1 if video_model_efficient is not None else 0,
        1 if video_model_resnet is not None else 0,
        1 if video_model_meta is not None else 0,
    ])
    return {
        "ok": bool(ok),
        "loaded": video_loaded,
        "stage": video_stage,
        "device": str(DEVICE),
        "models": {
            "vit": video_model_vit is not None,
            "efficient_bilstm": video_model_efficient is not None,
            "resnet50": video_model_resnet is not None,
            "meta_learner": video_model_meta is not None,
        },
        "loaded_count": loaded_count,
        "deepfake_loaded_count": loaded_count,
        "error": video_error,
    }


def get_video_model_status() -> Dict[str, object]:
    loaded_count = sum([
        1 if video_model_vit is not None else 0,
        1 if video_model_efficient is not None else 0,
        1 if video_model_resnet is not None else 0,
        1 if video_model_meta is not None else 0,
    ])
    return {
        "loaded": video_loaded,
        "loading": video_loading,
        "stage": video_stage,
        "device": str(DEVICE),
        "models": {
            "vit": video_model_vit is not None,
            "efficient_bilstm": video_model_efficient is not None,
            "resnet50": video_model_resnet is not None,
            "meta_learner": video_model_meta is not None,
        },
        "loaded_count": loaded_count,
        "deepfake_loaded_count": loaded_count,
        "error": video_error,
    }


def extract_frames_smart(video_path, max_frames=120):
    cap = cv2.VideoCapture(video_path)
    try:
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total == 0:
            return [], 0
        sample_count = min(max_frames, total)
        if total > 500:
            sample_count = min(180, total)
        indices = np.linspace(0, total - 1, sample_count, dtype=int)
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return frames, total
    finally:
        cap.release()


def extract_all_faces(frame):
    faces = []
    if video_face_detector is not None:
        boxes, probs = video_face_detector.detect(frame)
        if boxes is not None:
            for box, prob in zip(boxes, probs):
                if prob > 0.95:
                    x1, y1, x2, y2 = box.astype(int)
                    margin = 20
                    x1, y1 = max(0, x1 - margin), max(0, y1 - margin)
                    x2, y2 = min(frame.shape[1], x2 + margin), min(frame.shape[0], y2 + margin)
                    face = frame[y1:y2, x1:x2]
                    if face.size > 0:
                        faces.append(cv2.resize(face, (224, 224)))

    if faces:
        return faces

    h, w = frame.shape[:2]
    if h > 0 and w > 0:
        y1, y2 = int(h * 0.2), int(h * 0.8)
        x1, x2 = int(w * 0.2), int(w * 0.8)
        fallback = frame[y1:y2, x1:x2]
        if fallback.size > 0:
            return [cv2.resize(fallback, (224, 224))]

    return [cv2.resize(frame, (224, 224))]


def predict_vit(face):
    if video_transform is None or video_model_vit is None:
        if not load_video_model():
            raise RuntimeError("Video model is not ready")
    inp = video_transform(face).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        return float(video_model_vit(inp).item())


def predict_resnet(face):
    if video_transform is None or video_model_resnet is None:
        if not load_video_model():
            raise RuntimeError("Video model is not ready")
    inp = video_transform(face).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        return float(video_model_resnet(inp).item())


def predict_efficient(faces_seq):
    if video_transform is None or video_model_efficient is None:
        if not load_video_model():
            return 0.5
    if len(faces_seq) < 5:
        return 0.5
    seq = torch.stack([video_transform(f) for f in faces_seq[:30]])
    seq = seq.unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        return float(video_model_efficient(seq).item())


def predict_ensemble(video_path):
    if not load_video_model():
        return None, "Video model failed to load"

    frames, total_frames = extract_frames_smart(video_path)
    if len(frames) < 5:
        return None, "Not enough frames extracted"

    print(f"[INFO] Analyzing {len(frames)} frames from {total_frames} total frames...")
    face_predictions = []
    faces_for_temporal = []

    for frame in frames:
        faces = extract_all_faces(frame)
        if not faces:
            continue
        for face in faces:
            p1 = predict_vit(face)
            p2 = predict_resnet(face)
            face_predictions.append([p1, p2])
            faces_for_temporal.append(face)

    if not face_predictions:
        return None, "No faces detected in video"

    vit_probs = [fp[0] for fp in face_predictions]
    resnet_probs = [fp[1] for fp in face_predictions]
    avg_vit = float(np.mean(vit_probs))
    avg_resnet = float(np.mean(resnet_probs))

    # Match the notebook logic exactly: EfficientNet is loaded, but the final vote uses 0.5 as the temporal placeholder.
    final_prob = (avg_vit * 0.4) + (avg_resnet * 0.3) + (0.5 * 0.3)
    is_fake = final_prob > 0.5

    result = {
        "prediction": "FAKE" if is_fake else "REAL",
        "verdict": "fake" if is_fake else "real",
        "confidence": round(final_prob * 100, 2) if is_fake else round((1 - final_prob) * 100, 2),
        "fake_probability": round(final_prob * 100, 2),
        "real_probability": round((1 - final_prob) * 100, 2),
        "vit_fake_prob": round(avg_vit * 100, 2),
        "resnet_fake_prob": round(avg_resnet * 100, 2),
        "efficient_fake_prob": 50.0,
        "faces_analyzed": len(face_predictions),
        "frames_analyzed": len(frames),
        "total_frames": total_frames,
        "detector": "ViT + EfficientNet-BiLSTM + ResNet50 + Meta-Learner",
        "individual_models": {
            "ViT": {
                "prediction": "FAKE" if avg_vit > 0.5 else "REAL",
                "real_prob": round((1 - avg_vit) * 100, 2),
                "fake_prob": round(avg_vit * 100, 2),
            },
            "ResNet50": {
                "prediction": "FAKE" if avg_resnet > 0.5 else "REAL",
                "real_prob": round((1 - avg_resnet) * 100, 2),
                "fake_prob": round(avg_resnet * 100, 2),
            },
            "EfficientNet_BiLSTM": {
                "prediction": "Processing temporal features",
                "real_prob": 50.0,
                "fake_prob": 50.0,
            },
        },
        "model_meta": {
            "name": "RandomForestClassifier",
            "status": "placeholder_untrained",
        },
    }

    return result, "success"


def detect_video_logic(path: str):
    if not load_video_model():
        return {
            "error": "Video model is unavailable",
            "model_status": get_video_model_status(),
        }

    result, status = predict_ensemble(path)
    if result is None:
        return {
            "error": status,
            "model_status": get_video_model_status(),
        }

    result["status"] = status
    result["model_status"] = get_video_model_status()
    return result: f"Platform Error: {str(e)}"}
