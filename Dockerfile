# Use Python 3.8 base image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app on port 5001
EXPOSE 5001

# Run the Flask app
CMD ["python", "app.py"]
