import torch
import torch.nn as nn
import librosa
import numpy as np
import os
from transformers import (
    Wav2Vec2ForSequenceClassification,
    Wav2Vec2FeatureExtractor,
    WavLMModel
)
import warnings
warnings.filterwarnings('ignore')

# ================================
# MODEL CONFIG - 3 ENSEMBLE MODELS
# ================================
MODEL1_NAME = "abhishtagatya/wav2vec2-base-960h-itw-deepfake"
MODEL2_NAME = "Gustking/wav2vec2-large-xlsr-deepfake-audio-classification"
MODEL3_BASE = "microsoft/wavlm-base"

# Global model cache
_models = {
    "model1": None,
    "feat1": None,
    "model2": None,
    "feat2": None,
    "model3": None,
    "feat3": None,
    "loaded": False
}
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
_error = None
_loading_in_progress = False
_loading_stage = "idle"  # Track which stage is loading


# ================================
# WAVLM CLASSIFIER (Custom Head)
# ================================
class WavLMClassifier(nn.Module):
    def __init__(self, base_model, hidden_size=768, num_classes=2):
        super().__init__()
        self.base_model = base_model
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, input_values):
        outputs = self.base_model(input_values)
        pooled = outputs.last_hidden_state.mean(dim=1)
        return self.classifier(pooled)


# ================================
# OPTIMIZED MODEL LOADING
# ================================
def load_ensemble_models():
    """Load 3-model ensemble with better error handling"""
    global _models, _error, _loading_in_progress, _loading_stage
    
    # Already loaded
    if _models["loaded"]:
        return True
    
    # Currently loading
    if _loading_in_progress:
        return False
    
    _loading_in_progress = True
    _loading_stage = "initializing"
    
    try:
        print("[INFO] 🚀 Loading 3-Model Ensemble System...")
        
        # Load Model 1 - Fast Wav2Vec2
        try:
            _loading_stage = "loading_model1"
            print("[INFO] ⏳ Loading Model 1 (Wav2Vec2 Deepfake)...")
            _models["feat1"] = Wav2Vec2FeatureExtractor.from_pretrained(
                MODEL1_NAME, 
                cache_dir="./model_cache"
            )
            _models["model1"] = Wav2Vec2ForSequenceClassification.from_pretrained(
                MODEL1_NAME,
                cache_dir="./model_cache"
            ).to(_device)
            _models["model1"].eval()
            print("[SUCCESS] ✓ Model 1 ready")
        except Exception as e:
            print(f"[WARNING] Model 1 failed: {str(e)[:100]}...")
            _models["model1"] = None
        
        # Load Model 2 - Fallback Wav2Vec2
        try:
            _loading_stage = "loading_model2"
            print("[INFO] ⏳ Loading Model 2 (Wav2Vec2 Fallback)...")
            _models["feat2"] = Wav2Vec2FeatureExtractor.from_pretrained(
                MODEL2_NAME,
                cache_dir="./model_cache"
            )
            _models["model2"] = Wav2Vec2ForSequenceClassification.from_pretrained(
                MODEL2_NAME,
                cache_dir="./model_cache"
            ).to(_device)
            _models["model2"].eval()
            print("[SUCCESS] ✓ Model 2 ready")
        except Exception as e:
            print(f"[WARNING] Model 2 failed: {str(e)[:100]}...")
            _models["model2"] = None
        
        # Load Model 3 - WavLM
        try:
            _loading_stage = "loading_model3"
            print("[INFO] ⏳ Loading Model 3 (WavLM)...")
            _models["feat3"] = Wav2Vec2FeatureExtractor.from_pretrained(
                "facebook/wav2vec2-base",
                cache_dir="./model_cache"
            )
            wavlm_base = WavLMModel.from_pretrained(
                MODEL3_BASE,
                cache_dir="./model_cache"
            ).to(_device)
            wavlm_base.eval()
            _models["model3"] = WavLMClassifier(wavlm_base).to(_device)
            _models["model3"].eval()
            print("[SUCCESS] ✓ Model 3 ready")
        except Exception as e:
            print(f"[WARNING] Model 3 failed: {str(e)[:100]}...")
            _models["model3"] = None
        
        # Check if at least 2 models loaded
        loaded_count = sum([1 for m in [_models["model1"], _models["model2"], _models["model3"]] if m is not None])
        
        if loaded_count >= 2:
            _models["loaded"] = True
            _loading_stage = "complete"
            print(f"[SUCCESS] ✅ Ensemble ready with {loaded_count}/3 models")
            _loading_in_progress = False
            return True
        else:
            _error = f"Only {loaded_count} models loaded (need ≥2)"
            _loading_stage = "failed"
            print(f"[ERROR] {_error}")
            _loading_in_progress = False
            return False
    
    except Exception as e:
        _error = str(e)
        _loading_stage = "failed"
        print(f"[CRITICAL ERROR] {_error}")
        _loading_in_progress = False
        return False


