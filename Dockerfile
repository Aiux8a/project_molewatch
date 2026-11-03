# This will be the container setup for the cloudrun

FROM python:3.10-slim

WORKDIR /workspace

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY molewatch_app/ ./molewatch_app/

# Expose port 8080 for Cloud Run
EXPOSE 8080

CMD ["uvicorn", "molewatch_app.main:app", "--host", "0.0.0.0", "--port", "8080"]
