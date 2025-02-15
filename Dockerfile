FROM python:3.11.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy .env
COPY .env .env

# Run migrations and collect static files
RUN python faq_system/manage.py collectstatic --noinput

# Command to run on container start
CMD ["python", "faq_system/manage.py", "runserver", "0.0.0.0:8000"]