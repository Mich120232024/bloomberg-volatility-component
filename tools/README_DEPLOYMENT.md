# Bloomberg Gateway Deployment Guide

## Architecture Overview

```
Development (Local):
React App → Local Gateway (No Cache) → Bloomberg VM API → Bloomberg Terminal

Production (Azure):
React App → Gateway (Redis Cache) → Bloomberg VM API → Bloomberg Terminal
```

## Local Development

1. **Run without cache** (fresh Bloomberg data always):
```bash
cd tools
export ENABLE_CACHE=false
python bloomberg-gateway-enhanced.py
```

2. **Update frontend** to use local gateway:
```typescript
// src/api/bloomberg.ts
const BLOOMBERG_API_URL = import.meta.env.DEV 
  ? 'http://localhost:8000'  // Local gateway
  : 'https://bloomberg-gateway.azurewebsites.net'  // Production
```

## Production Deployment Options

### Option 1: Azure Container Apps (Recommended)
```bash
# Build and push to Azure Container Registry
az acr build --registry $ACR_NAME --image bloomberg-gateway:latest .

# Deploy to Container Apps
az containerapp create \
  --name bloomberg-gateway \
  --resource-group $RG \
  --image $ACR_NAME.azurecr.io/bloomberg-gateway:latest \
  --target-port 8000 \
  --ingress 'external' \
  --env-vars \
    BLOOMBERG_API_URL=http://20.172.249.92:8080 \
    ENABLE_CACHE=true \
    REDIS_CONNECTION=secretref:redis-connection
```

### Option 2: Azure Kubernetes Service (AKS)
```bash
# Apply Kubernetes deployment
kubectl apply -f deployment.yaml
```

### Option 3: Azure App Service
```bash
# Deploy as web app
az webapp up --name bloomberg-gateway --runtime "PYTHON:3.11"
```

## Environment Variables

| Variable | Development | Production | Description |
|----------|------------|------------|-------------|
| ENABLE_CACHE | false | true | Enable Redis caching |
| REDIS_CONNECTION | - | Azure Redis | Redis connection string |
| BLOOMBERG_API_URL | http://20.172.249.92:8080 | Same | Bloomberg VM endpoint |
| CACHE_TTL | - | 900 | Cache time in seconds |

## Key Features

1. **No cache in dev** - Always fresh Bloomberg data
2. **Redis cache in prod** - Reduces Bloomberg API calls
3. **Health checks** - Kubernetes/container ready
4. **CORS enabled** - Works with React frontend
5. **Ticker intelligence** - Uses 3,001 discovered tickers

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Get volatility surface
curl http://localhost:8000/api/volatility/EURUSD

# Force fresh data (bypass cache)
curl http://localhost:8000/api/volatility/EURUSD?force_fresh=true
```

## Notes

- Gateway is stateless - can scale horizontally
- Redis cache is optional - falls back to in-memory
- All responses include metadata showing data source
- Designed for containerized deployment

-- SOFTWARE_MANAGER @ 2025-07-26T00:45:00Z