output "primary_vpc_id" {
  description = "Primary VPC id"
  value       = module.networking_primary.vpc_id
}

output "primary_alb_dns" {
  description = "Public DNS name of the primary storefront ALB"
  value       = module.compute_primary.alb_dns_name
}

output "primary_cluster_name" {
  description = "ECS cluster name (primary)"
  value       = module.compute_primary.cluster_name
}

output "primary_service_name" {
  description = "ECS service name (primary)"
  value       = module.compute_primary.service_name
}

output "recovery_vpc_id" {
  description = "Recovery VPC id"
  value       = module.networking_recovery.vpc_id
}

output "recovery_alb_dns" {
  description = "Public DNS name of the recovery storefront ALB"
  value       = module.compute_recovery.alb_dns_name
}

output "aurora_global_cluster_id" {
  description = "Aurora Global Database cluster id shared by both regions"
  value       = module.data_primary.global_cluster_id
}

output "aurora_writer_endpoint" {
  description = "Writer endpoint of the primary Aurora cluster"
  value       = module.data_primary.cluster_endpoint
}

output "aurora_secondary_endpoint" {
  description = "Cluster endpoint of the secondary Aurora cluster (recovery region)"
  value       = module.data_recovery.cluster_endpoint
}
