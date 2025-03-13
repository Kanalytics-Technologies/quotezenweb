# 🔹 IAM Role para los Lambdas de autenticación
resource "aws_iam_role" "lambda_auth_role_quotezen" {
  name = "lambda-auth-role-${var.project_name}-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# 🔹 IAM Policy para permitir logs en CloudWatch
resource "aws_iam_policy" "lambda_logging_policy_quotezen" {
  name        = "lambda-logging-policy-${var.project_name}-${var.environment}"
  description = "Permisos para escribir logs en CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/*"
      }
    ]
  })
}

# 🔹 Adjuntar política de logs al rol del Lambda
resource "aws_iam_role_policy_attachment" "lambda_logs_attachment_quotezen" {
  role       = aws_iam_role.lambda_auth_role_quotezen.name
  policy_arn = aws_iam_policy.lambda_logging_policy_quotezen.arn
}

# 🔹 IAM Policy para permitir acceso a Cognito
resource "aws_iam_policy" "lambda_cognito_policy_quotezen" {
  name        = "lambda-cognito-policy-${var.project_name}-${var.environment}"
  description = "Permite a los Lambdas interactuar con Cognito"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "cognito-idp:AdminCreateUser",
          "cognito-idp:AdminInitiateAuth",
          "cognito-idp:AdminSetUserPassword",
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminUpdateUserAttributes",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:SignUp",
          "cognito-idp:ConfirmSignUp",
          "cognito-idp:ForgotPassword",
          "cognito-idp:ConfirmForgotPassword",
          "cognito-idp:InitiateAuth"
        ]
        Resource = aws_cognito_user_pool.user_pool_quotezen.arn
      }
    ]
  })
}

# 🔹 Adjuntar política de Cognito al rol del Lambda
resource "aws_iam_role_policy_attachment" "lambda_cognito_attachment_quotezen" {
  role       = aws_iam_role.lambda_auth_role_quotezen.name
  policy_arn = aws_iam_policy.lambda_cognito_policy_quotezen.arn
}

# 🔹 IAM Policy para permitir acceso a DynamoDB
resource "aws_iam_policy" "lambda_dynamo_policy_quotezen" {
  name        = "lambda-dynamo-policy-${var.project_name}-${var.environment}"
  description = "Permite a los Lambdas leer y escribir en la tabla de usuarios en DynamoDB"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.users_table_quotezen.arn
      }
    ]
  })
}

# 🔹 Adjuntar política de DynamoDB al rol del Lambda
resource "aws_iam_role_policy_attachment" "lambda_dynamo_attachment_quotezen" {
  role       = aws_iam_role.lambda_auth_role_quotezen.name
  policy_arn = aws_iam_policy.lambda_dynamo_policy_quotezen.arn
}