import os
import json
from typing import List, Tuple

import numpy as np
import tensorflow as tf
from PIL import Image
from keras import layers
from keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input

try:
    import torch
    import open_clip
except Exception:
    torch = None
    open_clip = None

try:
    import cv2
except Exception:
    cv2 = None

try:
    from transformers import pipeline
except Exception:
    pipeline = None

IMAGE_SIZE = (224, 224)
REAL_THRESHOLD = 0.5
MODEL_CANDIDATES = [
    "models/final_model.keras",
    "models/deepfake_model (1).keras",
]
CLIP_MODEL_NAME = "ViT-B-32"
CLIP_PRETRAINED = "laion2b_s34b_b79k"
CLIP_PROMPTS = [
    "a natural real camera photograph of a real person",
    "an ai-generated synthetic deepfake image",
]
HF_DEEPFAKE_MODEL_ID = "prithivMLmods/Deep-Fake-Detector-Model"
CALIBRATION_PATH = "models/image_calibration.json"
FAKE_NAME_HINTS = ("ai-generated", "deepfake", "synthetic", "fake")
REAL_OVERRIDE_MIN_HF = 0.68
REAL_OVERRIDE_MIN_CLIP = 0.90
UNCERTAIN_MARGIN = 0.06


def _build_fallback_model():
    # Keep fallback architecture close to typical training stacks for compatibility.
    base = MobileNetV2(weights=None, include_top=False, input_shape=(224, 224, 3))
    x = layers.GlobalAveragePooling2D()(base.output)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    output = layers.Dense(1, activation="sigmoid")(x)
    return tf.keras.Model(inputs=base.input, outputs=output)


def _load_image_model(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    try:
        print(f"Loading image model: {model_path}")
        model = tf.keras.models.load_model(model_path, compile=False)
        print("Image model loaded successfully")
        return model, model_path, "direct"
    except Exception as load_err:
        print(f"Direct model load failed for {model_path}: {load_err}")
        print("Trying fallback MobileNetV2 architecture + partial weights...")

        fallback_model = _build_fallback_model()
        try:
            fallback_model.load_weights(model_path, skip_mismatch=True)
            print(f"Fallback model initialized from: {model_path}")
            return fallback_model, model_path, "fallback"
        except Exception as weights_err:
            raise RuntimeError(
                f"Failed to load model '{model_path}'. "
                f"Direct error: {load_err}. Fallback error: {weights_err}"
            )


def _load_best_available_model() -> Tuple[tf.keras.Model, str, str, List[str]]:
    errors = []
    for candidate in MODEL_CANDIDATES:
        try:
            model, loaded_from, mode = _load_image_model(candidate)
            return model, loaded_from, mode, errors
        except Exception as err:
            errors.append(f"{candidate}: {err}")

    raise RuntimeError("No compatible image model could be loaded. " + " | ".join(errors))


model = None
model_source = ""
model_load_mode = ""
model_load_errors = []
model_init_error = None
model_is_degenerate = False

clip_model = None
clip_preprocess = None
clip_tokenizer = None
clip_device = "cpu"
clip_init_error = None
fallback_clip_weight = 0.35
fallback_heuristic_weight = 0.65
fallback_hf_weight = 0.0
fallback_threshold = REAL_THRESHOLD
fallback_calibration_samples = 0
fallback_calibration_score = None
fallback_calibration_source = "runtime"

hf_classifier = None
hf_init_error = None

try:
    model, model_source, model_load_mode, model_load_errors = _load_best_available_model()
except Exception as err:
    model_init_error = str(err)
    print(f"Image model initialization failed: {model_init_error}")


def _list_local_sample_images(max_samples: int = 8) -> List[str]:
    search_dir = "uploads"
    if not os.path.isdir(search_dir):
        return []

    valid_ext = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    samples = []
    for name in sorted(os.listdir(search_dir)):
        _, ext = os.path.splitext(name.lower())
        if ext in valid_ext:
            samples.append(os.path.join(search_dir, name))
        if len(samples) >= max_samples:
            break
    return samples


def _expected_label_from_filename(path: str) -> str:
    name = os.path.basename(path).lower()
    if any(k in name for k in FAKE_NAME_HINTS):
        return "Fake"
    return "Real"


def preprocess(img_path: str) -> np.ndarray:
    with Image.open(img_path) as image:
        image = image.convert("RGB")
        image = image.resize(IMAGE_SIZE, Image.Resampling.LANCZOS)
        img = np.array(image, dtype=np.float32)

    img = preprocess_input(img)
    return np.expand_dims(img, axis=0)


def _predict_with_tta(img_batch: np.ndarray) -> float:
    # Simple TTA improves prediction stability on mirrored/compressed uploads.
    pred_original = float(model.predict(img_batch, verbose=0)[0][0])
    pred_flipped = float(model.predict(img_batch[:, :, ::-1, :], verbose=0)[0][0])
    score = (pred_original + pred_flipped) / 2.0
    return float(np.clip(score, 0.0, 1.0))


def _detect_model_degeneracy() -> bool:
    if model is None:
        return True

    sample_paths = _list_local_sample_images(max_samples=8)
    if len(sample_paths) < 3:
        return False

    scores = []
    for path in sample_paths:
        try:
            s = _predict_with_tta(preprocess(path))
            scores.append(float(s))
        except Exception:
            continue

    if len(scores) < 3:
        return False

    std_val = float(np.std(scores))
    near_half = all(abs(x - 0.5) < 0.02 for x in scores)
    return std_val < 0.002 and near_half


def _init_clip_detector() -> bool:
    global clip_model, clip_preprocess, clip_tokenizer, clip_device, clip_init_error

    if clip_model is not None:
        return True

    if open_clip is None or torch is None:
        clip_init_error = "open_clip_torch or torch is not installed"
        return False

    try:
        clip_device = "cuda" if torch.cuda.is_available() else "cpu"
        clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
            CLIP_MODEL_NAME,
            pretrained=CLIP_PRETRAINED,
            device=clip_device,
        )
        clip_model.eval()
        clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
        return True
    except Exception as err:
        clip_init_error = str(err)
        return False


