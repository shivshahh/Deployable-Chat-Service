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


## Kubernestes

Before deploying, ensure you have:

- **Docker Desktop** (with Kubernetes enabled)
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Enable K8s: Preferences → Kubernetes → Enable Kubernetes

- ✅ **kubectl** (Kubernetes command-line tool)
  ```bash
  # macOS
  brew install kubectl
  
  # Or verify if installed with Docker Desktop
  kubectl version --client
  ```

## 🚀 Quick Start (4 Steps)

### **Step 2: Deploy to Kubernetes**

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Redis
kubectl apply -f k8s/redis.yaml

# Deploy Chat Server
kubectl apply -f k8s/chat-server.yaml

# Deploy Auto-scaling rules
kubectl apply -f k8s/hpa.yaml

### **Step 3: Verify Deployment**
# Check all resources
kubectl get all -n chat-app

# Expected output:
# - 1 chat-server pod (1/1 Running)
# - 1 redis pod (1/1 Running)
# - 2 services (chat-server, redis)


### **Step 4: Run Chat Clients**

**Terminal 1: First client**

python src/chat_client.py localhost 30060 alice


**Terminal 2: Second client**

python src/chat_client.py localhost 30060 bob



### **3. Chat Server Deployment**

Handles multiple client connections and broadcasts messages.


# Check Chat Server pods
kubectl get pods -n chat-app -l app=chat-server

# View Chat Server logs
kubectl logs -n chat-app -l app=chat-server

# Scale manually
kubectl scale deployment chat-server --replicas=3 -n chat-app


### **4. HPA (Horizontal Pod Autoscaler)**

Automatically scales pods based on CPU/memory usage.

```bash
# Check HPA status
kubectl get hpa -n chat-app

# Watch HPA scaling in real-time
kubectl get hpa -n chat-app -w

# View detailed HPA info
kubectl describe hpa chat-server-hpa -n chat-app
```

**Scaling Rules:**
- Minimum: 1 pod
- Maximum: 10 pods
- Scale up if: CPU > 70% OR Memory > 80%
- Scale down if: CPU < 70% AND Memory < 80%

---


## 📈 Testing Auto-Scaling

### **Manual Scaling Test**

```bash
# Terminal 1: Watch pods scale
kubectl get pods -n chat-app -w

# Terminal 2: Scale to 5 pods
kubectl scale deployment chat-server --replicas=5 -n chat-app

# Watch pods transition from Pending → Running
```

### **Load Test (Trigger Auto-Scaling)**

```bash
# Terminal 1: Monitor HPA
kubectl get hpa -n chat-app -w

# Terminal 2: Monitor pods
kubectl get pods -n chat-app -w

# Terminal 3: Generate load
kubectl run -it --rm load-generator --image=busybox /bin/sh -n chat-app

# Inside the pod:
while sleep 0.01; do wget -q -O- http://chat-server:6000; done
```

**Expected behavior:**
- CPU usage increases
- HPA detects > 70% CPU
- New pods are created
- Replicas scale from 1 → 3 → 5 → 10 (as needed)
- When load stops, pods scale back down

---

### **Common Issues**

| Issue | Solution |
|-------|----------|
| Pod stuck in `Pending` | Insufficient resources. Scale down other pods or reduce replicas. |
| `ImagePullBackOff` | Docker image not found. Verify image name in chat-server.yaml. |
| `Connection refused` | Service not running. Check: `kubectl get svc -n chat-app` |
| Metrics `<unknown>` | Metrics server not configured. This is okay for local testing. |

---
