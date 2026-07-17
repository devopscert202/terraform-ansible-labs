resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = {
    Name      = "${var.name}-vpc"
    ManagedBy = "Terraform"
  }
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.subnet_cidr

  tags = {
    Name      = "${var.name}-subnet"
    ManagedBy = "Terraform"
  }
}
