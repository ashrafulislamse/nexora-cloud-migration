variable "primary_region" {
  description = "Primary AWS region (Malaysia)"
  type        = string
  default     = "ap-southeast-5"
}

variable "recovery_region" {
  description = "Recovery AWS region (Jakarta)"
  type        = string
  default     = "ap-southeast-3"
}

variable "primary_vpc_cidr" {
  description = "CIDR block for the primary VPC"
  type        = string
  default     = "10.40.0.0/16"
}

variable "recovery_vpc_cidr" {
  description = "CIDR block for the recovery VPC"
  type        = string
  default     = "10.50.0.0/16"
}

variable "app_image" {
  description = "Container image for the storefront service. The compute module injects a command so this placeholder serves /health and the k6 API stub routes on app_port; replace with the real storefront image when built."
  type        = string
  default     = "public.ecr.aws/nginx/nginx:alpine"
}

variable "app_port" {
  description = "Port the storefront container listens on"
  type        = number
  default     = 8080
}

variable "min_tasks" {
  description = "Minimum Fargate tasks for the storefront service"
  type        = number
  default     = 2
}

variable "max_tasks" {
  description = "Maximum Fargate tasks under the autoscaling policy"
  type        = number
  default     = 20
}

variable "alarm_email" {
  description = "Email subscribed to the operations alarm topic"
  type        = string
  default     = "ops@nexora.example"
}
