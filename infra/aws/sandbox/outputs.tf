output "cluster_name" {
  value = aws_ecs_cluster.sandbox.name
}

output "service_name" {
  value = aws_ecs_service.classifier.name
}

output "log_group_name" {
  value = local.log_group
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.classifier.arn
}
