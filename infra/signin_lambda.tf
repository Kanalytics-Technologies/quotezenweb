# data "archive_file" "lambda_package_signin_quotezen" {
#   type        = "zip"
#   source_dir  = "${path.module}/../lambdas/signin"
#   output_path = "${path.module}/modules/lambda/signin.zip"
# }
#
# resource "aws_lambda_function" "signin_lambda_quotezen" {
#   function_name = "signin-${var.project_name}-${var.environment}"
#   role          = aws_iam_role.lambda_auth_role_quotezen.arn
#   handler       = "main.handler"
#   runtime       = "python3.9"
#   timeout          = 10
#   memory_size      = 256
#   filename         = data.archive_file.lambda_package_signin_quotezen.output_path
#   source_code_hash = data.archive_file.lambda_package_signin_quotezen.output_base64sha256
#
#   environment {
#     variables = {
#       ENVIRONMENT = var.environment
#       DYNAMODB_TABLE = aws_dynamodb_table.users_table_quotezen.name
#       COGNITO_CLIENT_ID = aws_cognito_user_pool_client.user_pool_client_quotezen.id
#       COGNITO_USER_POOL_ID = aws_cognito_user_pool.user_pool_quotezen.id
#       REGION = var.aws_region
#     }
#   }
# }
#
# resource "aws_lambda_permission" "allow_api_gateway_signin_quotezen" {
#   statement_id  = "AllowExecutionFromAPIGateway"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.signin_lambda_quotezen.arn
#   principal     = "apigateway.amazonaws.com"
# }
#
# # Logs for Lambda
# resource "aws_cloudwatch_log_group" "lambda_log_group_signin" {
#   name              = "/aws/lambda/${aws_lambda_function.signin_lambda_quotezen.function_name}"
#   retention_in_days = 30
# }