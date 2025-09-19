# Cloud Run Deployment

## Setup

### 1. GitHub Secrets
Add these secrets to your GitHub repository:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account JSON key (base64 encoded)

### 2. Service Account Permissions
Your service account needs these roles:
- Cloud Run Admin
- Artifact Registry Admin
- Storage Admin
- Service Account User

### 3. Enable APIs
```bash
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Usage

### GitHub Actions
1. Go to Actions tab in your repository
2. Select "Deploy Cloud Run" workflow
3. Click "Run workflow"
4. Choose action: `create` or `destroy`

### GitLab CI
1. Set pipeline variables: `ACTION=create` or `ACTION=destroy`
2. Run pipeline manually

## Manual Terraform

```bash
cd terraform
terraform init
terraform plan -var="project_id=YOUR_PROJECT" -var="region=us-central1"
terraform apply -var="project_id=YOUR_PROJECT" -var="region=us-central1"
```

## State Management
Terraform state is stored in GCS bucket: `maf-policy-bot-terraform-state`