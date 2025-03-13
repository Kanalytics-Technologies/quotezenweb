variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev or prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project Name"
  type        = string
  default     = "quotezenweb"
}

variable "allowed_origin" {
  description = "CORS Allowed Origins"
  type        = string
  default     = "http://localhost:3000"
}