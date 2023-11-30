# Use the official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application code to the working directory
COPY . .

# Install the Python dependencies
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Expose the port on which the application will run
EXPOSE 8080

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]