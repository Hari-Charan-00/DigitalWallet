# Use a slim Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only requirements first for better Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest (better to include this in requirements.txt if it's part of dev/test)
RUN pip install --no-cache-dir pytest

# Copy the rest of the application code
COPY . .

# Expose port for FastAPI
EXPOSE 9000

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "DigiApi:app", "--host", "0.0.0.0", "--port", "9000", "--reload"]