# ================================
# AUDIO PREPROCESSING
# ================================
def preprocess_audio(audio_path, target_sr=16000, max_len=16000*4):
    """Load and preprocess audio (4 seconds max)"""
    try:
        waveform, sr = librosa.load(audio_path, sr=target_sr, mono=True)
        
        # Pad or truncate to fixed length
        if len(waveform) < max_len:
            waveform = np.pad(waveform, (0, max_len - len(waveform)))
        else:
            waveform = waveform[:max_len]
        
        return waveform
    except Exception as e:
        print(f"[ERROR] Audio preprocessing: {e}")
        return None


# ================================
# SAFE PREDICTION FUNCTIONS
# ================================
def predict_model1(waveform):
    """Model 1 prediction with fallback"""
    if _models["model1"] is None or _models["feat1"] is None:
        return 50.0, 50.0, "UNKNOWN"
    
    try:
        inputs = _models["feat1"](waveform, sampling_rate=16000, return_tensors="pt")
        input_values = inputs.input_values.to(_device)
        
        with torch.no_grad():
            logits = _models["model1"](input_values).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        
        # Convert numpy to Python native floats
        real_prob = float(probs[0] * 100)
        fake_prob = float(probs[1] * 100)
        pred = "REAL" if real_prob > fake_prob else "FAKE"
        return real_prob, fake_prob, pred
    except Exception as e:
        print(f"[WARNING] Model1 prediction error: {str(e)[:80]}")
        return 50.0, 50.0, "ERROR"


def predict_model2(waveform):
    """Model 2 prediction with fallback"""
    if _models["model2"] is None or _models["feat2"] is None:
        return 50.0, 50.0, "UNKNOWN"
    
    try:
        inputs = _models["feat2"](waveform, sampling_rate=16000, return_tensors="pt")
        input_values = inputs.input_values.to(_device)
        
        with torch.no_grad():
            logits = _models["model2"](input_values).logits
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        
        # Convert numpy to Python native floats
        real_prob = float(probs[0] * 100)
        fake_prob = float(probs[1] * 100)
        pred = "REAL" if real_prob > fake_prob else "FAKE"
        return real_prob, fake_prob, pred
    except Exception as e:
        print(f"[WARNING] Model2 prediction error: {str(e)[:80]}")
        return 50.0, 50.0, "ERROR"


def predict_model3(waveform):
    """Model 3 prediction with fallback"""
    if _models["model3"] is None or _models["feat3"] is None:
        return 50.0, 50.0, "UNKNOWN"
    
    try:
        inputs = _models["feat3"](waveform, sampling_rate=16000, return_tensors="pt")
        input_values = inputs.input_values.to(_device)
        
        with torch.no_grad():
            logits = _models["model3"](input_values)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        
        # Convert numpy to Python native floats
        real_prob = float(probs[0] * 100)
        fake_prob = float(probs[1] * 100)
        pred = "REAL" if real_prob > fake_prob else "FAKE"
        return real_prob, fake_prob, pred
    except Exception as e:
        print(f"[WARNING] Model3 prediction error: {str(e)[:80]}")
        return 50.0, 50.0, "ERROR"


