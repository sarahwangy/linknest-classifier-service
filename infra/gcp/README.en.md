# Linknest GCP Terraform Lab

[中文](README.md) | English

This directory contains the Google Cloud Terraform configuration. It is independent of `../aws/sandbox`; each root has its own initialization, provider selection, and state.

## Current status

On 2026-10-26, the first **create → verify → clean up** cycle was completed. The Cloud Run sandbox was created, health/classification/authentication/input-validation checks passed, the post-deployment plan reported no changes, and the sandbox was then deleted. The original `linknest-classifier-service` was retained.

**The configuration remains, but the experimental service has been deleted. Running apply again will recreate it.** For future guided exercises, explain and review each step before executing it.

## Directory and files

The actual Terraform root is [`sandbox/`](sandbox/). Run Terraform commands there.

| File | Purpose |
| --- | --- |
| [sandbox/versions.tf](sandbox/versions.tf) | Terraform and Google Provider version constraints |
| [sandbox/providers.tf](sandbox/providers.tf) | Project `linknest-gcp-lab`, region `australia-southeast1` |
| [sandbox/main.tf](sandbox/main.tf) | New Cloud Run service and runtime configuration |
| [sandbox/.terraform.lock.hcl](sandbox/.terraform.lock.hcl) | Selected provider version; Google 7.46.2 for this run |
| `sandbox/terraform.tfstate` | Local resource records; ignored by Git; do not edit manually |
| `sandbox/.terraform/` | Initialization cache and installed providers; ignored by Git |

The GCP configuration currently contains resource references directly. It does not have the AWS root's `variables.tf`, `terraform.tfvars`, or `smoke_test.py`.

## Managed and reused resources

Only one resource is managed: `google_cloud_run_v2_service.classifier_sandbox`, named `linknest-classifier-tf-sandbox` in Google Cloud.

- Reuse an existing Artifact Registry image pinned by digest; no image is built or uploaded.
- Reuse the `linknest-run` runtime service account, version 1 of `linknest-service-api-key`, and the `linknest-gcp-lab-model-360990832014` model bucket.
- Mount the model bucket read-only at `/app/model`. Inject `SERVICE_API_KEY` by Secret reference, without putting its value in the configuration.
- Container port 8000, 1 vCPU, 2 GiB memory, and a 300-second request timeout.
- Keep Cloud Run IAM invocation checks enabled. An internet-accessible URL does not imply anonymous access.
- Do not create or manage the original service, shared bucket, image repository, Secret, service account, or their IAM grants.

## Local authentication and configuration checks

Terraform is installed at `~/.local/bin/terraform`. From the repository root:

```bash
cd infra/gcp/sandbox
terraform version
terraform fmt -check
terraform init -backend=false
terraform validate
```

`init` installs providers; `validate` checks the configuration. These commands do not deploy Cloud Run. This lab uses local state and has no remote backend configured.

Local Terraform uses Application Default Credentials (ADC). If credentials need to be configured or refreshed:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project linknest-gcp-lab
```

These credentials are for Terraform. The gcloud CLI's login is managed separately with `gcloud auth login`; it also does not read the project setting in `providers.tf`.

## Redeployment workflow

The following commands are instructions for a future rebuild; they do not need to be run now:

```bash
terraform init
terraform plan -out=tfplan
```

Review the plan. Expect only one sandbox service to be added, with no changes or deletions to the original service or shared resources. Confirm the caller has the permissions needed to deploy and reuse dependencies before running:

```bash
terraform apply tfplan
```

Applying a saved plan does not prompt for confirmation again. Generate a new plan for each rebuild rather than reusing an old plan that may no longer be valid.

## Verification and inspection

From Cloud Shell or a local gcloud session authenticated as an authorized caller, retrieve the service's current URL after redeployment:

```bash
gcloud run services describe linknest-classifier-tf-sandbox \
  --project=linknest-gcp-lab \
  --region=australia-southeast1 \
  --format='value(status.url)'
```

This run used individual curl requests in Cloud Shell, rather than the AWS `smoke_test.py` script:

| Test | Observed result |
| --- | --- |
| Valid Google identity, `/health` | 200, `model_loaded: true` |
| Valid Google identity and API key, `/classify` | Successful classification: Technology / 0.4478 |
| Valid Google identity, invalid API key | 401 |
| No Google identity, `/health` | 403 |
| Valid identity and API key, empty title | 422 |

Do not print or commit tokens, API keys, or credential files. Run `terraform plan` after deployment to check for unexpected differences. Inspect saved Terraform resource records with:

```bash
terraform state list
terraform state show google_cloud_run_v2_service.classifier_sandbox
```

State contains saved records. For live status, use Google Cloud Console → Cloud Run → Services. Because the sandbox has been deleted, `state list` should now be empty and `state show` will no longer find that resource.

## Cleanup

Use this only when a recreated sandbox needs to be deleted:

```bash
terraform plan -destroy -out=destroy.tfplan
```

Review the full deletion scope and confirm that only the sandbox will be removed, then run:

```bash
terraform apply destroy.tfplan
terraform state list
```

Keep the shared model bucket, Secret, image, runtime service account, and original service. Do not commit `.terraform/`, state, saved plans, or credentials. Keep the `.tf` configuration and `.terraform.lock.hcl`.

## Detailed lab records

The local learning-notes repository contains the full procedure, screenshots, and discussion:

- [GCP practice TODO (Chinese)](../../../../学习-相关/云与认证/Terraform/GCP-terraform/2026-10-26-Linknest-GCP-Terraform实践TODO.md)
- [GCP lab notes (Chinese)](../../../../学习-相关/云与认证/Terraform/GCP-terraform/2026-10-26-Linknest-GCP-Terraform实操笔记.md)

These links depend on the current multi-repository workspace layout. Cloning the classifier repository alone does not include the learning materials.
