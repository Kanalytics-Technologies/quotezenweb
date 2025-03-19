# ## 📌 POST /auth/signup
# resource "aws_api_gateway_resource" "signup_quotezen" {
#   rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
#   parent_id   = aws_api_gateway_resource.auth_quotezen.id
#   path_part   = "signup"
# }
#
# resource "aws_api_gateway_method" "signup_method_quotezen" {
#   rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id   = aws_api_gateway_resource.signup_quotezen.id
#   http_method   = "POST"
#   authorization = "NONE"
# }
#
# resource "aws_api_gateway_integration" "signup_integration_quotezen" {
#   rest_api_id             = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id             = aws_api_gateway_resource.signup_quotezen.id
#   http_method             = aws_api_gateway_method.signup_method_quotezen.http_method
#   integration_http_method = "POST"
#   type                    = "AWS_PROXY"
#   uri                     = aws_lambda_function.signup_lambda_quotezen.invoke_arn
# }
#
# # 🔹 OPTIONS para permitir CORS en /auth/signup
# resource "aws_api_gateway_method" "signup_options_quotezen" {
#   rest_api_id   = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id   = aws_api_gateway_resource.signup_quotezen.id
#   http_method   = "OPTIONS"
#   authorization = "NONE"
# }
#
# resource "aws_api_gateway_integration" "signup_options_integration_quotezen" {
#   rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id = aws_api_gateway_resource.signup_quotezen.id
#   http_method = aws_api_gateway_method.signup_options_quotezen.http_method
#   type        = "MOCK"
#
#   request_templates = {
#     "application/json" = <<EOF
# {
#   "statusCode": 200
# }
# EOF
#   }
# }
#
# resource "aws_api_gateway_method_response" "signup_options_response_quotezen" {
#   rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id = aws_api_gateway_resource.signup_quotezen.id
#   http_method = aws_api_gateway_method.signup_options_quotezen.http_method
#   status_code = "200"
#
#   response_parameters = {
#     "method.response.header.Access-Control-Allow-Origin"  = true
#     "method.response.header.Access-Control-Allow-Methods" = true
#     "method.response.header.Access-Control-Allow-Headers" = true
#   }
# }
#
# resource "aws_api_gateway_integration_response" "signup_options_integration_response_quotezen" {
#   rest_api_id = aws_api_gateway_rest_api.api_auth_quotezen.id
#   resource_id = aws_api_gateway_resource.signup_quotezen.id
#   http_method = aws_api_gateway_method.signup_options_quotezen.http_method
#   status_code = "200"
#
#   response_parameters = {
#     "method.response.header.Access-Control-Allow-Origin"  = "'*'"
#     "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
#     "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
#   }
#
#   depends_on = [aws_api_gateway_integration.signup_options_integration_quotezen]
# }