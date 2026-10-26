# Linknest AWS Terraform sandbox

This root is independent of `infra/gcp/sandbox` and uses local state.

## Scope

- Reuse an existing ECR image by digest, existing VPC/public subnet, task roles and Secrets Manager reference.
- Manage only the named sandbox cluster, ECS service/task definition, security group/HTTPS egress rule. The existing log group is referenced, not managed.
- One Linux x86_64 Fargate task, 0.5 vCPU and 2 GiB memory.
- No inbound security-group rules. Test the HTTP API on localhost through authenticated ECS Exec.
- A public IPv4 address provides outbound connectivity without adding a NAT gateway. It does not open inbound ports.
- Existing ALB, existing ECS service and `/ecs/linknest-classifier` log group are outside this state and must remain untouched.
- A first attempt created the empty `/ecs/linknest-tf-sandbox` log group. The lab caller lacks log-group tag/read/delete permissions; it was removed from this state and requires separate cleanup by an authorized administrator. Do not mistake state removal for cloud deletion.

## Configuration

Copy `terraform.tfvars.example` to the ignored `terraform.tfvars`, and supply verified references for your own account. Never supply the actual API key value. AWS credentials come from the AWS SDK credential chain, not Terraform files.

The reused roles retain their existing privileges; this lab neither grants new IAM permissions nor represents a production least-privilege design. The execution role must be able to fetch the referenced secret. The task role and caller need ECS Exec/SSM permissions. If an operation is denied, diagnose it instead of attaching broad policies.

## Workflow

```bash
terraform init
terraform fmt -check
terraform validate
terraform plan -out=tfplan
# Review resource scope and costs first; applying a saved plan skips confirmation.
terraform apply tfplan
```

After readiness, use ECS Exec to test `/health` and `/classify` inside the container. Do not expose or print SERVICE_API_KEY. Then check logs and run a deployment-after plan.

## Cleanup

```bash
terraform plan -destroy -out=destroy.tfplan
# Review that ONLY this sandbox is removed, then explicitly execute:
terraform apply destroy.tfplan
```

Preserve original resources. Local state and saved plans must remain private and must not be committed. Keep `.terraform.lock.hcl`. Fargate, public IPv4, image storage and logs can incur charges; no autoscaling or load balancer is introduced here. Do not leave failed tasks repeatedly restarting.
