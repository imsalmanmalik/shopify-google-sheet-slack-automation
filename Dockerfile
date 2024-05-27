# Use the official Python image from the Docker Hub
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt and application code into the container
COPY requirements.txt fetch_shopify_data.py ./

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Specify the command to run on container start
CMD ["python", "fetch_shopify_data.py"]
