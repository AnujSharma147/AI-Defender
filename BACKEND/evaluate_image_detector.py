import argparse
import os
from collections import Counter
from typing import List, Tuple

from detect_image import detect_image

VALID_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def collect_images(folder: str) -> List[str]:
    if not os.path.isdir(folder):
        return []

    items: List[str] = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(name.lower())
        if ext in VALID_EXT:
            items.append(path)
    return items


def label_from_name(path: str) -> str:
    name = os.path.basename(path).lower()
    if any(k in name for k in ("ai-generated", "deepfake", "synthetic", "fake")):
        return "Fake"
    return "Real"


def normalize_prediction(pred: str) -> str:
    if not pred:
        return "Error"
    value = pred.strip().lower()
    if value == "real":
        return "Real"
    if value == "fake":
        return "Fake"
    if value == "uncertain":
        return "Uncertain"
    return "Error"


def build_dataset(real_dir: str, fake_dir: str, hint_dir: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []

    for path in collect_images(real_dir):
        rows.append((path, "Real"))
    for path in collect_images(fake_dir):
        rows.append((path, "Fake"))

    if hint_dir:
        for path in collect_images(hint_dir):
            rows.append((path, label_from_name(path)))

    seen = set()
    unique_rows: List[Tuple[str, str]] = []
    for path, label in rows:
        key = os.path.abspath(path)
        if key in seen:
            continue
        seen.add(key)
        unique_rows.append((path, label))

    return unique_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate image detector and print report summary")
    parser.add_argument("--real-dir", default="", help="Folder containing real images")
    parser.add_argument("--fake-dir", default="", help="Folder containing fake images")
    parser.add_argument("--hint-dir", default="uploads", help="Folder using filename hints when labeled folders not provided")
    parser.add_argument("--show-all", action="store_true", help="Print all rows instead of only error/uncertain rows")
    args = parser.parse_args()

    rows = build_dataset(args.real_dir, args.fake_dir, args.hint_dir)
    if not rows:
        print("No images found. Provide --real-dir/--fake-dir or --hint-dir.")
        return 1

    confusion = Counter()
    pred_counts = Counter()
    details = []

    for path, expected in rows:
        result = detect_image(path)
        if isinstance(result, dict):
            prediction = normalize_prediction(str(result.get("prediction", "Error")))
            score = result.get("score")
            confidence = result.get("confidence")
            detector = result.get("detector")
        else:
            prediction = "Error"
            score = None
            confidence = None
            detector = None

        confusion[(expected, prediction)] += 1
        pred_counts[prediction] += 1
        details.append((path, expected, prediction, score, confidence, detector))

    total = len(details)
    correct = sum(1 for _, expected, prediction, *_ in details if expected == prediction)
    uncertain = sum(1 for _, _, prediction, *_ in details if prediction == "Uncertain")
    errors = sum(1 for _, _, prediction, *_ in details if prediction == "Error")
    accuracy = (correct / total) * 100.0 if total else 0.0

    print(f"TOTAL: {total}")
    print(f"CORRECT: {correct}")
    print(f"ACCURACY: {accuracy:.2f}%")
    print(f"UNCERTAIN: {uncertain}")
    print(f"ERROR: {errors}")
    print(f"PREDICTIONS: {dict(pred_counts)}")
    print(f"CONFUSION: {dict(confusion)}")

    print("\nROWS:")
    for path, expected, prediction, score, confidence, detector in details:
        if not args.show_all and prediction not in ("Uncertain", "Error") and expected == prediction:
            continue
        print(
            f"- {os.path.basename(path)} | expected={expected} | pred={prediction} "
            f"| score={score} | confidence={confidence} | detector={detector}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
