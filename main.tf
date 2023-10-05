# provider block
provider "aws" {
  profile = "default"
  region  = "us-east-1"

}

# S3 Bucket Definitions
# Destination Bucket for files from BLS 
resource "aws_s3_bucket" "khalid-rearc-bls" {
  bucket = "khalid-rearc-bls"
}
# Destination Bucket for API Call to save JSON - had to change it queue for notification queue distinction
resource "aws_s3_bucket" "khalid-rearc-queue" {
  bucket = "khalid-rearc-queue"
}
# Destination Bucket for Analysis results for final lambda
resource "aws_s3_bucket" "khalid-rearc-results" {
  bucket = "khalid-rearc-results"
}


# IAM Section 
# IAM role for Lambda function
resource "aws_iam_role" "lambda_execution_role" {
  name = "lambda_execution_role_rearc"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM policy for S3 bucket access (read and write)
resource "aws_iam_policy" "s3_bucket_policy" {
  name        = "s3-bucket-policy"
  description = "Policy for S3 bucket access"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject",
        ],
        Effect = "Allow",
        Resource = [
          "arn:aws:s3:::khalid-rearc-bls",       # Bucket ARN
          "arn:aws:s3:::khalid-rearc-bls/*",     # Objects within the bucket
          "arn:aws:s3:::khalid-rearc-results",   # Bucket ARN
          "arn:aws:s3:::khalid-rearc-results/*", # Objects within the bucket
          "arn:aws:s3:::khalid-rearc-queue",     # Bucket ARN
          "arn:aws:s3:::khalid-rearc-queue/*",   # Objects within the bucket
        ]
      }
    ]
  })
}

# Attach the IAM policy to the Lambda execution role
resource "aws_iam_policy_attachment" "s3_bucket_policy_attachment" {
  name       = "s3_bucket_policy_attachment"
  policy_arn = aws_iam_policy.s3_bucket_policy.arn
  roles      = [aws_iam_role.lambda_execution_role.name]
}




# Layer provider - Needed Panda and Numpy layers for analysis

