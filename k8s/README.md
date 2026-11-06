# Minikube deployment

This directory contains two Kubernetes layouts for the DocuSage services.

## Prerequisites

- Docker Desktop running
- Minikube running
- `kubectl` available on `PATH`

The manifests use local image names, so build the images inside Minikube's image store:

```powershell
minikube start --nodes=2 --cpus=6 --memory=8192
minikube image build -t docusage-backend:local ./backend
minikube image build -t docusage-ai:local ./ai-service
minikube image build -t docusage-frontend:local ./frontend

kubectl label node minikube docusage-architecture=isolated --overwrite
kubectl label node minikube-m02 docusage-architecture=shared --overwrite
minikube addons enable metrics-server
```

The first Ollama startup downloads `llama3.2:1b`; allow several minutes and enough disk space.

## Architecture 1: isolated application stacks

`k8s/isolated` creates two namespaces on the node labeled `docusage-architecture=isolated`. Each namespace has its own frontend, backend, AI service, PostgreSQL, Ollama model volume, and upload volume. HPA policies keep frontend, backend, and AI service between two and five replicas per tenant. This is the closest Kubernetes equivalent to the left-hand drawing.

```powershell
kubectl apply -k k8s/isolated
kubectl get pods -A
kubectl -n docusage-tenant-a get pods
kubectl -n docusage-tenant-b get pods
kubectl -n docusage-tenant-a get hpa
```

Use one stack locally at a time with two PowerShell terminals:

```powershell
kubectl -n docusage-tenant-a port-forward svc/frontend 3000:3000
kubectl -n docusage-tenant-a port-forward svc/backend 8000:8000
```

Open `http://localhost:3000`. To use tenant B, stop those port-forwards and run the same commands with `docusage-tenant-b`.

Remove both isolated stacks:

```powershell
kubectl delete -k k8s/isolated
```

## Architecture 2: shared services with horizontal scaling

`k8s/shared` creates one shared application on the node labeled `docusage-architecture=shared`. HPA policies keep frontend, backend, and AI service between two and five replicas based on average CPU utilization. PostgreSQL and Ollama intentionally have one replica with persistent volumes; duplicating either without replication would risk data corruption or inconsistent model state.

```powershell
kubectl create namespace docusage-shared --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -k k8s/shared -n docusage-shared
kubectl get pods -n docusage-shared
kubectl wait --for=condition=available deployment --all -n docusage-shared --timeout=10m
kubectl get hpa -n docusage-shared
```

Expose the UI and API locally with two PowerShell terminals:

```powershell
kubectl -n docusage-shared port-forward svc/frontend 3000:3000
kubectl -n docusage-shared port-forward svc/backend 8000:8000
```

Open `http://localhost:3000` and verify the API with `http://localhost:8000/health`.

Useful checks:

```powershell
kubectl -n docusage-shared logs deploy/ollama
kubectl -n docusage-shared logs deploy/ai-service
kubectl -n docusage-shared get pvc
kubectl top pods -n docusage-shared
```

During a test, watch autoscaling in another terminal:

```powershell
kubectl -n docusage-shared get hpa --watch
```

The HPA uses 20% average CPU utilization for testing, scales up after a short 30-second stabilization window, and waits 180 seconds before scaling down. Metrics Server may need a minute after enabling before `kubectl top` and HPA metrics become available.

Remove the shared stack:

```powershell
kubectl delete -k k8s/shared -n docusage-shared
```

## Important local-development note

The frontend image runs Create React App's development server, and its Kubernetes environment points the browser to `http://localhost:8000`. Keep the backend port-forward active in the same machine/browser session. The manifests are intended for Minikube evaluation, not a production cluster.
