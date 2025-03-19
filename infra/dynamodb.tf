# resource "aws_dynamodb_table" "users_table_quotezen" {
#   name         = "users-${var.project_name}-${var.environment}"
#   billing_mode = "PAY_PER_REQUEST"
#
#   attribute {
#     name = "Email"
#     type = "S"
#   }
#
#   attribute {
#     name = "Role"
#     type = "S"
#   }
#
#   attribute {
#     name = "Company"
#     type = "S"
#   }
#
#   hash_key = "Email"  # 📌 Clave primaria: el email
#
#   # 📌 Global Secondary Index for search by Role
#   global_secondary_index {
#     name               = "RoleIndex"
#     hash_key           = "Role"
#     projection_type    = "ALL"
#   }
#
#   # 📌 Global Secondary Index for search by Company
#   global_secondary_index {
#     name               = "CompanyIndex"
#     hash_key           = "Company"
#     projection_type    = "ALL"
#   }
# }