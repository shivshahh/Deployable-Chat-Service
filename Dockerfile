# Use official Python image
FROM python:3.13-slim

# Set work directory
WORKDIR /app

# Copy all source code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir redis

# Expose the chat server port
EXPOSE 6000

# Start the chat server
CMD ["python", "chat_server.py", "6000"]

