import torch
import torchvision.transforms as transforms
from PIL import Image
import torchvision.transforms as T

def transform_image(image):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Initial input size
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    input_tensor = transform(image)
    input_tensor = input_tensor.unsqueeze(0)  # Add batch dimension
    return input_tensor 

def get_transforms():
    transform = []
    transform.append(T.Resize((512, 512)))
    transform.append(T.ToTensor())
    return T.Compose(transform) 