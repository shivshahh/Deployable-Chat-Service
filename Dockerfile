# Use official Python image
FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Copy requirements first for efficient caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Expose the chat server port
EXPOSE 6000

# Run from inside src directory
CMD ["python", "-u", "src/chat_server.py", "6000"]
