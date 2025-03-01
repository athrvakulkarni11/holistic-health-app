import torchvision.transforms as transforms
from PIL import Image

def transform_image(image):
    transform = transforms.Compose([
        transforms.Resize((640, 640)),
        transforms.ToTensor(),
    ])
    
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image_tensor = transform(image)
    return image_tensor.unsqueeze(0)  # Add batch dimension
