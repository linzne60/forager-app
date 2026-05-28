import csv
from pathlib import Path
from PIL import Image
from torch.utils.data import Dataset


class PlantDataset(Dataset):
    def __init__(self, csv_path, class_map, transform=None, root_dir=None):
        self.labels = []
        self.img_paths = []
        self.transform = transform
        self.root_dir = Path(root_dir) if root_dir else None
        self.map = {}

        for k, plant in class_map.items():
            self.map[plant] = int(k)

        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.labels.append(row['label'])
                self.img_paths.append(row['path'])

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        
        img_path = self.img_paths[idx]
        if self.root_dir:
            img_path = self.root_dir / img_path

        img = Image.open(img_path)
        img = img.convert("RGB")

        if self.transform:
            img = self.transform(img)

        class_name = self.map[self.labels[idx]]

        return img, class_name


class DistillDataset(Dataset):                                                                                                                           
    def __init__(self, csv_path, class_map, teacher_transform, student_transform, root_dir=None):                                                        
        self.labels = []
        self.img_paths = []                                                                                                                              
        self.teacher_transform = teacher_transform                                                                                                       
        self.student_transform = student_transform
        self.root_dir = Path(root_dir) if root_dir else None                                                                                             
        self.map = {}   

        for k, plant in class_map.items():                                                                                                               
            self.map[plant] = int(k)
                                                                                                                                                        
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)

            for row in reader:
                self.labels.append(row['label'])
                self.img_paths.append(row['path'])
                                                                                                                                                        
    def __len__(self):
        return len(self.labels)                                                                                                                          
                        
    def __getitem__(self, idx):

        img_path = self.img_paths[idx]
        if self.root_dir:
            img_path = self.root_dir / img_path
                                                                                                                                                        
        img = Image.open(img_path)
        img = img.convert("RGB")                                                                                                                         
                        
        teacher_img = self.teacher_transform(img)
        student_img = self.student_transform(img)
                                                                                                                                                        
        class_name = self.map[self.labels[idx]]
                                                                                                                                                        
        return teacher_img, student_img, class_name