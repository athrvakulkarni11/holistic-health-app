from fastapi import File, UploadFile, HTTPException
from PIL import Image
import io
import os
import numpy as np
from tensorflow.keras.models import load_model
from .. import BaseModel
from .utils import preprocess_image

class DiabeticRetinopathyModel(BaseModel):
    def load_model(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, 'weights', 'diabetic-retinopathy.h5')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model file not found at {model_path}")
                
            print(f"Loading model from: {model_path}")
            self.model = load_model(model_path)
            
            # Print model architecture
            self.model.summary()
            print("Input shape:", self.model.input_shape)
            print("Output shape:", self.model.output_shape)
            
        except Exception as e:
            print(f"Error loading model: {e}")
            raise RuntimeError(f"Failed to load diabetic retinopathy model: {e}")

    async def predict(self, file: UploadFile = File(...)):
        try:
            # Read and preprocess image
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            
            # Print original image info
            print(f"Original image size: {image.size}")
            print(f"Original image mode: {image.mode}")
            
            processed_image = preprocess_image(image)
            print(f"Processed image shape: {processed_image.shape}")
            
            # Make prediction
            prediction = self.model.predict(processed_image, verbose=1)
            print(f"Raw prediction output: {prediction}")
            
            # Get the predicted class and confidence
            class_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][class_idx])
            
            # Map class index to severity level
            severity_levels = ['No DR', 'Mild', 'Moderate', 'Severe', 'Proliferative DR']
            predicted_class = severity_levels[class_idx]
            
            print(f"Predicted class: {predicted_class}")
            print(f"Confidence: {confidence}")
            
            return {
                "prediction": predicted_class,
                "confidence": confidence
            }
                
        except Exception as e:
            print(f"Detailed error in prediction: {str(e)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=str(e))
