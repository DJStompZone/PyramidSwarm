FROM python:3.13.0-slim-bookworm

# Install dependencies
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
CMD ["python", "app.py"]
