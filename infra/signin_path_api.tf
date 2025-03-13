## POST /auth/signin
resource "aws_api_gateway_resource" "signin_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
  parent_id   = aws_api_gateway_resource.auth_quotezen.id
  path_part   = "signin"
}

resource "aws_api_gateway_method" "signin_method_quotezen" {
  rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id   = aws_api_gateway_resource.signin_quotezen.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "signin_integration_quotezen" {
  rest_api_id             = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id             = aws_api_gateway_resource.signin_quotezen.id
  http_method             = aws_api_gateway_method.signin_method_quotezen.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.signin_lambda_quotezen.invoke_arn
}

# 🔹 OPTIONS para permitir CORS en /auth/signin
resource "aws_api_gateway_method" "signin_options_quotezen" {
  rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id   = aws_api_gateway_resource.signin_quotezen.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "signin_options_integration_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id = aws_api_gateway_resource.signin_quotezen.id
  http_method = aws_api_gateway_method.signin_options_quotezen.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = <<EOF
{
  "statusCode": 200
}
EOF
  }
}

resource "aws_api_gateway_method_response" "signin_options_response_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id = aws_api_gateway_resource.signin_quotezen.id
  http_method = aws_api_gateway_method.signin_options_quotezen.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Headers" = true
  }
}

resource "aws_api_gateway_integration_response" "signin_options_integration_response_quotezen" {
  rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
  resource_id = aws_api_gateway_resource.signin_quotezen.id
  http_method = aws_api_gateway_method.signin_options_quotezen.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
  }

  depends_on = [aws_api_gateway_integration.signin_options_integration_quotezen]
}