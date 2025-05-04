import torch
from ultralytics import YOLO

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Using device: {device}")

model = YOLO('Models/yolov8n.pt', verbose=False)
model.to(device)
vehicle_classes = {0: "ambulance", 1: "car", 2: "bus", 3: "bike", 4: "truck", 5: "rickshaw"}