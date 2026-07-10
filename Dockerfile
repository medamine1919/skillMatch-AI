# ===== FastAPI SkillMatch AI =====
FROM python:3.11-slim

WORKDIR /app

# Dépendances système (Tesseract OCR + libs pour PyMuPDF/Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python avec retry et timeout étendus
# (utile pour les connexions lentes/instables)
COPY requirements-docker.txt .
ENV PIP_DEFAULT_TIMEOUT=300 \
    PIP_RETRIES=10 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --upgrade pip && \
    pip install -r requirements-docker.txt

# Copier tout le projet
COPY . .

# Créer les dossiers requis
RUN mkdir -p data/uploads data/exports data/temp database resources assets

EXPOSE 8000

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
