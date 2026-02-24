import numpy as np
from PIL import Image
import tensorflow as tf

def preprocess_image(image):
    try:
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize to exactly 150x150 as expected by the model
        target_size = (150, 150)
        image = image.resize(target_size)
        
        # Convert to array and preprocess
        img_array = np.array(image)
        
        # Normalize to [0,1]
        img_array = img_array.astype('float32') / 255.0
        
        # Add batch dimension but keep the 3D structure
        img_array = np.expand_dims(img_array, axis=0)  # Shape will be (1, 150, 150, 3)
        
        print(f"Preprocessed image shape: {img_array.shape}")
        return img_array
        
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        raise e 