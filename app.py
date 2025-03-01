import os
import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
from fastapi import FastAPI, File, UploadFile
from typing import List, Dict
from shutil import rmtree
from groq import Groq
from dotenv import load_dotenv
from ml_backend.models.brain_tumor.model import BrainTumorModel
from ml_backend.models.diabetic_retinopathy.model import DiabeticRetinopathyModel
from ml_backend.models.skin_disease.model import SkinDiseaseModel
from ml_backend.models.xray_samples.model import XRaySamplesModel
import json
import io
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException

load_dotenv()
app = FastAPI()
    
OUTPUT_DIR = "output"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize ML models
brain_tumor_model = BrainTumorModel()
diabetic_retinopathy_model = DiabeticRetinopathyModel()
skin_disease_model = SkinDiseaseModel()
xray_samples_model = XRaySamplesModel()

async def scan_image_with_models(image_path: str) -> Dict:
    """Scan an image with all available ML models and return results."""
    results = {}
    base_name = os.path.basename(image_path)
    output_dir = os.path.join(OUTPUT_DIR, "annotated_images")
    os.makedirs(output_dir, exist_ok=True)
    
    with open(image_path, "rb") as f:
        file_content = f.read()
    
    upload_file = UploadFile(
        file=io.BytesIO(file_content),
        filename=base_name,
        headers={"content-type": "image/png"}
    )

    try:
        # Open image for annotation
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # Use a larger font size for better visibility
        try:
            font = ImageFont.truetype("arial.ttf", 24)
        except:
            font = ImageFont.load_default()
        
        for model_name, model in [
            ("brain_tumor", brain_tumor_model),
            ("diabetic_retinopathy", diabetic_retinopathy_model),
            ("skin_disease", skin_disease_model),
            ("xray", xray_samples_model)
        ]:
            upload_file.file.seek(0)
            result = await model.predict(upload_file)
            
            # Adjust confidence thresholds
            if model_name == "brain_tumor":
                confidence_threshold = 0.65
            elif model_name == "diabetic_retinopathy":
                confidence_threshold = 0.75
            else:
                confidence_threshold = 0.60
                
            if result:
                valid_prediction = False
                
                if "prediction" in result and result.get("confidence", 0) > confidence_threshold:
                    valid_prediction = True
                elif "predictions" in result:
                    valid_predictions = [p for p in result["predictions"] 
                                      if p.get("confidence", 0) > confidence_threshold]
                    if valid_predictions:
                        valid_prediction = True
                        result["predictions"] = valid_predictions

                if valid_prediction:
                    results[model_name] = result
                    annotated_path = os.path.join(output_dir, f"{model_name}_{base_name}")
                    
                    # Draw annotations with improved visibility
                    if "box" in result:
                        box = result["box"]
                        # Draw white background for text
                        text = f"{result['prediction']} ({result['confidence']:.2f})"
                        text_bbox = draw.textbbox((box[0], box[1]-30), text, font=font)
                        draw.rectangle(text_bbox, fill="white")
                        # Draw red box and text
                        draw.rectangle(box, outline="red", width=3)
                        draw.text((box[0], box[1]-30), text, fill="red", font=font)
                        
                    elif "predictions" in result:
                        for pred in result["predictions"]:
                            if "bbox" in pred:
                                bbox = pred["bbox"]
                                x, y = bbox["x"], bbox["y"]
                                w, h = bbox["width"], bbox["height"]
                                box = [x-w/2, y-h/2, x+w/2, y+h/2]
                                # Draw white background for text
                                text = f"{pred['prediction']} ({pred['confidence']:.2f})"
                                text_bbox = draw.textbbox((x-w/2, y-h/2-30), text, font=font)
                                draw.rectangle(text_bbox, fill="white")
                                # Draw blue box and text
                                draw.rectangle(box, outline="blue", width=3)
                                draw.text((x-w/2, y-h/2-30), text, fill="blue", font=font)
                    
                    # Save annotated image
                    image.save(annotated_path)
                    results[f"{model_name}_annotated"] = annotated_path

    except Exception as e:
        print(f"Error scanning image: {e}")
        
    return results

