# Credentials come from the AWS SDK credential chain, never from this file.
provider "aws" {
  region              = "ap-southeast-2"
  allowed_account_ids = [var.expected_account_id]
}
