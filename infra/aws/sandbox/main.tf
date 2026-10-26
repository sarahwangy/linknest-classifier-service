locals {
  name      = "linknest-tf-sandbox"
  log_group = "/ecs/linknest-classifier"
  tags = {
    Environment = "sandbox"
    ManagedBy   = "terraform"
  }
}

# Existing VPC, subnets, image, roles and secret remain outside this state.
resource "aws_security_group" "classifier" {
  name        = local.name
  description = "No inbound access; test through ECS Exec"
  vpc_id      = var.vpc_id
  ingress     = []
  tags        = local.tags
}

resource "aws_vpc_security_group_egress_rule" "https" {
  security_group_id = aws_security_group.classifier.id
  description       = "HTTPS for image pull, secrets, logs and SSM Messages"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}

resource "aws_ecs_cluster" "sandbox" {
  name = local.name
  tags = local.tags
}

resource "aws_ecs_task_definition" "classifier" {
  family                   = local.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "2048"
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "classifier"
      image     = var.image_uri
      essential = true
      portMappings = [{
        containerPort = 8000
        protocol      = "tcp"
      }]
      linuxParameters = { initProcessEnabled = true }
      secrets = [{
        name      = "SERVICE_API_KEY"
        valueFrom = var.api_key_secret_arn
      }]
      healthCheck = {
        command = [
          "CMD-SHELL",
          "python -c \"import json,urllib.request; r=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=4)); assert r.get('model_loaded') is True\""
        ]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 300
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = local.log_group
          "awslogs-region"        = "ap-southeast-2"
          "awslogs-stream-prefix" = local.name
        }
      }
    }
  ])
  tags = local.tags
}

resource "aws_ecs_service" "classifier" {
  name                               = local.name
  cluster                            = aws_ecs_cluster.sandbox.id
  task_definition                    = aws_ecs_task_definition.classifier.arn
  launch_type                        = "FARGATE"
  platform_version                   = "1.4.0"
  desired_count                      = 1
  enable_execute_command             = true
  wait_for_steady_state              = true
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100
  availability_zone_rebalancing      = "DISABLED"

  deployment_circuit_breaker {
    enable   = true
    rollback = false
  }

  network_configuration {
    subnets          = [var.subnet_id]
    security_groups  = [aws_security_group.classifier.id]
    assign_public_ip = true
  }

  # Do not start tasks before the HTTPS egress rule is ready.
  depends_on = [aws_vpc_security_group_egress_rule.https]
  timeouts {
    create = "15m"
    update = "15m"
    delete = "15m"
  }
  tags = local.tags
}
