terraform {
  backend "s3" {
    bucket         = "mentorpal-classifier-service-tf-state-us-east-1"
    region         = "us-east-1"
    key            = "terraform.tfstate"
    dynamodb_table = "mentorpal-classifier-service-tf-lock"
  }
}

provider "aws" {
  region = "us-east-1"
  alias  = "us_east_1"
}
