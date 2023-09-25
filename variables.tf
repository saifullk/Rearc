variable "instance_name" {
  description = "Instance for Khyber Projects"
  type        = string
  default     = "khyber_apps"
}

variable "ec2_instance_type" {
  description = "AWS EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "INPUT_BUCKET_1" {
  description = "Input Bucket for BLS Files"
  type        = string
  default     = "khalid-rearc-bls"
}

variable "INPUT_BUCKET_2" {
  description = "Input Bucket for JSON File"
  type        = string
  default     = "khalid-rearc-queue"
}


variable "OUTPUT_BUCKET" {
  description = "Output Bucket for Analysis results"
  type        = string
  default     = "khalid-rearc-results"
}

variable "INPUT_FILE_BLS" {
  description = "Input CSV file for Analysis"
  type        = string
  default     = "pr.data.0.Current"
}

variable "INPUT_FILE_POPULATION" {
  description = "Input JSON file for Analysis"
  type        = string
  default     = "population.json"
}

variable "ANALYSIS_FILE" {
  description = "Output of analysis results"
  type        = string
  default     = "analysis_results.txt"
}

variable "PYTHON_RUNTIME" {
  description = "Version of python needed"
  type        = string
  default     = "python3.9"
}


