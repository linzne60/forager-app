"""
Exports a trained checkpoint to dual-output ONNX (logits + features for CAM)
and extracts classifier weights for numpy-based CAM in the backend.

Reads model name and image size from configs/train_config.json.
Validates ONNX outputs match PyTorch and backend transform matches training transform.

Usage (from ml/):
    python scripts/export_onnx.py
    python scripts/export_onnx.py --checkpoint checkpoints/best_model.pth
"""

import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
import timm
import torch
import torch.nn as nn
from PIL import Image
from torchvision.transforms import v2

ML_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = ML_DIR / "configs" / "train_config.json"
MODELS_DIR = ML_DIR / "models"
ONNX_PATH = MODELS_DIR / "plant_classifier.onnx"
WEIGHTS_PATH = MODELS_DIR / "classifier_weights.json"


class DualOutputModel(nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        features = self.model.forward_features(x)
        logits = self.model.forward_head(features)
        return logits, features


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_checkpoint(checkpoint_path, config, device):
    checkpoint = torch.load(checkpoint_path, map_location=device)

    model = timm.create_model(
        config["model_name"],
        pretrained=False,
        num_classes=config["num_classes"],
    )
    model.load_state_dict(checkpoint["model_state"])
    model.to(device)
    model.eval()

    print(f"Loaded checkpoint: val_acc={checkpoint['val_acc']:.4f}, epoch={checkpoint['epoch']}")
    return model, checkpoint


def export_onnx(model, config, device):
    img_size = config["img_size"]
    dual_model = DualOutputModel(model).eval()
    dummy = torch.randn(1, 3, img_size, img_size).to(device)

    with torch.no_grad():
        logits_dual, features_dual = dual_model(dummy)
        logits_orig = model(dummy)
        diff = (logits_dual - logits_orig).abs().max().item()
        print(f"Dual wrapper logit diff: {diff:.6f}")

    print(f"Logits shape:   {logits_dual.shape}")
    print(f"Features shape: {features_dual.shape}")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    onnx_program = torch.onnx.export(
        dual_model,
        (dummy,),
        dynamo=True,
        input_names=["image"],
        output_names=["logits", "features"],
    )
    onnx_program.save(str(ONNX_PATH))
    print(f"Exported ONNX to {ONNX_PATH}")

    return dummy, logits_orig


def validate_onnx(dummy, torch_logits):
    session = ort.InferenceSession(str(ONNX_PATH))
    output_names = [o.name for o in session.get_outputs()]
    print(f"ONNX output names: {output_names}")

    input_np = dummy.cpu().numpy()
    ort_logits, ort_features = session.run(["logits", "features"], {"image": input_np})
    print(f"ONNX logits shape:   {ort_logits.shape}")
    print(f"ONNX features shape: {ort_features.shape}")

    torch_np = torch_logits.detach().cpu().numpy()
    np.testing.assert_allclose(torch_np, ort_logits, rtol=1e-2, atol=1e-2)
    print("ONNX logits match PyTorch within tolerance")

    torch_top = torch_np.argmax(axis=1)
    ort_top = ort_logits.argmax(axis=1)
    assert (torch_top == ort_top).all(), "Top predictions differ!"
    print("Top predicted class matches")


def export_weights(model):
    weights = model.classifier.weight.detach().cpu().numpy()
    print(f"Classifier weights shape: {weights.shape}")

    with open(WEIGHTS_PATH, "w") as f:
        json.dump(weights.tolist(), f)

    print(f"Exported weights to {WEIGHTS_PATH}")


def validate_transforms(config):
    img_size = config["img_size"]
    resize_to = img_size + 20

    fixture_path = ML_DIR.parent / "backend" / "tests" / "fixtures" / "sample_plant.jpg"
    if not fixture_path.exists():
        print(f"No test fixture found at {fixture_path}, skipping transform validation")
        return

    pil_img = Image.open(fixture_path).convert("RGB")

    torch_transform = v2.Compose([
        v2.Resize(resize_to),
        v2.CenterCrop(img_size),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    torch_output = torch_transform(pil_img).unsqueeze(0).numpy()

    w, h = pil_img.size
    if w <= h:
        new_w, new_h = resize_to, int(resize_to * h / w)
    else:
        new_w, new_h = int(resize_to * w / h), resize_to

    resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
    left = (new_w - img_size) // 2
    top = (new_h - img_size) // 2
    cropped = resized.crop((left, top, left + img_size, top + img_size))
    arr = np.array(cropped).astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    numpy_output = arr.transpose(2, 0, 1)[np.newaxis]

    max_diff = np.abs(torch_output - numpy_output).max()
    np.testing.assert_allclose(torch_output, numpy_output, rtol=1e-2, atol=1e-2)
    print(f"Transform parity check passed (max diff: {max_diff:.6f})")

    reference_path = ML_DIR.parent / "backend" / "tests" / "fixtures" / "transform_reference.npy"
    reference_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(reference_path), torch_output)
    print(f"Saved transform reference: {torch_output.shape}")


def main():
    parser = argparse.ArgumentParser(description="Export ONNX model and classifier weights")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to checkpoint (default: from config)")
    args = parser.parse_args()

    config = load_config()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Model: {config['model_name']}")
    print(f"Image size: {config['img_size']}")
    print(f"Classes: {config['num_classes']}")

    checkpoint_path = args.checkpoint
    if checkpoint_path is None:
        checkpoint_path = ML_DIR / config["checkpoint_dir"] / "best_model.pth"
    else:
        checkpoint_path = Path(checkpoint_path)

    model, checkpoint = load_checkpoint(checkpoint_path, config, device)

    print("\n--- Export ONNX ---")
    dummy, torch_logits = export_onnx(model, config, device)

    print("\n--- Validate ONNX ---")
    validate_onnx(dummy, torch_logits)

    print("\n--- Export Classifier Weights ---")
    export_weights(model)

    print("\n--- Validate Transforms ---")
    validate_transforms(config)

    print("\nDone. Files ready for backend:")
    print(f"  {ONNX_PATH}")
    print(f"  {WEIGHTS_PATH}")


if __name__ == "__main__":
    main()
