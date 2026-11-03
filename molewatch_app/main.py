

from fastapi import FastAPI, File, UploadFile, HTTPException
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import io

app = FastAPI(title="MoleWatch API", description="Skin Lesion Binary Classification API")

# Setup device & architecture
device = torch.device('cpu')
model = models.resnet18()
model.fc = nn.Linear(model.fc.in_features, 1)

# Load checkpoint
model.load_state_dict(torch.load('molewatch_app/model_baseline.pt', map_location=device))
model.to(device)
model.eval()

# Image Preprocessing Transform
val_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

OPTIMAL_THRESHOLD = 0.30

@app.get("/")
def health_check():
    return {"status": "ok", "message": "MoleWatch API is running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File uploaded is not an image.")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        tensor = val_transforms(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(tensor).squeeze(1)
            probability = torch.sigmoid(output).item()

        is_suspicious = probability >= OPTIMAL_THRESHOLD

        return {
            "probability": round(probability, 4),
            "threshold": OPTIMAL_THRESHOLD,
            "prediction": "Suspicious" if is_suspicious else "Benign",
            "is_suspicious": bool(is_suspicious)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")
