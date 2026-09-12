"""
AI-based image classification using HuggingFace zero-shot model.
Falls back to rule-based if model can't load.
"""

import streamlit as st
from PIL import Image

# Issue categories
ISSUE_LABELS = [
    "a pothole on the road",
    "a broken streetlight",
    "a garbage dump on the street",
    "a water leak or pipe burst",
    "a broken public property or bench"
]

LABEL_TO_TYPE = {
    "a pothole on the road": "Pothole",
    "a broken streetlight": "Broken Streetlight",
    "a garbage dump on the street": "Garbage Dump",
    "a water leak or pipe burst": "Water Leak",
    "a broken public property or bench": "Other"
}


@st.cache_resource(show_spinner="🤖 Loading AI model (first time only)...")
def load_model():
    """Load zero-shot image classification pipeline."""
    try:
        from transformers import pipeline
        classifier = pipeline(
            "zero-shot-image-classification",
            model="openai/clip-vit-base-patch32"
        )
        return classifier
    except Exception as e:
        return None


def classify_image(image: Image.Image):
    """
    Returns (issue_type, confidence, all_scores).
    Falls back to heuristics if model unavailable.
    """
    classifier = load_model()

    if classifier is not None:
        try:
            results = classifier(image, candidate_labels=ISSUE_LABELS)
            top = results[0]
            issue_type = LABEL_TO_TYPE[top["label"]]
            confidence = float(top["score"])
            all_scores = {LABEL_TO_TYPE[r["label"]]: float(r["score"]) for r in results}
            return issue_type, confidence, all_scores
        except Exception as e:
            pass

    # Fallback: rule-based on image brightness / colors
    return _fallback_classify(image)


def _fallback_classify(image: Image.Image):
    """Simple color/brightness heuristic."""
    img = image.convert("RGB").resize((100, 100))
    pixels = list(img.getdata())
    avg_r = sum(p[0] for p in pixels) / len(pixels)
    avg_g = sum(p[1] for p in pixels) / len(pixels)
    avg_b = sum(p[2] for p in pixels) / len(pixels)
    brightness = (avg_r + avg_g + avg_b) / 3

    if brightness < 60:
        issue_type = "Broken Streetlight"
    elif avg_b > avg_r + 30 and avg_b > avg_g + 20:
        issue_type = "Water Leak"
    elif avg_r > avg_g + 20 and avg_r > avg_b + 20:
        issue_type = "Garbage Dump"
    elif brightness < 110:
        issue_type = "Pothole"
    else:
        issue_type = "Other"

    return issue_type, 0.55, {issue_type: 0.55}


def estimate_severity(image: Image.Image, issue_type: str):
    """
    Estimate severity based on image size + type.
    (Dummy logic — real model would analyze damage extent)
    """
    # In a real app, run a segmentation model to measure damage area
    # Here we use image dimensions as a proxy
    w, h = image.size
    area_score = (w * h) / (800 * 600)

    severity_map = {
        "Pothole": "High" if area_score > 0.8 else "Medium",
        "Broken Streetlight": "Medium",
        "Garbage Dump": "High" if area_score > 0.9 else "Medium",
        "Water Leak": "High",
        "Other": "Low"
    }
    return severity_map.get(issue_type, "Medium")
