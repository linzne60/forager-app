                        
import json                                                                                                                                              
from datetime import datetime
from pathlib import Path

import timm
import torch
import torch.nn.functional as F                                                                                                                          
from torch import amp
from torch.utils.data import DataLoader                                                                                                                  
from torchvision.transforms import v2

from training.dataset import DistillDataset


def load_config(config_path):
    with open(config_path, 'r') as f:
        return json.load(f)                                                                                                                              

                                                                                                                                                        
def build_transforms(config):
    teacher_size = config['teacher_img_size']
    student_size = config['student_img_size']

    # deterministic — teacher should give consistent, high-quality soft targets                                                                          
    teacher_transform = v2.Compose([
        v2.Resize(teacher_size + 20),                                                                                                                    
        v2.CenterCrop(teacher_size),                                                                                                                     
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),                                                                                                           
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])                                                                                                                                                   

    student_train_transform = v2.Compose([                                                                                                               
        v2.RandomResizedCrop(student_size, scale=(0.7, 1.0)),
        v2.RandomHorizontalFlip(),                                                                                                                       
        v2.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        v2.RandomRotation(15),                                                                                                                           
        v2.RandAugment(num_ops=2, magnitude=12),
        v2.ToImage(),                                                                                                                                    
        v2.ToDtype(torch.float32, scale=True),
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),                                                                             
    ])                                                                                                                                                   

    student_val_transform = v2.Compose([                                                                                                                 
        v2.Resize(student_size + 20),
        v2.CenterCrop(student_size),
        v2.ToImage(),
        v2.ToDtype(torch.float32, scale=True),                                                                                                           
        v2.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])                                                                                                                                                   
                        
    return teacher_transform, student_train_transform, student_val_transform                                                                             

                                                                                                                                                        
def build_dataloaders(config, class_map):
    ML_DIR = Path(__file__).parent.parent
    DATA_DIR = ML_DIR / config['data_dir']
    ROOT_DIR = ML_DIR.parent
                                                                                                                                                        
    teacher_transform, student_train_transform, student_val_transform = build_transforms(config)
                                                                                                                                                        
    train_data = DistillDataset(
        DATA_DIR / "train.csv", class_map,
        teacher_transform, student_train_transform, root_dir=ROOT_DIR
    )                                                                                                                                                    
    val_data = DistillDataset(
        DATA_DIR / "val.csv", class_map,                                                                                                                 
        teacher_transform, student_val_transform, root_dir=ROOT_DIR
    )
                                                                                                                                                        
    train_loader = DataLoader(
        train_data, batch_size=config['batch_size'],                                                                                                     
        num_workers=config['num_workers'], shuffle=True, drop_last=True
    )
    val_loader = DataLoader(
        val_data, batch_size=config['batch_size'],
        num_workers=config['num_workers'], shuffle=False                                                                                                 
    )
                                                                                                                                                        
    return train_loader, val_loader


def build_teacher(config, device):
    model = timm.create_model(
        config['teacher_model'],
        pretrained=False,                                                                                                                                
        num_classes=config['num_classes'],
    )                                                                                                                                                    
                        
    ML_DIR = Path(__file__).parent.parent
    checkpoint = torch.load(ML_DIR / config['teacher_checkpoint'], map_location=device)
    model.load_state_dict(checkpoint['model_state'])                                                                                                     
    model.to(device)
    model.eval()                                                                                                                                         
                        
    for param in model.parameters():
        param.requires_grad = False

    return model


def build_student(config):
    model = timm.create_model(
        config['student_model'],                                                                                                                         
        pretrained=True,
        num_classes=config['num_classes'],                                                                                                               
        drop_rate=config.get('drop_rate', 0.0),
        drop_path_rate=config.get('drop_path_rate', 0.0),
    )                                                                                                                                                    
    return model
                                                                                                                                                        
                        
def distillation_loss(student_logits, teacher_logits, labels, temperature, alpha):
    soft_student = F.log_softmax(student_logits / temperature, dim=1)
    soft_teacher = F.softmax(teacher_logits / temperature, dim=1)                                                                                        

    kl_loss = F.kl_div(soft_student, soft_teacher, reduction='batchmean') * (temperature ** 2)                                                           
    hard_loss = F.cross_entropy(student_logits, labels)
                                                                                                                                                        
    return alpha * kl_loss + (1 - alpha) * hard_loss


def train_one_epoch(student, teacher, loader, optimizer, scaler, device, config):
    student.train()
    optimizer.zero_grad()                                                                                                                                

    accum_steps = config.get('accum_steps', 1)                                                                                                           
    temperature = config['temperature']
    alpha = config['alpha']
    total_loss, correct, total = 0, 0, 0
                                                                                                                                                        
    for i, (teacher_imgs, student_imgs, labels) in enumerate(loader):
        teacher_imgs = teacher_imgs.to(device)                                                                                                           
        student_imgs = student_imgs.to(device)
        labels = labels.to(device)

        with torch.no_grad():                                                                                                                            
            teacher_logits = teacher(teacher_imgs)
                                                                                                                                                        
        with amp.autocast('cuda'):
            student_logits = student(student_imgs)
            loss = distillation_loss(
                student_logits, teacher_logits, labels, temperature, alpha
            ) / accum_steps                                                                                                                              

        scaler.scale(loss).backward()                                                                                                                    
                        
        if (i + 1) % accum_steps == 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
                                                                                                                                                        
        total_loss += loss.item() * accum_steps
        correct += (student_logits.argmax(dim=1) == labels).sum().item()                                                                                 
        total += labels.size(0)

    return total_loss / len(loader), correct / total                                                                                                     

                                                                                                                                                        
