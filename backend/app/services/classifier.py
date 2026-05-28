from __future__ import annotations

import io
import json
import logging
from dataclasses import dataclass

import numpy as np
import onnxruntime as ort
from PIL import Image

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class SpeciesResult:
    species: str
    confidence: float


class PlantClassifier:
    def __init__(self, settings: Settings) -> None:

        with open(settings.cv_class_map_path) as f:
            class_map = json.load(f)

        self.idx_to_class = {int(k): v for k, v in class_map.items()}

        with open(settings.cv_classifier_weights_path) as f:
            weights_list = json.load(f)

        self.classifier_weights = np.array(weights_list, dtype=np.float32)
        self.img_size = settings.cv_img_size

        self.session = ort.InferenceSession(str(settings.cv_model_onnx_path))
    
    def _transform(self, image: Image.Image) -> np.ndarray:
        resize_to = self.img_size + 20
        crop_size = self.img_size

        w, h = image.size
        if w <= h:
            new_w = resize_to
            new_h = int(resize_to * h / w)
        else:
            new_h = resize_to
            new_w = int(resize_to * w / h)

        image = image.resize((new_w, new_h), Image.Resampling.BILINEAR)

        left = (new_w - crop_size) // 2
        top = (new_h - crop_size) // 2
        image = image.crop((left, top, left + crop_size, top + crop_size))

        arr = np.array(image).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        arr = (arr - mean) / std
        arr = arr.transpose(2, 0, 1)

        return arr[np.newaxis]

    def predict(self, image: Image.Image, top_k: int = 5) -> list[SpeciesResult]:

        input_np = self._transform(image)

        logits = self.session.run(["logits"], {"image": input_np})[0]

        exp_logits = np.exp(logits)
        probabilities = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        probabilities = probabilities[0]

        top_indices = np.argsort(probabilities)[::-1][:top_k]

        results = []

        for i in top_indices:
            species = self.idx_to_class[int(i)]
            confidence = float(probabilities[i])
            results.append(SpeciesResult(species=species, confidence=confidence))

        return results

    def explain(self, image: Image.Image) -> bytes:

        input_np = self._transform(image)

        logits, features = self.session.run(["logits", "features"], {"image": input_np})
        pred_class = int(np.argmax(logits[0]))

        weights = self.classifier_weights[pred_class]
        feature_maps = features[0]

        cam = np.zeros(feature_maps.shape[1:], dtype=np.float32)
        for i, w in enumerate(weights):
            cam += w * feature_maps[i]

        cam = np.maximum(cam, 0)
        if cam.max() > 0:
            cam = cam / cam.max()

        cam_resized = np.array(
            Image.fromarray((cam * 255).astype(np.uint8)).resize((self.img_size, self.img_size))
        ).astype(np.float32) / 255.0

        rgb = np.array(image.resize((self.img_size, self.img_size))).astype(np.float32) / 255.0

        heatmap = np.zeros((*cam_resized.shape, 3), dtype=np.float32)
        heatmap[:, :, 0] = cam_resized
        heatmap[:, :, 2] = 1 - cam_resized

        overlay = np.clip(0.5 * rgb + 0.5 * heatmap, 0, 1)
        visualization = (overlay * 255).astype(np.uint8)

        buf = io.BytesIO()
        Image.fromarray(visualization).save(buf, format="JPEG")
        return buf.getvalue()


classifier: PlantClassifier | None = None


def load_classifier(settings: Settings) -> None:
    global classifier
    classifier = PlantClassifier(settings)

    logger.info("PlantClassifier loaded: %d classes", len(classifier.idx_to_class))  


def get_classifier() -> PlantClassifier:
    if classifier is None:
        raise RuntimeError("Classifier not loaded")
    return classifier
