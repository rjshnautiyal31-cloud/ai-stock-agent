# Alpha Vantage Real-time Stock Agent & GitOps Ecosystem

This repository hosts a production-hardened, multi-layered, declarative GitOps deployment architecture and runtime engine for an **Alpha Vantage Real-time Stock Agent**. 

The system leverages **Google Cloud Platform (GCP)**, **Model Context Protocol (MCP)**, **Workload Identity Federation (OIDC)**, and **Vertex AI Agent Builder (Gemini Enterprise Apps)** to deliver a highly secure, credential-free, code-driven cognitive financial assistant.

---

## 🌌 Architectural Overview

The architecture is divided into three distinct, decoupled, and securely bound layers, fully automated in GitOps:

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 GITHUB GITOPS RUNNER                   │
                  │  Authenticates securely via Workload Identity (OIDC)   │
                  └──────────────────────────┬─────────────────────────────┘
                                             │ [Assumes Deployer SA Identity]
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               GOOGLE CLOUD PROJECT (GCP)                               │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  ┌─────────────────────────────┐           ┌────────────────────────────────────────┐  │
│  │   SECRET MANAGER (GCP)      │           │         ARTIFACT REGISTRY (GCP)        │  │
│  │  Stores:                    │           │  Holds: alphavantage-agent-repo        │  │
│  │  - alpha-vantage-api-key    │           │  Container image built on commit pushes│  │
│  │             ▲               │           └───────────────────┬────────────────────┘  │
│  └─────────────┼───────────────┘                               │                       │
│                │ [accesses key]                                │ [deploys image]       │
│  ┌─────────────┴───────────────┐                               ▼                       │
│  │     CLOUD RUN V2 SERVICE    │           ┌────────────────────────────────────────┐  │
│  │  Runs: Python FastMCP       │◄──────────┤       VERTEX AI COGNITIVE AGENT        │  │
│  │  - SSE on: /sse             │  [REST    │  - Gemini Enterprise (GE) App          │  │
│  │  - REST on: /quote          │   Query]  │  - Dialogflow CX Agent Runtime         │  │
│  │  Identity: mcp-runner SA    │           │  - Declaratively linked via Playbooks  │  │
│  └─────────────────────────────┘           └────────────────────────────────────────┘  │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Bootstrap Infrastructure Layer (`terraform/bootstrap/`)**
   * Configures a remote state Google Cloud Storage (GCS) bucket.
   * Provisions a secure **Workload Identity Pool** and **OIDC Provider** mapped to GitHub Actions, enabling keyless deployments.
   * Creates a dedicated `github-actions-deployer` service account with elevated project-level privileges (including Artifact Registry, Service Account, and Dialogflow Admin roles) to build and deploy resources.
   * Provisions the private **Artifact Registry Repository** (`alphavantage-agent-repo`) to store compiled Docker images.

2. **Application Infrastructure Layer (`terraform/app/`)**
   * Configures GCP Secret Manager to hold the Alpha Vantage API key securely.
   * Deploys a **Google Cloud Run v2 service** running the MCP Application over HTTP/SSE, with local host origin protections disabled for secure Cloud Run ingress.
   * Provisions the **Discovery Engine Data Store** and **Chat Engine (GE App)** using the advanced **`google-beta` 6.x** provider.
   * Declaratively binds the `/quote` REST endpoint on your live Cloud Run server to the GE App's auto-created Agent Runtime using **`google_dialogflow_cx_tool`** and **`google_dialogflow_cx_playbook`**.

3. **Software Engine Layer (`src/`)**
   * **GCPSecretManagerClient (`src/mcp_server/secrets.py`)**: An OOP-based secrets accessor that implicitly resolves project credentials via Google Application Default Credentials (ADC) to access GCP Secret Manager.
   * **AlphaVantageToolKit (`src/mcp_server/toolkit.py`)**: A type-safe API wrapper executing the `GLOBAL_QUOTE` function to extract stock metrics with strict exception handling and logging.
   * **MCPServerApplication (`src/mcp_server/server.py`)**: An ASGI Starlette application factory spinning up FastMCP over Server-Sent Events (SSE on `/sse`) and standard REST (on `/quote`) over port 8080.
   * **AlphaVantageAgentRuntime (`src/agent_runtime/agent.py`)**: A code-first local test runner utilizing Vertex AI ADK `LlmAgent`, `InMemorySessionService`, and `Runner` to connect dynamically to the SSE-based Cloud Run server and execute user prompts.

---

## 📁 Repository Scaffolding

