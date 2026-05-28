import json
from datetime import datetime
from pathlib import Path

import timm
import timm.loss
import torch
from timm.data.mixup import Mixup
from torch import amp
from torch.optim.swa_utils import AveragedModel, SWALR, update_bn
from torch.utils.data import DataLoader
from torchvision.transforms import v2
from tqdm import tqdm

from training.dataset import PlantDataset


def load_config(config_path):
    config = Path(config_path)

    with open(config, 'r') as f:
        train_config = json.load(f)

    return train_config


def build_transforms(config):

    img_size = config['img_size']

    train_transform = v2.Compose([
        v2.RandomResizedCrop(img_size, scale=(0.7, 1.0)),
        v2.RandomHorizontalFlip(),
        v2.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        v2.RandomRotation(15),
        v2.RandAugment(num_ops=2, magnitude=12),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    val_transform = v2.Compose([
        v2.Resize(img_size + 20),
        v2.CenterCrop(img_size),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    return train_transform, val_transform


def build_dataloaders(config, class_map):

    ML_DIR = Path(__file__).parent.parent
    DATA_DIR = ML_DIR / config['data_dir']
    ROOT_DIR = ML_DIR.parent

    train_csv_path = DATA_DIR / "train.csv"
    val_csv_path = DATA_DIR / "val.csv"

    train_transform, val_transform = build_transforms(config)

    train_data = PlantDataset(train_csv_path, class_map, train_transform, root_dir=ROOT_DIR)
    val_data = PlantDataset(val_csv_path, class_map, val_transform, root_dir=ROOT_DIR)

    train_loader = DataLoader(train_data, batch_size=config['batch_size'], num_workers=config["num_workers"], shuffle=True, drop_last=True)
    val_loader = DataLoader(val_data, batch_size=config['batch_size'], num_workers=config["num_workers"], shuffle=False)

    return train_loader, val_loader


def build_model(config):

    model = timm.create_model(
        config['model_name'],
        pretrained=True,
        num_classes=config['num_classes'],
        drop_rate=config.get('drop_rate', 0.0),
        drop_path_rate=config.get('drop_path_rate', 0.0),
    )
    return model


def build_mixup(config):

    mixup_alpha = config.get('mixup_alpha', 0.0)
    cutmix_alpha = config.get('cutmix_alpha', 0.0)

    if mixup_alpha > 0 or cutmix_alpha > 0:
        mixup_fn = Mixup(
            mixup_alpha=mixup_alpha,
            cutmix_alpha=cutmix_alpha,
            num_classes=config['num_classes'],
        )
        return mixup_fn

    return None


def train_one_epoch(model, loader, optimizer, criterion, scaler, device, config, mixup_fn=None):
    model.train()
    optimizer.zero_grad()

    accum_steps = config.get('accum_steps', 1)
    total_loss, correct, total = 0, 0, 0

    for i, (images, labels) in enumerate(loader):
        images, labels = images.to(device), labels.to(device)

        # track accuracy before mixup transforms the labels
        with torch.no_grad():
            original_labels = labels.clone()

        if mixup_fn is not None:
            images, labels = mixup_fn(images, labels)

        with amp.autocast('cuda'):
            outputs = model(images)
            loss = criterion(outputs, labels) / accum_steps

        scaler.scale(loss).backward()

        if (i + 1) % accum_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

        total_loss += loss.item() * accum_steps
        correct += (outputs.argmax(dim=1) == original_labels).sum().item()
        total += original_labels.size(0)

    return total_loss / len(loader), correct / total


def evaluate(model, loader, criterion, device):

    model.eval()

    total_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            with amp.autocast('cuda'):
                outputs = model(images)
                loss = criterion(outputs, labels)

            total += labels.size(0)

            total_loss += loss.item()
            correct += (outputs.argmax(dim=1) == labels).sum().item()

    return total_loss / len(loader), correct / total


def analyze_errors(model, loader, class_map, device):
    model.eval()
    all_preds = []
    all_labels = []

    id_to_name = {int(k): v for k, v in class_map.items()}

    with torch.no_grad():
        for images, labels in tqdm(loader, desc="Analyzing"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1)

            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    class_stats = {}
    for i in range(len(all_labels)):
        label = int(all_labels[i])
        pred = int(all_preds[i])

        if label not in class_stats:
            class_stats[label] = {'correct': 0, 'total': 0}

        class_stats[label]['total'] += 1
        if label == pred:
            class_stats[label]['correct'] += 1

    performance = []
    for label, stats in class_stats.items():
        acc = stats['correct'] / stats['total']
        name = id_to_name.get(label, f"Unknown_ID_{label}")
        performance.append((name, acc, stats['total']))

    performance.sort(key=lambda x: x[1])

    print("\n--- Top 10 Most Confused Species ---")
    for name, acc, total in performance[:10]:
        print(f"{name:25} | Accuracy: {acc:.2%} (from {total} samples)")


def main():

    ML_DIR = Path(__file__).parent.parent
    config = load_config(ML_DIR / "configs" / "train_config.json")

    with open(ML_DIR / "data" / "splits" / "class_map.json") as f:
        class_map = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(config).to(device)

    print(f"Device: {device}")
    print(f"Model: {config['model_name']}")
    print(f"Drop rate: {config.get('drop_rate', 0.0)} | Drop path rate: {config.get('drop_path_rate', 0.0)}")

    train_loader, val_loader = build_dataloaders(config, class_map)
    print(f"Train batches per epoch: {len(train_loader)}")
    print(f"Effective batch size: {config['batch_size'] * config.get('accum_steps', 1)}")

    mixup_fn = build_mixup(config)
    if mixup_fn:
        print(f"Mixup alpha: {config.get('mixup_alpha')} | CutMix alpha: {config.get('cutmix_alpha')}")
        mixup_criterion = timm.loss.SoftTargetCrossEntropy()
    else:
        mixup_criterion = torch.nn.CrossEntropyLoss(label_smoothing=config.get('label_smoothing', 0.0))

    clean_criterion = torch.nn.CrossEntropyLoss(label_smoothing=config.get('label_smoothing', 0.0))
    val_criterion = torch.nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=config['phase_a_lr'], weight_decay=config['weight_decay'])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config['phase_b_epochs'])
    scaler = torch.amp.GradScaler('cuda')

    # Setup paths and log
    checkpoint_path = ML_DIR / config['checkpoint_dir'] / "best_model.pth"
    (ML_DIR / config['checkpoint_dir']).mkdir(exist_ok=True)
    log_path = ML_DIR / config['checkpoint_dir'] / "training_log.txt"

    # --- RESUME LOGIC ---
    start_phase = 'A'
    start_epoch = 0
    best_val_acc = 0.0

    if checkpoint_path.exists():
        print(f"Found checkpoint at {checkpoint_path}. Resuming...")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state'])
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        if 'scheduler_state' in checkpoint:
            scheduler.load_state_dict(checkpoint['scheduler_state'])
        start_phase = checkpoint.get('phase', 'A')
        start_epoch = checkpoint['epoch'] + 1
        best_val_acc = checkpoint['val_acc']
        print(f"Resuming from Phase {start_phase}, Epoch {start_epoch} (Best Val Acc: {best_val_acc:.4f})")

    # --- Phase A: Head Only ---
    if start_phase == 'A':
        print("\n--- Phase A: Head Only ---")

        for param in model.parameters():
            param.requires_grad = False
        for param in model.classifier.parameters():
            param.requires_grad = True

        with open(log_path, "a" if start_epoch > 0 else "w") as log:
            if start_epoch == 0:
                log.write("epoch,phase,train_loss,train_acc,val_loss,val_acc,saved\n")

            for epoch in range(start_epoch, config['phase_a_epochs']):
                train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, mixup_criterion, scaler, device, config, mixup_fn)
                val_loss, val_acc = evaluate(model, val_loader, val_criterion, device)

                saved = val_acc > best_val_acc
                if saved:
                    best_val_acc = val_acc
                    torch.save({
                        'epoch': epoch,
                        'phase': 'A',
                        'model_state': model.state_dict(),
                        'optimizer_state': optimizer.state_dict(),
                        'scheduler_state': scheduler.state_dict(),
                        'val_acc': val_acc,
                        'num_classes': config['num_classes'],
                        'class_map': class_map,
                    }, checkpoint_path)

                log.write(f"{epoch},A,{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},{saved}\n")
                log.flush()

                now = datetime.now().strftime("%H:%M:%S")
                print(f"[A] Epoch {epoch} | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}{' ✓ saved' if saved else ''} | {now}")

        start_epoch = 0

    # --- Phase B: Full Fine-tune ---
    if start_phase in ('A', 'B'):
        for param in model.parameters():
            param.requires_grad = True

        if start_phase == 'A' or (start_phase == 'B' and start_epoch == 0):
            for group in optimizer.param_groups:
                group['lr'] = config['phase_b_lr']

        print("\n--- Phase B: Full Fine-tune ---")

        b_start = start_epoch if start_phase == 'B' else 0
        patience = config.get('patience', 8)
        no_improve = 0

        with open(log_path, "a") as log:
            for epoch in range(b_start, config['phase_b_epochs']):
                train_loss, train_acc = train_one_epoch(model, train_loader, optimizer, mixup_criterion, scaler, device, config, mixup_fn)
                val_loss, val_acc = evaluate(model, val_loader, val_criterion, device)

                scheduler.step()

                saved = val_acc > best_val_acc
                if saved:
                    best_val_acc = val_acc
                    no_improve = 0
                    torch.save({
                        'epoch': epoch,
                        'phase': 'B',
                        'model_state': model.state_dict(),
                        'optimizer_state': optimizer.state_dict(),
                        'scheduler_state': scheduler.state_dict(),
                        'val_acc': val_acc,
                        'num_classes': config['num_classes'],
                        'class_map': class_map,
                    }, checkpoint_path)
                else:
                    no_improve += 1
                    if no_improve >= patience:
                        print(f"Early stopping — no improvement for {patience} epochs")
                        break

                log.write(f"{epoch},B,{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},{saved}\n")
                log.flush()

                now = datetime.now().strftime("%H:%M:%S")
                patience_str = f"patience {no_improve}/{patience}" if not saved else "✓ saved"
                print(f"[B] Epoch {epoch} | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | {patience_str} | {now}")

        print(f"\nPhase B complete. Best val accuracy: {best_val_acc:.4f}")

    # --- Phase C: Refinement (no Mixup/CutMix, SWA) ---
    if start_phase in ('A', 'B', 'C'):
        phase_c_epochs = config.get('phase_c_epochs', 10)
        phase_c_lr = config.get('phase_c_lr', 1e-6)

        print(f"\n--- Phase C: Refinement (SWA, no augmentation blending) ---")
        print(f"Epochs: {phase_c_epochs} | LR: {phase_c_lr}")

        # Load best checkpoint from Phase B as starting point
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint['model_state'])
        print(f"Loaded best checkpoint: Phase {checkpoint['phase']}, Epoch {checkpoint['epoch']}, Val Acc: {checkpoint['val_acc']:.4f}")

        # Fresh optimizer with very low static LR
        phase_c_optimizer = torch.optim.AdamW(model.parameters(), lr=phase_c_lr, weight_decay=config['weight_decay'])
        swa_model = AveragedModel(model)
        swa_scheduler = SWALR(phase_c_optimizer, swa_lr=phase_c_lr)

        with open(log_path, "a") as log:
            for epoch in range(phase_c_epochs):
                train_loss, train_acc = train_one_epoch(model, train_loader, phase_c_optimizer, clean_criterion, scaler, device, config, mixup_fn=None)
                swa_model.update_parameters(model)
                swa_scheduler.step()

                val_loss, val_acc = evaluate(model, val_loader, val_criterion, device)

                log.write(f"{epoch},C,{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},False\n")
                log.flush()

                now = datetime.now().strftime("%H:%M:%S")
                print(f"[C] Epoch {epoch} | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | {now}")

        # Update batch norm statistics for the SWA averaged model
        print("\nUpdating SWA batch norm statistics...")
        update_bn(train_loader, swa_model, device=device)

        # Evaluate the SWA model
        swa_val_loss, swa_val_acc = evaluate(swa_model, val_loader, val_criterion, device)
        print(f"SWA Val Loss: {swa_val_loss:.4f} | SWA Val Acc: {swa_val_acc:.4f}")

        # Save SWA model
        swa_checkpoint_path = ML_DIR / config['checkpoint_dir'] / "best_model_swa.pth"
        torch.save({
            'epoch': phase_c_epochs,
            'phase': 'C',
            'model_state': swa_model.module.state_dict(),
            'val_acc': swa_val_acc,
            'num_classes': config['num_classes'],
            'class_map': class_map,
        }, swa_checkpoint_path)
        print(f"SWA model saved to {swa_checkpoint_path}")

        # Also save the non-SWA Phase C model for comparison
        phase_c_val_loss, phase_c_val_acc = evaluate(model, val_loader, val_criterion, device)
        print(f"Non-SWA Phase C Val Loss: {phase_c_val_loss:.4f} | Val Acc: {phase_c_val_acc:.4f}")

        if swa_val_acc > phase_c_val_acc:
            print(f"\nSWA model wins ({swa_val_acc:.4f} vs {phase_c_val_acc:.4f})")
        else:
            print(f"\nNon-SWA model wins ({phase_c_val_acc:.4f} vs {swa_val_acc:.4f})")

        best_final_acc = max(swa_val_acc, phase_c_val_acc, best_val_acc)
        print(f"\nTraining complete. Best overall val accuracy: {best_final_acc:.4f}")


if __name__ == "__main__":
    main()
