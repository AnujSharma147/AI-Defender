import torch
import torch.nn as nn
import librosa
import numpy as np
import os
from torchvision import models

MODEL_PATH = "models/Audio_Detect_System.pth"

device = "cuda" if torch.cuda.is_available() else "cpu"

_model = None
_error = None


# -------- LOAD MODEL --------
def load_model():
    global _model, _error

    if _model is not None:
        return _model

    if not os.path.exists(MODEL_PATH):
        _error = "Audio model not found"
        return None

    try:
        # ✅ MODEL STRUCTURE recreate
        model = models.resnet18(pretrained=False)
        model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        model.fc = nn.Linear(512, 2)

        # ✅ LOAD WEIGHTS
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))

        model.to(device)
        model.eval()

        print("[INFO] Audio model loaded")

        _model = model
        return _model

    except Exception as e:
        _error = str(e)
        print("[ERROR]", _error)
        return None


# -------- AUDIO → MEL --------
def audio_to_mel(file):
    y, sr = librosa.load(file, sr=16000)

    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel = librosa.power_to_db(mel)

    mel = np.resize(mel, (128, 128))
    mel = np.expand_dims(mel, axis=0)

    return torch.tensor(mel, dtype=torch.float32)


# -------- MAIN FUNCTION --------
def detect_audio(path):

    model = load_model()

    if model is None:
        return {"error": _error}

    try:
        mel = audio_to_mel(path).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(mel)
            probs = torch.softmax(output, dim=1)

        real = float(probs[0][0]) * 100
        fake = float(probs[0][1]) * 100

        return {
            "real": round(real, 2),
            "fake": round(fake, 2),
            "verdict": "fake" if fake > real else "real"
        }

    except Exception as e:
        return {"error": str(e)}