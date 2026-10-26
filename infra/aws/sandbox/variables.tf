variable "expected_account_id" {
  description = "Account verified with STS; prevents targeting another account."
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.expected_account_id))
    error_message = "Provide the verified 12-digit AWS account ID."
  }
}

variable "vpc_id" {
  description = "Existing VPC with a verified internet gateway route."
  type        = string
}

variable "subnet_id" {
  description = "Existing public subnet; no subnet or NAT is created."
  type        = string
}

variable "image_uri" {
  description = "Existing Linux amd64 ECR image pinned by digest."
  type        = string
  validation {
    condition     = can(regex("@sha256:[a-f0-9]{64}$", var.image_uri))
    error_message = "Use a fixed image digest, not a mutable tag."
  }
}

variable "execution_role_arn" {
  description = "Existing role used by ECS to pull images, inject secrets and write logs."
  type        = string
}

variable "task_role_arn" {
  description = "Existing task role with the SSM Messages permissions required by ECS Exec."
  type        = string
}

variable "api_key_secret_arn" {
  description = "Existing Secrets Manager reference; do not supply the secret value."
  type        = string
}