def _predict_with_clip(img_path: str) -> float:
    if not _init_clip_detector():
        raise RuntimeError(f"CLIP detector init failed: {clip_init_error}")

    with Image.open(img_path) as image:
        image = image.convert("RGB")
        image_tensor = clip_preprocess(image).unsqueeze(0).to(clip_device)

    text_tokens = clip_tokenizer(CLIP_PROMPTS).to(clip_device)

    with torch.no_grad():
        image_features = clip_model.encode_image(image_tensor)
        text_features = clip_model.encode_text(text_tokens)

        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        logits = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        real_probability = float(logits[0][0].item())

    return float(np.clip(real_probability, 0.0, 1.0))


def _init_hf_detector() -> bool:
    global hf_classifier, hf_init_error

    if hf_classifier is not None:
        return True

    if pipeline is None:
        hf_init_error = "transformers is not installed"
        return False

    try:
        hf_classifier = pipeline("image-classification", model=HF_DEEPFAKE_MODEL_ID)
        return True
    except Exception as err:
        hf_init_error = str(err)
        return False


def _predict_with_hf(img_path: str) -> float:
    if not _init_hf_detector():
        raise RuntimeError(f"HF detector init failed: {hf_init_error}")

    with Image.open(img_path) as image:
        result = hf_classifier(image.convert("RGB"))

    if not result:
        return 0.5

    real_prob = None
    fake_prob = None
    for item in result:
        label = str(item.get("label", "")).lower()
        score = float(item.get("score", 0.0))
        if "real" in label:
            real_prob = score
        if "fake" in label:
            fake_prob = score

    if real_prob is not None:
        return float(np.clip(real_prob, 0.0, 1.0))
    if fake_prob is not None:
        return float(np.clip(1.0 - fake_prob, 0.0, 1.0))

    top = result[0]
    label = str(top.get("label", "")).lower()
    score = float(top.get("score", 0.5))
    if "fake" in label:
        return float(np.clip(1.0 - score, 0.0, 1.0))
    if "real" in label:
        return float(np.clip(score, 0.0, 1.0))
    return 0.5


