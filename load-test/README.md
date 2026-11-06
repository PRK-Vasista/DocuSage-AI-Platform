# Independent load-test image

This image is intentionally separate from the application Compose and Kubernetes resources. It has no `depends_on`, no application network, no application credentials, and no startup behavior. It runs only when manually invoked.

## Build

From the repository root:

```powershell
docker build -t docusage-load-test:local .\load-test
```

Or use the standalone Compose file:

```powershell
docker compose -f .\load-test\docker-compose.yaml build
```

The standalone Compose file has no dependency on the application Compose file. It only starts the load generator when you explicitly run it.

## Run a fixed request load

The default target is the backend health endpoint exposed on the host:

```powershell
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

Example: 500 requests, 25 concurrent requests, at most 20 requests per second:

```powershell
$env:TARGET_URL = "http://host.docker.internal:8000/health"
$env:REQUESTS = "500"
$env:CONCURRENCY = "25"
$env:REQUESTS_PER_SECOND = "20"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

## Collect both architecture stats

Forward one backend endpoint from each architecture in separate terminals. For example, use port `8000` for the shared architecture and port `8001` for isolated tenant A:

```powershell
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/backend 8000:8000
kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/backend 8001:8000
```

Then run one independent load-test container against both named targets:

```powershell
$env:TARGETS_JSON = '{"shared":"http://host.docker.internal:8000/health","isolated-tenant-a":"http://host.docker.internal:8001/health"}'
$env:REQUESTS = "500"
$env:CONCURRENCY = "25"
$env:REQUESTS_PER_SECOND = "20"
$env:RESULTS_FILE = "/results/both-architectures.json"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

If PowerShell reports `APPLICATION_TARGETS_JSON must contain valid JSON`, use the file-based form to avoid shell quoting:

```powershell
Copy-Item .\load-test\application-targets.example.json .\load-test\application-targets.json
$env:APPLICATION_TARGETS_JSON = $null
$env:APPLICATION_TARGETS_FILE = "/config/application-targets.json"
$env:LOAD_MODE = "application-crud"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

Edit `load-test/application-targets.json` when your port-forwards differ. The standalone Compose file mounts that file read-only at `/config/application-targets.json`.

The output contains separate statistics for `shared` and `isolated-tenant-a`. The combined JSON report is written to `load-test/results/both-architectures.json` on the host. To include tenant B as well, add another named URL using a third port-forward, such as port `8002`.

## Run for a fixed duration

`DURATION_SECONDS` takes precedence over `REQUESTS` when it is greater than zero:

```powershell
$env:TARGET_URL = "http://host.docker.internal:8000/health"
$env:DURATION_SECONDS = "120"
$env:CONCURRENCY = "20"
$env:REQUESTS_PER_SECOND = "15"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

## Target either architecture

Keep the relevant backend port-forward active, then point the independent load container at it.

```powershell
# Shared architecture
kubectl -n docusage-shared port-forward svc/backend 8000:8000
$env:TARGET_URL = "http://host.docker.internal:8000/health"

# Isolated tenant A, using a different local port
kubectl -n docusage-tenant-a port-forward svc/backend 8001:8000
$env:TARGET_URL = "http://host.docker.internal:8001/health"
```

Run the load command from another terminal so the port-forward remains active.

You can also target the AI service health endpoint after forwarding it:

```powershell
kubectl -n docusage-shared port-forward svc/ai-service 8100:8100
$env:TARGET_URL = "http://host.docker.internal:8100/api/v1/ai/health"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

## POST requests

Use JSON headers and body through environment variables:

```powershell
$env:HTTP_METHOD = "POST"
$env:TARGET_URL = "http://host.docker.internal:8000/api/v1/ai/chat"
$env:REQUEST_HEADERS = '{"Content-Type":"application/json"}'
$env:REQUEST_BODY = '{"question":"What is this document about?","document_context":"A short test document.","history":[]}'
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

The process prints total requests, throughput, status counts, errors, and min/p50/p95/max latency. It exits nonzero when every request fails, or when `FAIL_ON_ERROR=true` and any request fails.

## Application CRUD scenario mode

For application-aware testing, use `LOAD_MODE=application-crud`. This mode uses dummy data and records metrics by architecture, component/container, and operation. It exercises:

- Frontend root requests
- Backend health, registration, login, `/me`, document list, upload, metadata read, summary read, chat history, chat creation, soft delete, trash listing, and permanent delete
- AI-service health, summarize, and chat
- Ollama tags and a small dummy generation request
- PostgreSQL connection plus temporary-table create, insert, read, update, and delete operations

Document files are permanently deleted at the end of each workflow. Test users remain in the database because the application has no user-delete endpoint; use a disposable test database or remove the test database volume after testing.

### Run against both architectures

Forward each service endpoint needed by the scenario. The following example uses shared services on ports ending in `0` and isolated tenant A on ports ending in `1`:

```powershell
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/frontend 3000:3000
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/backend 8000:8000
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/ai-service 8100:8100
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/ollama 11434:11434
kubectl -n docusage-shared port-forward --address=0.0.0.0 svc/db 5432:5432

kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/frontend 3001:3000
kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/backend 8001:8000
kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/ai-service 8101:8100
kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/ollama 11435:11434
kubectl -n docusage-tenant-a port-forward --address=0.0.0.0 svc/db 5433:5432
```

Run the load image from another terminal:

```powershell
$env:LOAD_MODE = "application-crud"
$env:APPLICATION_TARGETS_JSON = '{"shared":{"frontend":"http://host.docker.internal:3000","backend":"http://host.docker.internal:8000","ai":"http://host.docker.internal:8100","ollama":"http://host.docker.internal:11434","database":"postgresql://user:password@host.docker.internal:5432/docu_sage_db"},"isolated-tenant-a":{"frontend":"http://host.docker.internal:3001","backend":"http://host.docker.internal:8001","ai":"http://host.docker.internal:8101","ollama":"http://host.docker.internal:11435","database":"postgresql://user:password@host.docker.internal:5433/docu_sage_db"}}'
$env:SCENARIO_USERS = "5"
$env:SCENARIO_ROUNDS = "2"
$env:SCENARIO_CONCURRENCY = "5"
$env:SCENARIO_PROCESSING_WAIT_SECONDS = "60"
$env:SCENARIO_RUN_CHAT = "true"
$env:SCENARIO_RUN_OLLAMA_INFERENCE = "true"
$env:RESULTS_FILE = "/results/application-crud-report.json"
docker compose -f .\load-test\docker-compose.yaml run --rm load-test
```

The scenario runs each architecture independently and writes the combined report to `load-test/results/application-crud-report.json`. The report contains operation-level request counts, status codes, errors, p50/p95 latency, and first-error details, so failures can be attributed to a specific service/container rather than only to an architecture-wide URL.

To test tenant B instead, replace the tenant A namespace and port-forwards with `docusage-tenant-b` and use another set of local ports.

Stop a running test with `Ctrl+C`; there is no persistent load-test container to stop.