terraform {
  required_providers {
    klayers = {
      version = "~> 1.0.0"
      source  = "ldcorentin/klayer"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }

}

# Layer for pandas module
data "klayers_package_latest_version" "pandas" {
  name   = "pandas"
  region = "us-east-1"
}
# Layer for numpy module
data "klayers_package_latest_version" "numpy" {
  name   = "numpy"
  region = "us-east-1"
}

# Create a Lambda Layer for requests module 
resource "aws_lambda_layer_version" "requests_layer" {
  layer_name          = "requests-layer"
  description         = "Layer for requests module"
  compatible_runtimes = [var.PYTHON_RUNTIME] # Set the Python runtime version you're using

  # Specify the location of the requests library
  source_code_hash = filebase64sha256("layers/requests_layer.zip")
  filename         = "layers/requests_layer.zip"
}

# Create a Lambda Layer for numpy module
resource "aws_lambda_layer_version" "bs4_layer" {
  layer_name          = "bs4-layer"
  description         = "Layer for bs4 module"
  compatible_runtimes = [var.PYTHON_RUNTIME] # Set the Python runtime version you're using

  # Specify the location of the requests library
  source_code_hash = filebase64sha256("layers/bs4_layer.zip")
  filename         = "layers/bs4_layer.zip"
}


# Lambda Section

#zip the lambda function file before deploying
data "archive_file" "lambda_function_zip_copy_files" {
  type        = "zip"
  source_file = "lambda_code/copy_files_lambda.py"
  output_path = "out/copy_files_lambda.zip"
}


# Create Lambda Function 1: Copy files from URL to S3
resource "aws_lambda_function" "copy_files_lambda" {
  filename         = "out/copy_files_lambda.zip"
  function_name    = "CopyFilesLambda"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "copy_files_lambda.copy_files_to_s3"
  source_code_hash = data.archive_file.lambda_function_zip_copy_files.output_base64sha256
  runtime          = var.PYTHON_RUNTIME
  # Attach the requests layer to the Lambda function
  layers  = [aws_lambda_layer_version.requests_layer.arn, aws_lambda_layer_version.bs4_layer.arn]
  timeout = 60


  environment {
    variables = {
      SOURCE_URL         = "https://download.bls.gov/pub/time.series/pr/",
      DESTINATION_BUCKET = var.INPUT_BUCKET_1,
    }
  }


}

#zip the lambda function file before deploying
data "archive_file" "lambda_function_zip_api_call" {
  type        = "zip"
  source_file = "lambda_code/api_call_lambda.py"
  output_path = "out/api_call_lambda.zip"
}

# Create Lambda Function 2: Call API and save JSON to S3
resource "aws_lambda_function" "api_call_lambda" {
  filename         = "out/api_call_lambda.zip"
  function_name    = "ApiCallLambda"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "api_call_lambda.call_api_and_save_to_s3"
  source_code_hash = data.archive_file.lambda_function_zip_api_call.output_base64sha256
  runtime          = var.PYTHON_RUNTIME
  # Attach the requests layer to the Lambda function
  layers  = [aws_lambda_layer_version.requests_layer.arn]
  timeout = 60


  environment {
    variables = {
      SOURCE_URL    = "https://datausa.io/api/data?drilldowns=Nation&measures=Population",
      OUTPUT_BUCKET = var.INPUT_BUCKET_2,
      OUTPUT_FILE   = var.INPUT_FILE_POPULATION,
    }
  }

}

#zip the lambda function file before deploying
data "archive_file" "lambda_function_zip_process_data" {
  type        = "zip"
  source_file = "lambda_code/process_data_lambda.py"
  output_path = "out/process_data_lambda.zip"
}

# Create Lambda Function 3: Process data and write results to S3
resource "aws_lambda_function" "process_data_lambda" {
  filename         = "out/process_data_lambda.zip" # Replace with the path to your deployment package
  function_name    = "ProcessDataLambda"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "process_data_lambda.process_data_and_write_results"
  source_code_hash = data.archive_file.lambda_function_zip_process_data.output_base64sha256
  runtime          = var.PYTHON_RUNTIME
  timeout          = 120
  layers = [
    data.klayers_package_latest_version.pandas.arn, data.klayers_package_latest_version.numpy.arn
  ]

  environment {
    variables = {
      INPUT_BUCKET_1 = var.INPUT_BUCKET_1,
      INPUT_BUCKET_2 = var.INPUT_BUCKET_2,
      CSV_FILE       = var.INPUT_FILE_BLS,
      JSON_FILE      = var.INPUT_FILE_POPULATION,
      OUTPUT_BUCKET  = var.OUTPUT_BUCKET,
      ANALYSIS_FILE  = var.ANALYSIS_FILE,
    }
  }

}


#Scheduling Config

# Define a CloudWatch Event Rule to schedule the daily job
resource "aws_cloudwatch_event_rule" "daily_job_rule" {
  name                = "daily_job_rule"
  description         = "Scheduled daily job rule"
  schedule_expression = "cron(0 0 * * ? *)" # Schedule for daily execution at midnight UTC
}

# Define CloudWatch Event Targets to trigger Lambda functions
resource "aws_cloudwatch_event_target" "BLS" {
  rule      = aws_cloudwatch_event_rule.daily_job_rule.name
  arn       = aws_lambda_function.copy_files_lambda.arn
  target_id = "target-1"
}

resource "aws_cloudwatch_event_target" "JSON" {
  rule      = aws_cloudwatch_event_rule.daily_job_rule.name
  arn       = aws_lambda_function.api_call_lambda.arn
  target_id = "target-2"
}



# Create an SQS queue that tiggers process_data_lambda
resource "aws_sqs_queue" "sqs_queue" {
  name = "rearc-sqs-queue"
}

# Attach a policy to the SQS queue that allows S3 to send notifications
resource "aws_sqs_queue_policy" "sqs_queue_policy" {
  queue_url = aws_sqs_queue.sqs_queue.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action    = "sqs:SendMessage",
        Effect    = "Allow",
        Principal = "*",
        Resource  = aws_sqs_queue.sqs_queue.arn,
        Condition = {
          ArnLike = {
            "aws:SourceArn" = aws_s3_bucket.khalid-rearc-queue.arn
          }
        }
      }
    ]
  })
}

# Create an S3 event notification to trigger the SQS queue
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.khalid-rearc-queue.id

  queue {
    queue_arn = aws_sqs_queue.sqs_queue.arn
    events    = ["s3:ObjectCreated:*"]
  }
}