# ================================
# MAIN ENSEMBLE DETECTION FUNCTION
# ================================
def detect_audio_logic(path):
    """3-Model Ensemble with Majority Voting - Simplified"""
    
    if not os.path.exists(path):
        return {"error": "Audio file not found"}

    try:
        # Preprocess audio
        audio, sr = librosa.load(path, sr=16000)
        duration = len(audio) / 16000
        print(f"[INFO] Audio: {round(duration, 2)}s")

        waveform = preprocess_audio(path)
        if waveform is None:
            return {"error": "Could not preprocess audio"}

        # Load models on first use
        if not _models["loaded"]:
            print("[INFO] First-time model loading...")
            load_ensemble_models()

        # Get predictions from all 3 models
        print("[INFO] Running Model 1...")
        real1, fake1, pred1 = predict_model1(waveform)
        
        print("[INFO] Running Model 2...")
        real2, fake2, pred2 = predict_model2(waveform)
        
        print("[INFO] Running Model 3...")
        real3, fake3, pred3 = predict_model3(waveform)

        # Majority voting
        votes = [pred1, pred2, pred3]
        valid_votes = [v for v in votes if v not in ["ERROR", "UNKNOWN"]]
        
        if len(valid_votes) < 2:
            return {"error": "Not enough valid model predictions"}
        
        real_votes = valid_votes.count("REAL")
        fake_votes = valid_votes.count("FAKE")
        
        final_is_fake = fake_votes > real_votes
        final_prediction = "FAKE (AI-Generated)" if final_is_fake else "REAL (Human Voice)"

        # Calculate ensemble confidence - Convert numpy to Python native types
        real_avg = float((float(real1) + float(real2) + float(real3)) / 3)
        fake_avg = float((float(fake1) + float(fake2) + float(fake3)) / 3)
        confidence = float(max(real_avg, fake_avg))

        print(f"[SUCCESS] Prediction: {final_prediction} ({confidence:.1f}%)")

        return {
            "prediction": final_prediction,
            "confidence": float(confidence),
            "confidence_str": f"{float(confidence):.2f}%",
            "real_prob_avg": float(real_avg),
            "fake_prob_avg": float(fake_avg),
            "verdict": "fake" if final_is_fake else "real",
            "votes": {
                "REAL": int(real_votes),
                "FAKE": int(fake_votes)
            },
            "individual_models": {
                "Model1_Wav2Vec2_Deepfake": {
                    "prediction": str(pred1),
                    "real_prob": float(real1),
                    "fake_prob": float(fake1)
                },
                "Model2_Wav2Vec2_Fallback": {
                    "prediction": str(pred2),
                    "real_prob": float(real2),
                    "fake_prob": float(fake2)
                },
                "Model3_WavLM_Specialized": {
                    "prediction": str(pred3),
                    "real_prob": float(real3),
                    "fake_prob": float(fake3)
                }
            },
            "duration_sec": float(duration),
            "model": "3-Model Ensemble (Wav2Vec2 + WavLM)",
            "audio_file": str(path)
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}


# ================================
# MODEL STATUS & WARMUP
# ================================
def get_audio_model_status():
    """Get the status of loaded audio models"""
    return {
        "loaded": _models["loaded"],
        "device": str(_device),
        "models": ["Wav2Vec2 Model 1 (Deepfake)", "Wav2Vec2 Model 2 (Fallback)", "WavLM Model 3 (Specialized)"],
        "status": "Ready" if _models["loaded"] else "Not loaded yet (will load on first use)"
    }


def warmup_audio_model():
    """Warmup all audio models for faster first inference"""
    try:
        if _models["loaded"]:
            return {"ok": True, "status": "Audio models already loaded"}
        
        print("[INFO] Warming up audio models...")
        success = load_ensemble_models()
        
        if success:
            return {"ok": True, "status": "Audio models warmed up successfully"}
        else:
            return {"ok": False, "error": f"Warmup failed: {_error}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}