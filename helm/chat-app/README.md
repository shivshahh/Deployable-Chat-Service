# Chat Service Helm Chart

This Helm chart deploys a complete chat service application with Redis backend on Kubernetes.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+

## Installation

### Install with default values

```bash
helm install chat-service . -n chat-app --create-namespace
```

### Install with custom values

```bash
helm install chat-service . -f custom-values.yaml -n chat-app --create-namespace
```

### Upgrade existing release

```bash
helm upgrade chat-service . -n chat-app
```

### Uninstall

```bash
helm uninstall chat-service -n chat-app
```

## Configuration

The following table lists the configurable parameters and their default values:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `namespace.name` | Namespace name | `chat-app` |
| `namespace.create` | Create namespace | `true` |
| `chatServer.image.repository` | Chat server image repository | `mshenoydocker/chat-server` |
| `chatServer.image.tag` | Chat server image tag | `latest` |
| `chatServer.image.pullPolicy` | Image pull policy | `Always` |
| `chatServer.replicaCount` | Number of chat server replicas | `1` |
| `chatServer.service.type` | Service type | `NodePort` |
| `chatServer.service.port` | Service port | `6000` |
| `chatServer.service.targetPort` | Container port | `6000` |
| `chatServer.service.nodePort` | NodePort (for NodePort type) | `30060` |
| `chatServer.env.redisHost` | Redis hostname | `redis` |
| `chatServer.env.redisPort` | Redis port | `6379` |
| `chatServer.resources.requests.memory` | Memory request | `64Mi` |
| `chatServer.resources.requests.cpu` | CPU request | `50m` |
| `chatServer.resources.limits.memory` | Memory limit | `128Mi` |
| `chatServer.resources.limits.cpu` | CPU limit | `250m` |
| `chatServer.autoscaling.enabled` | Enable HPA | `true` |
| `chatServer.autoscaling.minReplicas` | Minimum replicas | `1` |
| `chatServer.autoscaling.maxReplicas` | Maximum replicas | `10` |
| `chatServer.autoscaling.targetCPUUtilizationPercentage` | CPU target | `70` |
| `chatServer.autoscaling.targetMemoryUtilizationPercentage` | Memory target | `80` |
| `redis.image.repository` | Redis image repository | `redis` |
| `redis.image.tag` | Redis image tag | `7` |
| `redis.replicaCount` | Number of Redis replicas | `1` |
| `redis.service.type` | Redis service type | `ClusterIP` |
| `redis.service.port` | Redis service port | `6379` |
| `redis.persistence.enabled` | Enable Redis persistence | `true` |
| `redis.persistence.storageClass` | Storage class (empty for default) | `""` |
| `redis.persistence.accessMode` | PVC access mode | `ReadWriteOnce` |
| `redis.persistence.size` | PVC size | `500Mi` |

## Example: Custom Values File

```yaml
namespace:
  name: my-chat-app

chatServer:
  replicaCount: 3
  image:
    tag: v1.2.3
  service:
    type: LoadBalancer
  autoscaling:
    minReplicas: 2
    maxReplicas: 20

redis:
  persistence:
    size: 1Gi
```

## Components

This chart deploys:

- **Namespace**: `chat-app` (configurable)
- **Chat Server Deployment**: Main application server
- **Chat Server Service**: Exposes the chat server
- **Redis Deployment**: Redis cache/backend
- **Redis Service**: Internal service for Redis
- **Redis PVC**: Persistent volume for Redis data
- **Horizontal Pod Autoscaler**: Auto-scales chat server based on CPU/memory

## Notes

- The HPA will only be created if `chatServer.autoscaling.enabled` is `true`
- Redis persistence can be disabled by setting `redis.persistence.enabled` to `false`
- The namespace will only be created if `namespace.create` is `true`

