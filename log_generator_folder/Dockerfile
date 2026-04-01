# Use official Python 3.11 image as the base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt (copy even if empty for consistency)
COPY requirements.txt .

# Install dependencies (if any)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Set startup command
CMD ["python", "app.py"]