```
.
├── .github/
│   └── workflows/
│       └── gitops.yml                  # Task 3: CI/CD GitOps Pipeline with WIF, builds & deploys
├── src/
│   ├── agent_runtime/
│   │   ├── agent.py                    # Task 3: OOP Vertex AI ADK Grounded LlmAgent Client
│   │   └── server.py                   # REST API wrapper exposing POST /chat (Optional)
│   └── mcp_server/
│       ├── secrets.py                  # Task 2: OOP Secret Manager client with ADC project lookup
│       ├── server.py                   # Task 2: MCPServerApplication Starlette/SSE + REST factory
│       └── toolkit.py                  # Task 2: OOP Typed AlphaVantageToolKit Client
├── terraform/
│   ├── app/
│   │   ├── agent.tf                    # Task 3: Declarative google_discovery_engine_chat_engine & Playbook
│   │   ├── mcp.tf                      # Task 2: Secret, runner SA, secret IAM, Cloud Run, invoker IAM
│   │   ├── outputs.tf                  # Task 2: Cloud Run service URL output, GE App IDs
│   │   ├── providers.tf                # Task 2: Provider config + GCS backend + 6.x billing overrides
│   │   └── variables.tf                # Task 2/3: Workspace inputs, including github_repository
│   └── bootstrap/
│       ├── main.tf                     # Task 1: GCS backend, WIF Pool + Provider, Artifact Registry, Deployer SA, elevated IAM
│       ├── outputs.tf                  # Task 1: GCS bucket, WIF provider name, SA email outputs
│       ├── providers.tf                # Task 1: Provider config
│       └── variables.tf                # Task 1: Bootstrap inputs
├── Dockerfile                           # Production multi-stage build container
├── requirements.txt                     # Package dependencies
└── run_test.py                         # Test harness for local E2E ADK agent
```

---

## 🛠️ Step-by-Step Deployment & Usage

### Prerequisites
* [Terraform v1.15.8+](https://www.terraform.io/)
* [Docker v29.0.0+](https://www.docker.com/)
* [Python 3.11+](https://www.python.org/)
* [gcloud SDK](https://cloud.google.com/sdk) authenticated with active credentials:
  ```bash
  gcloud auth application-default login
  gcloud config set project fabled-ruler-363118
  gcloud auth application-default set-quota-project fabled-ruler-363118
  ```

---

### Step 1: Deploy the Bootstrap Layer (Local Manual Run)
First, provision the secure OIDC, remote GCS state bucket, and the Artifact Registry using your active user credentials.

```bash
cd terraform/bootstrap
terraform init
terraform apply -var="github_repository=rjshnautiyal31-cloud/ai-stock-agent" -auto-approve
cd ../..
```

---

### Step 2: Configure the Secret Value on GCP
Add your **actual, valid Alpha Vantage API key** directly to the generated GCP Secret Manager placeholder:

```bash
echo -n "YOUR_ACTUAL_ALPHA_VANTAGE_KEY" | gcloud secrets versions add alpha-vantage-api-key --data-file=-
```
*(This version is secure, is kept out of Git, and will never be overwritten by future Terraform runs).*

---

### Step 3: GitOps Automated Application Deployment
Once the Bootstrap Layer is deployed, you do not need to apply `terraform/app` manually. 

Simply **push your code to your GitHub repository** (`rjshnautiyal31-cloud/ai-stock-agent`) to trigger the `.github/workflows/gitops.yml` pipeline:

```bash
git add .
git commit -m "feat: complete automated stock agent deployment"
git push origin main
```

The pipeline will:
1. Validate HCL syntax and check formatting (`terraform fmt -check`).
2. Authenticate keylessly to GCP via WIF OIDC.
3. Build the custom multi-stage Docker image and push it to GCP Artifact Registry.
4. Run `terraform apply` to deploy your Cloud Run MCP service and Vertex AI GE App.

---

### Step 4: The 10-Second Post-Deployment Adjustment (GCP Console)
Because the GCP API *forces* us to link a Data Store to the Chat Engine, Google automatically routes conversational traffic to the empty Data Store first (throwing `data_store_no_match`). 

To complete the setup, quickly disable the empty search Data Store inside the console:

1. Open the [Dialogflow CX Console](https://dialogflow.cloud.google.com/cx/projects/fabled-ruler-363118/locations/us-central1/agents).
2. Click on your active agent **`alphavantage-stock-agent`**.
3. Under **Build** > **Playbooks**, click on **`StockAnalystSpecialist`**.
4. In the right-side configuration panel, **uncheck/remove the data store connection** `alphavantage-agent-datastore` (ensure only `AlphaVantageTool` is checked under *Tools*).
5. Click **Save**.

Your agent is now permanently stable and focused only on the live stock metrics!

---

### Step 5: Test the Live Cloud Suite

To test the entire integrated platform (Local ADK client handshaking with live Cloud Run MCP server over SSE):

1. **Set the environment variables**:
   ```bash
   # Align project to your active project
   export GOOGLE_CLOUD_PROJECT="fabled-ruler-363118"

   # Instruct httpx to use HTTP/1.1 (prevents HTTP/2 connection pooling conflicts)
   export HTTPX_NO_HTTP2=1

   # Instruct GenAI to use GCP Vertex AI (uses active ADC)
   export GOOGLE_GENAI_USE_VERTEXAI=true
   ```
2. **Execute the integration test**:
   ```bash
   uv run --with mcp --with starlette --with uvicorn --with requests --with google-cloud-secret-manager --with google-auth --with google-adk python run_test.py
   ```

You will see the local ADK client perform the dynamic handshake, connect to your live Cloud Run container over SSE, and print out live, real-time stock-market summaries retrieved dynamically over GCP!

---

## 🔒 Security Hardening Policies

* **Keyless OIDC CI/CD**: No static GCP JSON credentials are ever stored inside GitHub Secrets.
* **Granular IAM binding**: The CI/CD deployer SA possesses administrative rights scoped only to the required resources (Cloud Run, Discovery Engine, Secret Manager, Artifact Registry).
* **Least-Privilege Container Identity**: The `alphavantage-mcp-runner` service account only possesses `roles/secretmanager.secretAccessor` strictly for the Alpha Vantage key secret.
