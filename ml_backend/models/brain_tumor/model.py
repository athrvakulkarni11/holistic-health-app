from fastapi import File, UploadFile, HTTPException
from PIL import Image
import io
import os
from inference_sdk import InferenceHTTPClient
from .. import BaseModel

class BrainTumorModel(BaseModel):
    def load_model(self):
        try:
            self.client = InferenceHTTPClient(
                api_url="https://outline.roboflow.com",
                api_key="ejX2g8OKP9TO4VxUTvVp"
            )
            self.model_id = "brain-tumor-40crk-zgelw/1"
            # Set confidence threshold
            self.confidence_threshold = 0.5
            print("Roboflow client initialized successfully")
        except Exception as e:
            print(f"Error initializing Roboflow client: {e}")
            raise RuntimeError(f"Failed to initialize Roboflow client: {e}")

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
                print("Roboflow response:", result)  # Debug print
                
                # Process predictions
                if result and isinstance(result, dict) and 'predictions' in result:
                    predictions = result['predictions']
                    
                    # Filter predictions based on confidence threshold
                    valid_predictions = [
                        pred for pred in predictions 
                        if pred.get('confidence', 0) > self.confidence_threshold
                    ]
                    
                    if valid_predictions:
                        # Get the prediction with highest confidence
                        best_pred = max(valid_predictions, key=lambda x: x.get('confidence', 0))
                        
                        # Check prediction class
                        pred_class = best_pred.get('class', '').lower()
                        
                        if pred_class == 'normal':
                            return {
                                "prediction": "No Tumor Detected",
                                "confidence": best_pred.get('confidence', 0.0)
                            }
                        elif pred_class == 'tumor':
                            return {
                                "prediction": "Tumor Detected",
                                "confidence": best_pred.get('confidence', 0.0),
                                "box": [
                                    best_pred.get('x') - best_pred.get('width')/2,
                                    best_pred.get('y') - best_pred.get('height')/2,
                                    best_pred.get('x') + best_pred.get('width')/2,
                                    best_pred.get('y') + best_pred.get('height')/2
                                ],
                                "points": best_pred.get('points', [])
                            }
                
                # If no valid predictions were found
                return {
                    "prediction": "No Tumor Detected",
                    "confidence": 0.0
                }
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        except Exception as e:
            print(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
