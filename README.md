# Plant Disease Detection

Classifies plant leaf diseases from photos with a ResNet written from scratch in PyTorch. A FastAPI backend serves the model. It also calls Gemini on Vertex AI to explain the diagnosis, answer follow-up questions and produce a PDF report in several Indian languages. The UI is a Next.js app.

## Features

- **Batch prediction**: `POST /predict/` takes one or more images and returns the top-10 classes with softmax confidence. If the top-1 confidence is at or below `PREDICTION_THRESHOLD` (0.7), the API returns the label `"Healthy image"` instead.
- **Diagnosis + explanation**: `POST /analyze/` takes one image and a `language` code. It runs the classifier and then asks Gemini for causes, symptoms, prevention and treatment in that language.
- **Follow-up chat**: `POST /generate-stream` streams Gemini's answer as plain text.
- **PDF report**: `POST /generate-pdf/` summarises the chat transcript into a structured report, generates it with Gemini, and renders it with ReportLab.
- **Languages**: the backend maps `en, hi, kn, ta, ml, bn, gu, pa, te`. The frontend currently offers English, Hindi, Kannada, Tamil and Malayalam.
- **Frontend** (`frontend/`): Next.js 15 + Tailwind + shadcn/ui. It has a multi-image prediction page and a chat sidebar for analysis, follow-up questions and PDF export.

## Architecture

```
Next.js frontend (:3000)
   |  /predict/  /analyze/  /generate-stream  /generate-pdf/
   v
FastAPI backend (:8000, app/main.py)
   |-- ResNet classifier (model/final_model.pth, 38 classes)
   '-- Gemini via Vertex AI (google-genai), used by analyze/stream/pdf routes
```

## Model

`src/Models/resnet.py` defines `ResNet50`: four residual stages with `[3, 4, 6, 3]` two-layer basic blocks, global average pooling and a linear head. This is the ResNet-34 layout. The original ResNet-50 uses bottleneck blocks. The committed checkpoint `model/final_model.pth` has a 38-way output layer.

Training (`training_model.py`): Adam (lr 1e-4), batch size 128, 20 epochs, 224x224 inputs with random flips and random resized crops. A checkpoint is saved every epoch to `checkpoints/`. The training script expects `Plantdisease/{train,valid,test}/<class>/*`.

Dataset: [khushwant04/Plant-Disease-Dataset](https://huggingface.co/datasets/khushwant04/Plant-Disease-Dataset) on Hugging Face (`plant-disease-data.tar`).

## Project structure

```
app/
  main.py               FastAPI app, CORS, router registration, model load on startup
  config.py             Paths, Gemini model, GCP project/location (env-overridable)
  models/model_loader.py  Singleton that loads the checkpoint and class names
  router/
    prediction.py       GET /, POST /predict/
    analyse.py          POST /analyze/
    generation.py       POST /generate-stream
    pdf_report.py       POST /generate-pdf/
    data_viz.py         POST /generate-visualization/ (not registered in main.py)
  utils.py              Inference preprocessing
src/
  Models/resnet.py      Residual network
  datasets/plant_disease.py  Dataset, transforms, dataloaders
  train.py, helper.py   Training loop class and helpers
training_model.py       Training script with checkpointing
model/final_model.pth   Trained weights
frontend/               Next.js UI
main.py, gemini.py      Earlier single-file API and a Gemini test script (superseded by app/)
```

## Getting started

### Prerequisites

- Python 3.10+ and Node.js 18+
- The class folder names. The API builds its index-to-class mapping from the sorted sub-folders of `Plantdisease/train/`, so download and extract the dataset tarball there first. Only the folder names are read at startup.
- For the Gemini routes: a Google Cloud project with Vertex AI enabled and Application Default Credentials (`gcloud auth application-default login`). `/predict/` works without these.

### Backend

```bash
git clone https://github.com/khushwant04/Plant-Disease.git
cd Plant-Disease
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export GOOGLE_CLOUD_PROJECT=<your-gcp-project>   # default in app/config.py is the author's project
make run                                         # uvicorn app.main:app --reload  -> http://localhost:8000/docs
```

| Variable | Default |
| --- | --- |
| `MODEL_PATH` | `model/final_model.pth` |
| `DATASET_PATH` | `Plantdisease/train` |
| `GOOGLE_CLOUD_PROJECT` | `hexel-studio-admin` |
| `GOOGLE_CLOUD_LOCATION` | `us-central1` |
| `GEMINI_MODEL` | `gemini-2.5-pro-preview-05-06` |

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev   # http://localhost:3000
```

The prediction page (`src/app/page.tsx`) calls `http://localhost:8000/predict/` directly. Only the chat sidebar reads `NEXT_PUBLIC_API_URL`.

### Docker (backend)

```bash
docker build -t plant-disease-api .
docker run --rm -p 8000:8000 \
  -v "$PWD/Plantdisease:/app/Plantdisease:ro" \
  -v "$HOME/.config/gcloud/application_default_credentials.json:/creds.json:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS=/creds.json \
  -e GOOGLE_CLOUD_PROJECT=<your-gcp-project> \
  plant-disease-api
```

## API example

```bash
curl -F "files=@leaf1.jpg" -F "files=@leaf2.jpg" http://localhost:8000/predict/
curl -F "file=@leaf1.jpg" -F "language=kn" http://localhost:8000/analyze/
```

Sample test images: [OneDrive folder](https://1drv.ms/f/s!Akr767JWN3vEllsH0PqUESUpbakN?e=rETLSX).
