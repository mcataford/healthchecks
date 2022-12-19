resource "aws_iam_role" "lambda_role" {
  name               = "${local.service_longname}_lambda-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = local.common_tags

}

resource "aws_lambda_function" "lambda_func" {
  function_name = "${local.service_longname}_function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "src.base.handler"
  runtime       = "python3.8"

  s3_bucket = var.artifacts_bucket_name
  s3_key    = var.lambda_archive_name

  tags = local.common_tags
}

resource "aws_api_gateway_rest_api" "gateway" {
  name        = "${local.service_longname}_gateway"
  description = "Lambda Boilerplate"

  tags = local.common_tags

}

resource "aws_api_gateway_resource" "lambda_proxy" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  parent_id   = aws_api_gateway_rest_api.gateway.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "lambda_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.gateway.id
  resource_id   = aws_api_gateway_resource.lambda_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.gateway.id
  resource_id = aws_api_gateway_resource.lambda_proxy.id
  http_method = aws_api_gateway_method.lambda_proxy.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_func.invoke_arn

}

resource "aws_api_gateway_deployment" "lambda" {
  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  rest_api_id = aws_api_gateway_rest_api.gateway.id
  stage_name  = "test"

}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_func.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.gateway.execution_arn}/*/*"

}

resource "aws_dynamodb_table" "ddb" {
  name           = "healthchecks"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "event_id"
  range_key      = "service_name"

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "service_name"
    type = "S"
  }

  ttl {
    enabled = true
    attribute_name = "ttl"
  }
}

output "base_url" {
  value = aws_api_gateway_deployment.lambda.invoke_url
}