def _load_saved_calibration(path: str) -> bool:
    global fallback_hf_weight
    global fallback_clip_weight
    global fallback_heuristic_weight
    global fallback_threshold
    global fallback_calibration_score
    global fallback_calibration_source

    if not os.path.exists(path):
        return False

    try:
        with open(path, "r", encoding="utf-8") as fp:
            cfg = json.load(fp)

        hf_w = float(cfg.get("hf_weight", fallback_hf_weight))
        clip_w = float(cfg.get("clip_weight", fallback_clip_weight))
        heur_w = float(cfg.get("heuristic_weight", fallback_heuristic_weight))
        threshold = float(cfg.get("threshold", fallback_threshold))

        total = hf_w + clip_w + heur_w
        if total <= 0:
            return False

        hf_w /= total
        clip_w /= total
        heur_w /= total

        fallback_hf_weight = float(np.clip(hf_w, 0.0, 1.0))
        fallback_clip_weight = float(np.clip(clip_w, 0.0, 1.0))
        fallback_heuristic_weight = float(np.clip(heur_w, 0.0, 1.0))
        fallback_threshold = float(np.clip(threshold, 0.05, 0.95))

        metrics = cfg.get("metrics")
        if isinstance(metrics, dict):
            fallback_calibration_score = metrics
        else:
            fallback_calibration_score = None

        fallback_calibration_source = "file"
        return True
    except Exception as err:
        print(f"Failed to load calibration file '{path}': {err}")
        return False


def _heuristic_real_score(img_path: str) -> float:
    if cv2 is None:
        raise RuntimeError("opencv-python is not installed")

    try:
        with Image.open(img_path) as pil_image:
            rgb = np.array(pil_image.convert("RGB"), dtype=np.uint8)
        image = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    except Exception as err:
        raise RuntimeError(f"Failed to read image: {img_path}. {err}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    noise_std = float(np.std(gray.astype(np.float32) - blur.astype(np.float32)))

    h, w = gray.shape
    if w > 16:
        left = gray[:, 7::8].astype(np.float32)
        right = gray[:, 8::8].astype(np.float32)
        cols = min(left.shape[1], right.shape[1])
        if cols > 0:
            boundary_diff = np.abs(left[:, :cols] - right[:, :cols])
            blockiness = float(np.mean(boundary_diff))
        else:
            blockiness = 0.0
    else:
        blockiness = 0.0

    saturation = float(np.mean(hsv[:, :, 1]))

    lap_n = np.clip(lap_var / 5000.0, 0.0, 1.0)
    noise_n = np.clip(noise_std / 30.0, 0.0, 1.0)
    block_n = np.clip(blockiness / 20.0, 0.0, 1.0)
    sat_n = np.clip(saturation / 255.0, 0.0, 1.0)

    linear = (0.35 * lap_n) + (0.35 * noise_n) + (0.20 * block_n) - (0.15 * sat_n)
    score = 1.0 / (1.0 + np.exp(-(linear - 0.18) / 0.08))
    return float(np.clip(score, 0.0, 1.0))


def _image_quality_metrics(img_path: str) -> dict:
    with Image.open(img_path) as image:
        rgb = np.array(image.convert("RGB"), dtype=np.uint8)

    h, w = rgb.shape[:2]
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY) if cv2 is not None else np.mean(rgb, axis=2).astype(np.uint8)
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var()) if cv2 is not None else 0.0

    warnings = []
    if min(h, w) < 224:
        warnings.append("low_resolution")
    if lap_var > 0 and lap_var < 80:
        warnings.append("blurry_image")

    return {
        "width": int(w),
        "height": int(h),
        "laplacian_var": round(lap_var, 2),
        "warnings": warnings,
    }


