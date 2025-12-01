# Chat Service – Multi-Client TCP Chat with Redis Persistence

This project implements a lightweight, multi-client chat server and client system using Python sockets, Redis-backed message persistence, and Docker Compose orchestration. Clients can connect, exchange messages in real time, and automatically receive full chat history stored in Redis.

---

## Features

### ✔ Multi-client TCP chat server
- Handles multiple clients using threads  
- Broadcasts messages to all connected users  
- Notifies when users connect/disconnect

### ✔ Chat history saved in Redis
- Messages persist even after the server restarts  
- On connection, clients receive **full chat history** before joining the live chat

### ✔ Simple Python chat client
- Clean CLI interface  
- Real-time message streaming  
- Graceful shutdown using `exit`  
- Dual-threaded input/output (non-blocking)

### ✔ Dockerized Deployment
- Redis container  
- Chat-server container  
- Port mappings for easy local development  
- Persistent Redis volume for message storage

---

## Project Structure

project/
│
├── docker-compose.yml # Runs Redis + Chat Server
│
└── src/
├── chat_server.py # Main TCP chat server
├── chat_client.py # CLI client
├── Dockerfile # Server container definition

---

## Running with Docker Compose

Make sure you have **Docker** and **Docker Compose** installed.

### Start the full system

docker compose up --build

## Connecting a Client

Clients run on your local machine, not inside Docker.
Open a terminal and run:

python src/chat_client.py 127.0.0.1 6000 username


Example:
python src/chat_client.py localhost 6000 alice


Then type messages:
[alice]: Hello everyone!


To exit gracefully:
exit

## How It Works
Server (chat_server.py)
Accepts a TCP socket connection
Reads the username
Sends full chat history (pulled from Redis)
Broadcasts all future messages to every connected client
Saves messages to Redis (rpush chat_history)
Uses per-client threads for concurrent message handling
Client (chat_client.py)
Sends username on connection
Receives chat history until HISTORY_END
Starts:
Reader thread (prints incoming messages)
Writer thread (captures user input)
Uses exit to shut down cleanly
Redis
Stores persistent chat history in a list:
LPUSH chat_history "[alice]: hello"

## Environment Variables

The chat-server container uses the following (defined in docker-compose.yml):

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_USER=optional
REDIS_PASSWORD=optional

## Dockerfile Summary

Based on python:3.13-slim

Installs Redis Python client

Runs chat_server.py at startup

## Testing Locally Without Docker

Start the Redis service on your Linux host:

sudo service redis-server start


Then start the server:

python src/chat_server.py 6000


Start multiple clients:

python src/chat_client.py localhost 6000 user1
python src/chat_client.py localhost 6000 user2
