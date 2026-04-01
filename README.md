# AI SRE Watchdog - Beginner Workshop Guide

Welcome to this workshop. This project shows the full path for a Python-based AI security log analysis system (log generator + log receiver): local run, Docker containerization, and deployment to Google Kubernetes Engine (GKE).

No prior experience is required. Follow the steps in order and copy/paste the commands.

---

## Pre-Workshop Setup (Required)
If this is a fresh machine, install these tools first:
1. [Python 3.10+](https://www.python.org/downloads/)
	- On Windows, make sure to check Add python.exe to PATH during installation.
2. [Docker Desktop](https://www.docker.com/products/docker-desktop/)
	- Start Docker Desktop after installation and keep it running.
3. Code editor (recommended): [Visual Studio Code](https://code.visualstudio.com/)
4. GCP account and project (required)
	- Google Cloud sign-up/free tier: [https://cloud.google.com/free](https://cloud.google.com/free)
	- Google Account sign-up: [https://accounts.google.com/signup](https://accounts.google.com/signup)
	- Create a GCP project: [https://console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate)
	- Enable billing: [https://console.cloud.google.com/billing](https://console.cloud.google.com/billing)
5. [Google Cloud CLI (gcloud)](https://cloud.google.com/sdk/docs/install)

Important:
- Complete GCP account/project/billing and gcloud setup before class. Otherwise, Artifact Registry, GKE auth, and image push steps will fail.
- kubectl is usually installed automatically with Docker Desktop.

---

## Step 1: Download the Workshop Repository (git clone)
For Windows:
1. Open PowerShell (Win + X, then select Windows PowerShell or Terminal).
2. Move to your preferred folder (example: Desktop):

```powershell
cd $HOME\Desktop
```

3. Clone the repository:

```powershell
git clone https://github.com/TJY-6666/AI_SRE_REPO.git
```

4. Enter the workshop folder:

```powershell
cd <repo-name>\dryrun_folder
```

5. If the instructor updates the repo later, run this from the repository root:

```powershell
git pull
```

Tip: Keep your working directory at dryrun_folder during the workshop.

---

## Phase 1: Local Run with Python
Before Docker and cloud deployment, run everything locally with Python first. Use a virtual environment (venv) to keep dependencies isolated.

### 1. Run the Log Receiver

```powershell
# 1) Enter the receiver folder
cd log_receiver_folder

# 2) Create a virtual environment
python -m venv venv

# 3) Activate the virtual environment
venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# 4) Install dependencies
pip install -r requirements.txt

# 5) Start the app
python app.py
```

Open [http://localhost:5000/](http://localhost:5000/) in your browser.

To stop the app, press Ctrl + C, then return to the root folder:

```powershell
cd ..
```

### 2. Optional: Run the Local Attack Log Generator

```powershell
cd log_generator_folder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

It sends simulated attack logs every 15 seconds.
Stop with Ctrl + C, then run:

```powershell
cd ..
```

---

## Phase 2: Docker Containerization
To avoid environment mismatch across machines, package the app and dependencies into Docker images.

### 1. Build Images

```powershell
# Build receiver image
docker build -t log_receiver_image:v1 .\log_receiver_folder\

# Build generator image
docker build -t log_generator_image:v1 .\log_generator_folder\
```

### 2. Create a Docker Network

```powershell
docker network create sre-network
```

### 3. Run Containers
Start receiver:

```powershell
docker run -d --name log_receiver_container --network sre-network --network-alias log-receiver -p 5000:5000 log_receiver_image:v1
```

Start generator:

```powershell
docker run -d --name log_generator_container --network sre-network -e SERVICE_B_URL="http://log-receiver:5000/logs" log_generator_image:v1
```

Refresh [http://localhost:5000/](http://localhost:5000/).

Stop containers when needed:

```powershell
docker stop log_receiver_container
docker stop log_generator_container
```

---

## Optional Path (No Docker Desktop): Cloud Build
If you cannot install Docker Desktop, you can skip Phase 2 and build images directly in Google Cloud Build.

Prerequisite: Create your Artifact Registry repository first.

```powershell
# Build and push receiver image in cloud
gcloud builds submit --tag us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_receiver_image:v1 .\log_receiver_folder

# Build and push generator image in cloud
gcloud builds submit --tag us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_generator_image:v1 .\log_generator_folder
```

If you use this path, you can skip Phase 3 Step 2 and Step 3.

---

## Phase 3: Deploy to Google Kubernetes Engine (GKE)

### 1. Create Cloud Resources
Open [Google Cloud Console](https://console.cloud.google.com/) and create:
- Artifact Registry repository
- GKE Autopilot cluster

### 2. Configure Docker Auth for Artifact Registry

```powershell
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 3. Tag and Push Images

```powershell
# Tag generator image
docker tag log_generator_image:v1 us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_generator_image:v1

# Tag receiver image
docker tag log_receiver_image:v1 us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_receiver_image:v1

# Push receiver image
docker push us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_receiver_image:v1

# Push generator image
docker push us-central1-docker.pkg.dev/<your-gcp-project-id>/<your-artifact-registry-repo>/log_generator_image:v1
```

### 4. Get GKE Credentials

```powershell
gcloud container clusters get-credentials docker-dryrun-cluster --region us-central1 --project <your-gcp-project-id>
```

### 5. Apply Kubernetes Manifests

```powershell
kubectl apply -f k8s/
kubectl get pods -w
```

Wait until pods are Running, then stop watching with Ctrl + C.

### 6. Access the App via Port Forward

```powershell
kubectl port-forward svc/log-receiver 5000:5000
```

Open [http://localhost:5000/](http://localhost:5000/) again.

You have now completed a full path from local Python app to containerized microservices on Kubernetes.