def _predict_fallback_score_with_tta(img_path: str) -> tuple[float, float, float, float]:
    with Image.open(img_path) as image:
        image = image.convert("RGB")
        mirrored = image.transpose(Image.FLIP_LEFT_RIGHT)

        tmp_original = os.path.join("uploads", "__tmp_original_eval.jpg")
        tmp_mirror = os.path.join("uploads", "__tmp_mirror_eval.jpg")
        image.save(tmp_original)
        mirrored.save(tmp_mirror)

    try:
        hf_o = _predict_with_hf(tmp_original)
        hf_m = _predict_with_hf(tmp_mirror)
        clip_o = _predict_with_clip(tmp_original)
        clip_m = _predict_with_clip(tmp_mirror)
        heur_o = _heuristic_real_score(tmp_original)
        heur_m = _heuristic_real_score(tmp_mirror)
    finally:
        for p in (tmp_original, tmp_mirror):
            if os.path.exists(p):
                os.remove(p)

    hf_score = (hf_o + hf_m) / 2.0
    clip_score = (clip_o + clip_m) / 2.0
    heuristic_score = (heur_o + heur_m) / 2.0

    score = (
        (fallback_hf_weight * hf_score)
        + (fallback_clip_weight * clip_score)
        + (fallback_heuristic_weight * heuristic_score)
    )
    return float(score), float(hf_score), float(clip_score), float(heuristic_score)


def _calibrate_fallback_detector() -> None:
    global fallback_clip_weight
    global fallback_heuristic_weight
    global fallback_hf_weight
    global fallback_threshold
    global fallback_calibration_samples
    global fallback_calibration_score
    global fallback_calibration_source

    sample_paths = _list_local_sample_images(max_samples=60)
    rows = []

    for path in sample_paths:
        try:
            hf_score = _predict_with_hf(path)
            clip_score = _predict_with_clip(path)
            heuristic_score = _heuristic_real_score(path)
            label = _expected_label_from_filename(path)
            rows.append((hf_score, clip_score, heuristic_score, label))
        except Exception:
            continue

    fallback_calibration_samples = len(rows)
    if len(rows) < 6:
        return

    best = None
    for hf_w in [i / 20.0 for i in range(0, 21)]:
        for clip_w in [j / 20.0 for j in range(0, 21)]:
            heur_w = 1.0 - hf_w - clip_w
            if heur_w < 0.0:
                continue
            for t_step in range(30, 71):
                threshold = t_step / 100.0
                correct = 0
                real_total = 0
                fake_total = 0
                real_correct = 0
                fake_correct = 0

                for hf_score, clip_score, heuristic_score, label in rows:
                    score = (hf_w * hf_score) + (clip_w * clip_score) + (heur_w * heuristic_score)
                    pred = "Real" if score > threshold else "Fake"
                    if pred == label:
                        correct += 1
                    if label == "Real":
                        real_total += 1
                        if pred == "Real":
                            real_correct += 1
                    else:
                        fake_total += 1
                        if pred == "Fake":
                            fake_correct += 1

                accuracy = correct / len(rows)
                real_recall = (real_correct / real_total) if real_total else 0.0
                fake_recall = (fake_correct / fake_total) if fake_total else 0.0
                balanced = (real_recall + fake_recall) / 2.0
                objective = (0.7 * balanced) + (0.3 * accuracy)

                item = (objective, balanced, accuracy, hf_w, clip_w, heur_w, threshold)
                if best is None or item > best:
                    best = item

    if best is None:
        return

    _, balanced, accuracy, hf_w, clip_w, heur_w, threshold = best
    fallback_hf_weight = float(hf_w)
    fallback_clip_weight = float(clip_w)
    fallback_heuristic_weight = float(heur_w)
    fallback_threshold = float(threshold)
    fallback_calibration_score = {
        "balanced_accuracy": round(float(balanced), 4),
        "accuracy": round(float(accuracy), 4),
    }
    fallback_calibration_source = "runtime"


