FROM python:3-slim

# Copy files
COPY scripts/rotate_keys.py /app/rotate_keys.py
COPY scripts/requirements.txt /app/requirements.txt

# Install boto3
RUN pip install -r /app/requirements.txt

# Make executable
RUN chmod +x /app/rotate_keys.py

# Set working directory
WORKDIR /app

# Run the script
ENTRYPOINT ["python3", "rotate_keys.py"]