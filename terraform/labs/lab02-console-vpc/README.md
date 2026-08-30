# Lab 02 — Console VPC

This directory intentionally contains no Terraform configuration.

Lab 02 is built entirely by hand in the AWS console: a VPC, a public subnet, an internet
gateway, a default route, and a security group, each verified with the AWS CLI and then deleted
again. The point is to do the work manually once, so the declarative version later in the track
has something to contrast against.

Follow the lab manual: [`lab02-console-vpc.md`](../../labmanuals/lab02-console-vpc.md).

## Where these concepts return in code

| Console object | Terraform type | Lab |
|---|---|---|
| EC2 instance | `aws_instance` | [Lab 03 — Your first EC2 instance](../../labmanuals/lab03-first-ec2.md) |
| VPC, subnet | `aws_vpc`, `aws_subnet` | [Lab 09 — Modules](../../labmanuals/lab09-modules.md) |
| VPC, subnet, gateway, route table, security group | `aws_vpc`, `aws_subnet`, `aws_internet_gateway`, `aws_route_table`, `aws_security_group` | [Lab 21 — Capstone](../../labmanuals/lab10-capstone-vpc-ec2.md) |

Lab 21 is the full build: the same network you clicked together here, declared in one root
module and applied with a single command.
