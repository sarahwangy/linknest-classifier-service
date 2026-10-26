# Only this new service is managed here. Existing shared resources are references.
resource "google_cloud_run_v2_service" "classifier_sandbox" {
  name     = "linknest-classifier-tf-sandbox"
  project  = "linknest-gcp-lab"
  location = "australia-southeast1"

  # Keep IAM authentication enabled even though the URL accepts internet traffic.
  ingress              = "INGRESS_TRAFFIC_ALL"
  invoker_iam_disabled = false

  # This disposable sandbox may be removed after reviewing a destroy plan.
  deletion_protection = false

  labels = {
    environment = "sandbox"
    managed-by  = "terraform"
  }

  # Match the original service-level cap, separate from the revision cap below.
  scaling {
    min_instance_count = 0
    max_instance_count = 1
  }

  template {
    service_account                  = "linknest-run@linknest-gcp-lab.iam.gserviceaccount.com"
    execution_environment            = "EXECUTION_ENVIRONMENT_GEN2"
    timeout                          = "300s"
    max_instance_request_concurrency = 1
    session_affinity                 = false

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    containers {
      name  = "classifier"
      image = "australia-southeast1-docker.pkg.dev/linknest-gcp-lab/cloud-run-source-deploy/linknest-classifier-service/linknest-classifier-service@sha256:5137c6f11c89fd4762a5bd2f3884cbd358a774c062007918122ac4b85091eed9"

      ports {
        name           = "http1"
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
        cpu_idle          = true
        startup_cpu_boost = true
      }

      # Reference the secret version; do not read its value into Terraform state.
      env {
        name = "SERVICE_API_KEY"
        value_source {
          secret_key_ref {
            secret  = "linknest-service-api-key"
            version = "1"
          }
        }
      }

      volume_mounts {
        name       = "model"
        mount_path = "/app/model"
      }

      # Preserve the original startup probe; real model readiness needs /health.
      startup_probe {
        timeout_seconds   = 240
        period_seconds    = 240
        failure_threshold = 1
        tcp_socket {
          port = 8000
        }
      }
    }

    volumes {
      name = "model"
      gcs {
        bucket    = "linknest-gcp-lab-model-360990832014"
        read_only = true
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