async def extract_images_and_text(pdf_bytes: bytes, output_dir: str):
    """Extract text and images from the uploaded PDF file and scan with ML models."""
    
    # Clear output directory
    if os.path.exists(output_dir):
        rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    images_dir = os.path.join(output_dir, "images")
    scans_dir = os.path.join(output_dir, "scan_results")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(scans_dir, exist_ok=True)

    # Extract text and images using PyMuPDF
    doc = fitz.open(stream=pdf_bytes)
    full_text = ""
    image_paths = []
    scan_results = {}

    for page_num, page in enumerate(doc):
        # Extract text
        full_text += page.get_text("text") + "\n"
        
        # Extract images
        image_list = page.get_images(full=True)
        
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Save image
            image_path = os.path.join(images_dir, f"image_{page_num+1}_{img_idx+1}.png")
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            image_paths.append(image_path)
            
            # Scan image with ML models
            results = await scan_image_with_models(image_path)
            
            if results:  # If any conditions were detected
                scan_results[f"image_{page_num+1}_{img_idx+1}"] = results
                
                # Save scan results to JSON
                results_path = os.path.join(scans_dir, f"image_{page_num+1}_{img_idx+1}_results.json")
                with open(results_path, 'w') as f:
                    json.dump(results, f, indent=4)

    return full_text, image_paths, scan_results

def extract_important_terms(text: str) -> Dict:
    """Use Groq to extract key medical terms from text."""
    prompt = f"""
    Extract and return only the key medical metrics from the following text, including:
    - Blood Pressure (BP)
    - Heart Rate
    - Risk Factors (e.g., hypertension, cardiovascular risk, diabetes, etc.)
    - Key medical findings
    
    Return ONLY a valid JSON object with fields: 'blood_pressure', 'heart_rate', 'risk_factors', and 'key_findings'.
    Do not include any markdown formatting, backticks, or extra text.
    
    Text: {text}
    """
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    # Clean up the response content
    content = response.choices[0].message.content
    
    # Remove any markdown formatting or backticks
    content = content.replace('```json', '').replace('```', '').strip()
    
    return content  # Cleaned JSON string

def save_metrics_to_json(metrics_str: str, output_dir: str) -> str:
    """Save extracted medical metrics to a JSON file."""
    try:
        # Parse the metrics string into JSON
        metrics_data = json.loads(metrics_str)
        
        # Create metrics directory if it doesn't exist
        metrics_dir = os.path.join(output_dir, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Save to JSON file
        metrics_file = os.path.join(metrics_dir, "medical_metrics.json")
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=4)
            
        return metrics_file
    except json.JSONDecodeError as e:
        print(f"Error parsing metrics JSON: {e}")
        print(f"Raw metrics string: {metrics_str}")
        metrics_file = None
    except Exception as e:
        print(f"Error saving metrics: {e}")
        metrics_file = None

@app.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()
        extracted_text, images, scan_results = await extract_images_and_text(pdf_bytes, OUTPUT_DIR)

        # Process extracted text with Groq to get key terms
        metrics_str = extract_important_terms(extracted_text)
        
        # Create metrics directory
        metrics_dir = os.path.join(OUTPUT_DIR, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)
        
        # Save metrics to JSON file
        metrics_file = os.path.join(metrics_dir, "medical_metrics.json")
        try:
            # Clean up the metrics string and ensure it's valid JSON
            metrics_str = metrics_str.strip()
            if not metrics_str.startswith('{'):
                raise json.JSONDecodeError("Invalid JSON format", metrics_str, 0)
                
            # Parse the metrics string into JSON
            metrics_data = json.loads(metrics_str)
            
            # Save to JSON file
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, indent=4)
                
        except json.JSONDecodeError as e:
            print(f"Error parsing metrics JSON: {e}")
            print(f"Raw metrics string: {metrics_str}")
            metrics_file = None
            metrics_data = None
        except Exception as e:
            print(f"Error saving metrics: {e}")
            metrics_file = None
            metrics_data = None

        return {
            "message": "PDF processed successfully",
            "metrics": metrics_data,
            "metrics_file": metrics_file,
            "image_files": images,
            "scan_results": scan_results
        }
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
