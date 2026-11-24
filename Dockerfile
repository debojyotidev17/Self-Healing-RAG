FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data
COPY src/ ./src/
COPY data/ ./data/
COPY eval/ ./eval/
COPY streamlit_app.py .
COPY .env.example .env

# Expose API and Streamlit ports
EXPOSE 8000
EXPOSE 8501

# Default command launches FastAPI server
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
