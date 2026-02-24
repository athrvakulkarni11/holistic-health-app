from fastapi import File, UploadFile, HTTPException
from PIL import Image
import io
import os
from inference_sdk import InferenceHTTPClient
from .. import BaseModel

class SkinDiseaseModel(BaseModel):
    def load_model(self):
        try:
            self.client = InferenceHTTPClient(
                api_url="https://outline.roboflow.com",
                api_key="ejX2g8OKP9TO4VxUTvVp"
            )
            self.model_id = "skin-disease-prediction-1ej1a/6"
            self.confidence_threshold = 0.4
            
            # Updated condition categories based on new model classes
            self.condition_types = [
                'Acne-and-Rosacea',
                "Athlete's-foot",
                'Chickenmonkey pox',
                'Cold-Sores',
                'Contact-Dermatitis',
                'Eczema',
                'Hives',
                'Keratosis pilaris',
                'Lupus',
                'Moles',
                'Psoriasis',
                'Ringworm',
                'Shingles',
                'Skin-cancer-(Basal-cell-carcinoma)',
                'Skin-cancer-(Melanoma)',
                'Skin-cancer-(Squamous-cell-carcinoma)',
                'Vitiligo',
                'Warts',
                'cyst',
                'nail-fungus'
            ]
            
            print("Roboflow client initialized successfully")
        except Exception as e:
            print(f"Error initializing Roboflow client: {e}")
            raise RuntimeError(f"Failed to initialize Roboflow client: {e}")

    async def predict(self, file: UploadFile = File(...)):
        try:
            image_data = await file.read()
            temp_path = "temp_image.jpg"
            
            with open(temp_path, "wb") as f:
                f.write(image_data)
            
            try:
                result = self.client.infer(temp_path, model_id=self.model_id)
                print("API Response:", result)  # Debug print
                
                if result and isinstance(result, dict) and 'predictions' in result:
                    predictions = result['predictions']
                    if predictions:
                        # Filter predictions by confidence threshold
                        valid_predictions = [
                            pred for pred in predictions 
                            if pred.get('confidence', 0) > self.confidence_threshold
                        ]
                        
                        if valid_predictions:
                            best_pred = max(valid_predictions, key=lambda x: x.get('confidence', 0))
                            
                            # Extract all necessary information
                            return {
                                "prediction": best_pred.get('class', 'Unknown'),
                                "confidence": best_pred.get('confidence', 0.0),
                                "box": [
                                    best_pred.get('x') - best_pred.get('width')/2,
                                    best_pred.get('y') - best_pred.get('height')/2,
                                    best_pred.get('x') + best_pred.get('width')/2,
                                    best_pred.get('y') + best_pred.get('height')/2
                                ],
                                "points": best_pred.get('points', []),
                                "severity": "high" if "cancer" in best_pred.get('class', '').lower() else "moderate"
                            }
                
                return {
                    "prediction": "No specific condition detected",
                    "confidence": 0.0,
                    "box": None,
                    "points": [],
                    "severity": "low"
                }
                
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
        except Exception as e:
            print(f"Prediction error: {e}")
            print(f"Error details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) 