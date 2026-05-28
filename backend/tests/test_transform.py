from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from PIL import Image

from app.config import settings
from app.services.classifier import PlantClassifier

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REFERENCE_PATH = FIXTURE_DIR / "transform_reference.npy"
IMAGE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_plant.jpg"


def test_transform_matches_reference():
    reference = np.load(str(REFERENCE_PATH))
    image = Image.open(IMAGE_PATH).convert("RGB")

    classifier = MagicMock(spec=PlantClassifier)
    classifier.img_size = settings.cv_img_size
    result = PlantClassifier._transform(classifier, image)

    np.testing.assert_allclose(reference, result, rtol=1e-2, atol=1e-2)
