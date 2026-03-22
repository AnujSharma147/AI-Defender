import argparse
import json
import os
from typing import List, Tuple

from detect_image import _predict_with_hf, _predict_with_clip, _heuristic_real_score

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
DEFAULT_OUT = "models/image_calibration.json"


def _collect_images(folder: str) -> List[str]:
    items: List[str] = []
    if not os.path.isdir(folder):
        return items

    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(name.lower())
        if ext in VALID_EXT:
            items.append(path)
    return items


def _label_from_name(path: str) -> str:
    name = os.path.basename(path).lower()
    if any(k in name for k in ("ai-generated", "deepfake", "synthetic", "fake")):
        return "Fake"
    return "Real"


def _build_rows(real_paths: List[str], fake_paths: List[str]) -> List[Tuple[float, float, float, str]]:
    rows: List[Tuple[float, float, float, str]] = []

    labeled = [(p, "Real") for p in real_paths] + [(p, "Fake") for p in fake_paths]
    for path, label in labeled:
        try:
            hf_score = _predict_with_hf(path)
            clip_score = _predict_with_clip(path)
            heuristic_score = _heuristic_real_score(path)
            rows.append((hf_score, clip_score, heuristic_score, label))
        except Exception as err:
            print(f"Skip {path}: {err}")
    return rows


def _find_best(rows: List[Tuple[float, float, float, str]]):
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

    return best


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate image detector ensemble weights.")
    parser.add_argument("--real-dir", default="calibration_data/real", help="Folder with real images")
    parser.add_argument("--fake-dir", default="calibration_data/fake", help="Folder with fake images")
    parser.add_argument("--hint-dir", default="", help="Optional folder using filename hints (fake/deepfake/ai-generated)")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output calibration JSON path")
    args = parser.parse_args()

    real_paths = _collect_images(args.real_dir)
    fake_paths = _collect_images(args.fake_dir)

    if args.hint_dir:
        hinted = _collect_images(args.hint_dir)
        for path in hinted:
            label = _label_from_name(path)
            if label == "Fake":
                fake_paths.append(path)
            else:
                real_paths.append(path)

    print(f"Real images: {len(real_paths)}")
    print(f"Fake images: {len(fake_paths)}")

    if not real_paths or not fake_paths:
        print("Need both real and fake images for calibration.")
        return 1

    rows = _build_rows(real_paths, fake_paths)
    if len(rows) < 10:
        print("Too few valid rows for calibration. Need at least 10.")
        return 1

    best = _find_best(rows)
    if best is None:
        print("Calibration search failed.")
        return 1

    objective, balanced, accuracy, hf_w, clip_w, heur_w, threshold = best
    payload = {
        "hf_weight": round(float(hf_w), 6),
        "clip_weight": round(float(clip_w), 6),
        "heuristic_weight": round(float(heur_w), 6),
        "threshold": round(float(threshold), 6),
        "metrics": {
            "objective": round(float(objective), 6),
            "balanced_accuracy": round(float(balanced), 6),
            "accuracy": round(float(accuracy), 6),
            "rows": len(rows),
            "real_count": len(real_paths),
            "fake_count": len(fake_paths),
        },
    }

    out_dir = os.path.dirname(args.out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(args.out, "w", encoding="utf-8") as fp:
        json.dump(payload, fp, indent=2)

    print(f"Saved calibration: {args.out}")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
