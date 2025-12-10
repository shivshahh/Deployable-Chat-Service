```markdown
# Chat Service – Multi-Client TCP Chat with Redis Persistence

This project implements a lightweight, multi-client chat server and client system using Python sockets, Redis-backed message persistence, and Docker Compose orchestration. Clients can connect, exchange messages in real time, and automatically receive full chat history stored in Redis. Clients can also optionally specify a target username to communicate directly with another user when running the Python client.

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
- Optional: send messages directly to another user by passing a second username argument  
  ```
  python src/chat_client.py localhost 30060 alice bob
  ```

### ✔ Dockerized Deployment
- Redis container  
- Chat-server container  
- Port mappings for easy local development  
- Persistent Redis volume for message storage

---

## Project Structure

```
project/
│
├── docker-compose.yml # Runs Redis + Chat Server
│
└── src/
    ├── chat_server.py # Main TCP chat server
    ├── chat_client.py # CLI client
    ├── Dockerfile      # Server container definition
```

---

## Running with Docker Compose

Make sure you have **Docker** and **Docker Compose** installed.

### Start the full system

```
docker compose up --build
```

## Connecting a Client

Clients run on your local machine, not inside Docker.  
Open a terminal and run:

```
python src/chat_client.py 127.0.0.1 6000 username
```

Example:

```
python src/chat_client.py localhost 6000 alice
```

Direct chat mode (optional):

```
python src/chat_client.py localhost 6000 alice bob
```

Then type messages:

```
[alice]: Hello everyone!
```

To exit gracefully:

```
exit
```

---

## How It Works

### Server (chat_server.py)

- Accepts a TCP socket connection  
- Reads the username  
- Sends full chat history (pulled from Redis)  
- Broadcasts all future messages to every connected client  
- Saves messages to Redis (`rpush chat_history`)  
- Uses per-client threads for concurrent message handling  
- Supports routing of messages when clients specify a target user on connect

### Client (chat_client.py)

- Sends username on connection  
- Optionally sends a target username if provided on the command line  
- Receives chat history until `HISTORY_END`  
- Starts:
  - Reader thread (prints incoming messages)  
  - Writer thread (captures user input)  
- Uses `exit` to shut down cleanly  

### Redis

Stores persistent chat history in a list:

```
LPUSH chat_history "[alice]: hello"
```

---

## Environment Variables

The chat-server container uses the following (defined in docker-compose.yml):

```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_USER=optional
REDIS_PASSWORD=optional
```

---

## Dockerfile Summary

- Based on `python:3.13-slim`  
- Installs Redis Python client  
- Runs `chat_server.py` at startup  

---

## Testing Locally Without Docker

Start the Redis service on your Linux host:

```
sudo service redis-server start
```

Then start the server:

```
python src/chat_server.py 6000
```

Start multiple clients:

```
python src/chat_client.py localhost 6000 user1
python src/chat_client.py localhost 6000 user2
```

Direct client-to-client:

```
python src/chat_client.py localhost 6000 alice bob
```

---

## 🚀 Kubernetes

### Prerequisites

Before deploying, ensure you have:

- **Docker Desktop** (with Kubernetes enabled)  
  - Enable K8s: Preferences → Kubernetes → Enable Kubernetes  
- **kubectl**  
  ```
  kubectl version --client
  ```

### Quick Start (4 Steps)

#### **Step 1: Clone Repository**

```bash
git clone https://github.com/mshenoy/Deployable-Chat-Service.git
cd Deployable-Chat-Service
```

#### **Step 2: Deploy to Kubernetes**

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Deploy Chat Server
kubectl apply -f k8s/chat-server.yaml

# Deploy Auto-scaling rules
kubectl apply -f k8s/hpa.yaml
```

#### **Step 3: Verify Deployment**

```bash
kubectl get all -n chat-app
```

Expected output:
- 1 chat-server pod (1/1 Running)  
- 1 redis pod (1/1 Running)  
- 2 services (chat-server, redis)

#### **Step 4: Run Chat Clients**

**Terminal 1:**

```bash
python src/chat_client.py localhost 30060 alice
```

**Terminal 2:**

```bash
python src/chat_client.py localhost 30060 bob
```

Or direct messaging:

```bash
python src/chat_client.py localhost 30060 alice bob
```

---

## Chat Server Deployment

```bash
kubectl get pods -n chat-app -l app=chat-server
kubectl logs -n chat-app -l app=chat-server
kubectl scale deployment chat-server --replicas=3 -n chat-app
```

---

## HPA (Horizontal Pod Autoscaler)

```bash
kubectl get hpa -n chat-app
kubectl get hpa -n chat-app -w
kubectl describe hpa chat-server-hpa -n chat-app
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| Pod stuck in `Pending` | Insufficient resources |
| `ImagePullBackOff` | Verify image name in manifest |
| `Connection refused` | Check service running |
| Metrics `<unknown>` | Metrics server missing |

---

# 🧭 Helm Deployment

```
cd helm/chat-app
helm install chat-service . -n chat-app --create-namespace
```

Check all resources:

```
k get all -n chat-app
```

Expose service URL via minikube:

```
minikube service chat-service-chat-app-server --url -n chat-app
```

Use this URL for Python load testing:

```
cd test
python3 load_test.py --host localhost --port 34843 --clients 100 --messages 5000
```

Open Kubernetes dashboard:

```
minikube dashboard
```
```
