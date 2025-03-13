# 🔹 Definir API Gateway
resource "aws_api_gateway_rest_api" "api_auth_quotezen" {
  name        = "auth-api-${var.project_name}-${var.environment}"
  description = "API de autenticación con Cognito y DynamoDB"
}

# 🔹 Definir Cognito Authorizer
resource "aws_api_gateway_authorizer" "cognito_auth_quotezen" {
  name          = "cognito-auth-${var.project_name}-${var.environment}"
  type          = "COGNITO_USER_POOLS"
  rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
  provider_arns = [aws_cognito_user_pool.user_pool_quotezen.arn]
}

### 📌 AUTH RESOURCE (/auth)
resource "aws_api_gateway_resource" "auth_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
  parent_id   = aws_api_gateway_rest_api.api_auth_quotezen.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_deployment" "auth_api_deployment_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.api_auth_quotezen))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.signup_method_quotezen,
    aws_api_gateway_method.signup_options_quotezen,
    aws_api_gateway_integration.signup_integration_quotezen,
    aws_api_gateway_method.confirm_account_method_quotezen,
    aws_api_gateway_method.confirm_account_options_quotezen,
    aws_api_gateway_integration.confirm_account_integration_quotezen
  ]
}


resource "aws_api_gateway_stage" "auth_api_stage_quotezen" {
  deployment_id = aws_api_gateway_deployment.auth_api_deployment_quotezen.id
  rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
  stage_name    = var.environment
}