from fastapi import File, UploadFile, HTTPException
from PIL import Image
import io
import os
from inference_sdk import InferenceHTTPClient
from .. import BaseModel
from .config import API_KEY

class XRaySamplesModel(BaseModel):
    def load_model(self):
        try:
            self.client = InferenceHTTPClient(
                api_url="https://detect.roboflow.com",
                api_key=API_KEY
            )
            self.model_id = "x-ray-images-sample/2"
            print("Roboflow client initialized successfully")
        except Exception as e:
            print(f"Error initializing Roboflow client: {e}")
            raise RuntimeError(f"Failed to initialize X-ray samples model: {e}")

    async def predict(self, file: UploadFile = File(...)):
        try:
            # Read image data
            image_data = await file.read()
            
            # Save temporarily to pass to Roboflow
            temp_path = "temp_image.jpg"
            with open(temp_path, "wb") as f:
                f.write(image_data)
            
            try:
                # Make prediction using Roboflow
                result = self.client.infer(temp_path, model_id=self.model_id)
                
                # Process all detections
                if result and isinstance(result, dict) and 'predictions' in result:
                    predictions = result['predictions']
                    if predictions:
                        # Return all predictions
                        return {
                            "predictions": [
                                {
                                    "prediction": pred.get('class', 'Unknown'),
                                    "confidence": pred.get('confidence', 0.0),
                                    "bbox": {
                                        "x": pred.get('x', 0),
                                        "y": pred.get('y', 0),
                                        "width": pred.get('width', 0),
                                        "height": pred.get('height', 0)
                                    }
                                } for pred in predictions
                            ]
                        }
                
                return {
                    "predictions": []
                }
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        except Exception as e:
            print(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e)) 