def _confidence_from_threshold(score: float, threshold: float) -> float:
    if score >= threshold:
        denom = 1.0 - threshold
        conf = (score - threshold) / denom if denom > 0 else 1.0
    else:
        denom = threshold
        conf = (threshold - score) / denom if denom > 0 else 1.0
    return float(np.clip(conf, 0.0, 1.0))


if model is not None:
    model_is_degenerate = _detect_model_degeneracy()
    if model_is_degenerate:
        print("Model scores look degenerate; CLIP fallback will be used for reliability")
        try:
            if _load_saved_calibration(CALIBRATION_PATH):
                print(
                    "Loaded saved calibration "
                    f"(hf_w={fallback_hf_weight:.2f}, "
                    f"clip_w={fallback_clip_weight:.2f}, "
                    f"heur_w={fallback_heuristic_weight:.2f}, "
                    f"threshold={fallback_threshold:.2f})"
                )
            else:
                _calibrate_fallback_detector()
            print(
                "Fallback calibrated "
                f"(samples={fallback_calibration_samples}, "
                f"hf_w={fallback_hf_weight:.2f}, "
                f"clip_w={fallback_clip_weight:.2f}, "
                f"heur_w={fallback_heuristic_weight:.2f}, "
                f"threshold={fallback_threshold:.2f})"
            )
        except Exception as calibration_err:
            print(f"Fallback calibration failed: {calibration_err}")


def detect_image(img_path: str):
    try:
        if not os.path.exists(img_path):
            return {"error": f"Image file not found: {img_path}"}

        detector = "keras_model"
        hf_score = None
        clip_score = None
        heuristic_score = None
        quality = _image_quality_metrics(img_path)
        if model is None:
            score, hf_score, clip_score, heuristic_score = _predict_fallback_score_with_tta(img_path)
            detector = "clip_heuristic_fallback"
            decision_threshold = fallback_threshold
        elif model_is_degenerate:
            score, hf_score, clip_score, heuristic_score = _predict_fallback_score_with_tta(img_path)
            detector = "clip_heuristic_fallback"
            decision_threshold = fallback_threshold
        else:
            img = preprocess(img_path)
            score = _predict_with_tta(img)
            decision_threshold = REAL_THRESHOLD

        is_real = score > decision_threshold
        # Reduce false-fake outcomes when two strong independent detectors agree on real.
        if (
            not is_real
            and hf_score is not None
            and clip_score is not None
            and hf_score >= REAL_OVERRIDE_MIN_HF
            and clip_score >= REAL_OVERRIDE_MIN_CLIP
        ):
            is_real = True
            detector = f"{detector}_real_override"

        band_low = decision_threshold - UNCERTAIN_MARGIN
        band_high = decision_threshold + UNCERTAIN_MARGIN
        prediction = "Real" if is_real else "Fake"
        if band_low <= score <= band_high:
            prediction = "Uncertain"
            detector = f"{detector}_uncertain_band"

        confidence = _confidence_from_threshold(score, decision_threshold)

        return {
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "score": round(score, 4),
            "threshold": round(float(decision_threshold), 4),
            "uncertain_band": {
                "low": round(float(band_low), 4),
                "high": round(float(band_high), 4),
            },
            "model_source": model_source,
            "model_load_mode": model_load_mode,
            "detector": detector,
            "model_is_degenerate": model_is_degenerate,
            "quality": quality,
            "fallback_weights": {
                "hf": round(float(fallback_hf_weight), 4),
                "clip": round(float(fallback_clip_weight), 4),
                "heuristic": round(float(fallback_heuristic_weight), 4),
            },
            "fallback_calibration": {
                "samples": fallback_calibration_samples,
                "metrics": fallback_calibration_score,
                "source": fallback_calibration_source,
            },
            "signals": {
                "hf": round(float(hf_score), 4) if hf_score is not None else None,
                "clip": round(float(clip_score), 4) if clip_score is not None else None,
                "heuristic": round(float(heuristic_score), 4) if heuristic_score is not None else None,
            },
        }

    except Exception as err:
        return {"error": str(err)}