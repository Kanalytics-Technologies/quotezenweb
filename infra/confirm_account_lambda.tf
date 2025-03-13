data "archive_file" "lambda_package_confirm_account_quotezen" {
  type        = "zip"
  source_dir  = "${path.module}/../lambdas/confirm_account"
  output_path = "${path.module}/modules/lambda/confirm_account.zip"
}

resource "aws_lambda_function" "confirm_account_lambda_quotezen" {
  function_name = "confirm_account-${var.project_name}-${var.environment}"
  role          = aws_iam_role.lambda_auth_role_quotezen.arn
  handler       = "main.handler"
  runtime       = "python3.9"
  timeout          = 10
  memory_size      = 256
  filename         = data.archive_file.lambda_package_confirm_account_quotezen.output_path
  source_code_hash = data.archive_file.lambda_package_confirm_account_quotezen.output_base64sha256

  environment {
    variables = {
      ENVIRONMENT = var.environment
      DYNAMODB_TABLE = aws_dynamodb_table.users_table_quotezen.name
      COGNITO_CLIENT_ID = aws_cognito_user_pool_client.user_pool_client_quotezen.id
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.user_pool_quotezen.id
      REGION = var.aws_region
    }
  }
}

resource "aws_lambda_permission" "allow_api_gateway_confirm_account_quotezen" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.confirm_account_lambda_quotezen.arn
  principal     = "apigateway.amazonaws.com"
}

# Logs for Lambda
resource "aws_cloudwatch_log_group" "lambda_log_group_confirm_account" {
  name              = "/aws/lambda/${aws_lambda_function.confirm_account_lambda_quotezen.function_name}"
  retention_in_days = 30
}