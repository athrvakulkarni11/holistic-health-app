from PIL import Image
import io

def process_image(image_data):
    """
    Basic image processing if needed before sending to Roboflow
    """
    image = Image.open(io.BytesIO(image_data))
    if image.mode != 'RGB':
        image = image.convert('RGB')
    return image 