def evaluate(student, loader, device):
    student.eval()
    total_loss, correct, total = 0, 0, 0
    criterion = torch.nn.CrossEntropyLoss()
                                                                                                                                                        
    with torch.no_grad():
        for teacher_imgs, student_imgs, labels in loader:                                                                                                
            student_imgs = student_imgs.to(device)
            labels = labels.to(device)

            with amp.autocast('cuda'):
                outputs = student(student_imgs)
                loss = criterion(outputs, labels)                                                                                                        

            total_loss += loss.item()                                                                                                                    
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += labels.size(0)

    return total_loss / len(loader), correct / total                                                                                                     

                                                                                                                                                        
def main():             
    ML_DIR = Path(__file__).parent.parent
    config = load_config(ML_DIR / "configs" / "distill_config.json")

    with open(ML_DIR / "data" / "splits" / "class_map.json") as f:                                                                                       
        class_map = json.load(f)
                                                                                                                                                        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    teacher = build_teacher(config, device)                                                                                                              
    student = build_student(config).to(device)
                                                                                                                                                        
    print(f"Device: {device}")
    print(f"Teacher: {config['teacher_model']} (frozen)")
    print(f"Student: {config['student_model']}")
    print(f"Temperature: {config['temperature']} | Alpha: {config['alpha']}")
                                                                                                                                                        
    train_loader, val_loader = build_dataloaders(config, class_map)
    print(f"Train batches per epoch: {len(train_loader)}")                                                                                               
    print(f"Effective batch size: {config['batch_size'] * config.get('accum_steps', 1)}")
                                                                                                                                                        
    optimizer = torch.optim.AdamW(
        student.parameters(), lr=config['lr'], weight_decay=config['weight_decay']                                                                       
    )                                                                                                                                                    

    warmup_epochs = config.get('warmup_epochs', 3)                                                                                                       
    total_epochs = config['epochs']

    warmup_scheduler = torch.optim.lr_scheduler.LinearLR(
        optimizer, start_factor=0.1, total_iters=warmup_epochs
    )                                                                                                                                                    
    cosine_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=total_epochs - warmup_epochs                                                                                                    
    )                   
    scheduler = torch.optim.lr_scheduler.SequentialLR(
        optimizer, [warmup_scheduler, cosine_scheduler], milestones=[warmup_epochs]                                                                      
    )
                                                                                                                                                        
    scaler = torch.amp.GradScaler('cuda')

    checkpoint_dir = ML_DIR / config['checkpoint_dir']                                                                                                   
    checkpoint_dir.mkdir(exist_ok=True)
    checkpoint_path = checkpoint_dir / "best_student.pth"                                                                                                
    log_path = checkpoint_dir / "training_log.txt"

    best_val_acc = 0.0                                                                                                                                   
    patience = config.get('patience', 10)
    no_improve = 0                                                                                                                                       
                        
    print(f"\n--- Distillation Training ---")

    with open(log_path, "w") as log:
        log.write("epoch,train_loss,train_acc,val_loss,val_acc,lr,saved\n")
                                                                                                                                                        
        for epoch in range(total_epochs):
            train_loss, train_acc = train_one_epoch(                                                                                                     
                student, teacher, train_loader, optimizer, scaler, device, config
            )                                                                                                                                            
            val_loss, val_acc = evaluate(student, val_loader, device)
                                                                                                                                                        
            current_lr = optimizer.param_groups[0]['lr']
            scheduler.step()

            saved = val_acc > best_val_acc                                                                                                               
            if saved:
                best_val_acc = val_acc                                                                                                                   
                no_improve = 0
                torch.save({
                    'epoch': epoch,
                    'model_state': student.state_dict(),
                    'optimizer_state': optimizer.state_dict(),
                    'val_acc': val_acc,                                                                                                                  
                    'num_classes': config['num_classes'],
                    'class_map': class_map,                                                                                                              
                }, checkpoint_path)
            else:
                no_improve += 1
                if no_improve >= patience:                                                                                                               
                    print(f"Early stopping — no improvement for {patience} epochs")
                    break                                                                                                                                
                        
            log.write(f"{epoch},{train_loss:.4f},{train_acc:.4f},{val_loss:.4f},{val_acc:.4f},{current_lr:.6f},{saved}\n")                               
            log.flush()
                                                                                                                                                        
            now = datetime.now().strftime("%H:%M:%S")
            status = "✓ saved" if saved else f"patience {no_improve}/{patience}"
            print(f"Epoch {epoch} | Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | LR: {current_lr:.6f} | {status} | {now}")                                                                                                                    

    print(f"\nDistillation complete. Best val accuracy: {best_val_acc:.4f}")                                                                             
                        

if __name__ == "__main__":
    main()