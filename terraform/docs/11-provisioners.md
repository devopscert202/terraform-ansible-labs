# Terraform Provisioners

Backs labs 14 and 15. Covers what provisioners do, why HashiCorp calls them a last resort, the two
kinds you will meet, and what to use instead in almost every case.

## The escape hatch

A **provisioner** runs a script or command as part of a resource's lifecycle. It is Terraform's
escape hatch from being declarative: instead of describing an end state, you are giving imperative
instructions to execute.

That is exactly why it should make you uncomfortable. Everything good about Terraform —
idempotency, a reviewable plan, safe re-runs — comes from being declarative. A provisioner opts out
of all three:

| Property | A normal resource | A provisioner |
|---|---|---|
| Shown in the plan | Yes, argument by argument | No. The plan says a provisioner will run, not what it will do |
| Safe to re-run | Yes, converges to the same state | Only if your script happens to be idempotent |
| Recorded in state | Full attributes | Nothing. Terraform records only that it succeeded |
| Failure behaviour | The resource is not created | **The resource exists and is marked tainted** |

HashiCorp's own documentation describes provisioners as a last resort. That is not boilerplate
caution — it is the correct reading. Learn them so you recognise them in existing code and know
what they cost, then reach for the alternatives below.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## local-exec (lab14)

`local-exec` runs a command **on the machine running Terraform** — your laptop, or a CI runner. No
network access to the target is needed, because there is no target.

```hcl
variable "message" {
  type        = string
  default     = "local-exec completed"
  description = "Text the local-exec provisioner prints on the machine running Terraform."
}

resource "terraform_data" "local_action" {
  input = var.message
  provisioner "local-exec" {
    command = "printf '%s\n' '${self.input}'"
  }
}

output "message" {
  value = terraform_data.local_action.output
}
```

| Element | Meaning |
|---|---|
| `provisioner "local-exec"` | Nested inside the resource whose lifecycle it hooks into |
| `command` | The shell command. Runs after the resource is created |
| `self.input` | `self` refers to the resource the provisioner is attached to. Inside a provisioner you must use `self`, not `terraform_data.local_action` — the latter would be a self-reference cycle |

Useful additional arguments: `working_dir` sets the directory, `environment = { KEY = "value" }`
passes environment variables, and `interpreter` overrides the default shell.

`terraform_data` is a built-in resource that stores a value in state and calls no API. It costs
nothing, needs no credentials, and still participates in the dependency graph — which makes it the
right host for demonstrating a lifecycle hook without a server.

The portability problem is worth naming: this command is a shell command, and it runs wherever
Terraform runs. A `local-exec` that works on your macOS laptop can fail in a minimal Linux CI
container that lacks the binary you assumed. If you must use one, keep it to POSIX basics.

## remote-exec (lab15)

`remote-exec` runs commands **on the resource itself**, over SSH or WinRM. It needs a `connection`
block and a reachable, already-booted host.

```hcl
variable "host" {
  type        = string
  description = "Reachable SSH host. Supply with TF_VAR_host or terraform.tfvars."
}

variable "user" {
  type        = string
  default     = "ec2-user"
  description = "SSH login name. Amazon Linux 2023 uses ec2-user; Ubuntu uses ubuntu."
}

variable "private_key_path" {
  type        = string
  sensitive   = true
  description = "Path to an SSH private key; do not commit it."
}

resource "terraform_data" "bootstrap" {
  input = var.host
  connection {
    type        = "ssh"
    host        = var.host
    user        = var.user
    private_key = file(pathexpand(var.private_key_path))
  }
  provisioner "remote-exec" {
    inline = ["echo Terraform remote-exec connected to $(hostname)"]
  }
}
```

The `connection` block:

| Field | Purpose |
|---|---|
| `type` | `ssh` (default) or `winrm` |
| `host` | Target address. On a real instance, usually `self.public_ip` |
| `user` | Login name. `ec2-user` on Amazon Linux 2023, `ubuntu` on Ubuntu |
| `private_key` | The key **material**, not a path — hence `file()` |
| `port` | Defaults to 22 for SSH |
| `timeout` | How long to keep retrying the handshake. Default `5m` |
| `bastion_host` | Connect via a jump host, for instances with no public address |

`remote-exec` accepts `inline` (a list of commands), `script` (one local file, uploaded and run),
or `scripts` (several).

Note `private_key = file(pathexpand(var.private_key_path))`. `pathexpand` expands `~` to your home
directory, since Terraform does not do shell expansion. `file()` reads the key material at plan
time, on the machine running Terraform.

### Why remote-exec is the fragile one

`local-exec` needs a working shell. `remote-exec` needs a working shell **plus** an entire network
path, and each link is a way to hang until timeout:

- The instance must have finished booting and started `sshd` — being "created" per the AWS API is
  not the same as being ready.
- A route to the instance must exist: public IP or bastion, internet gateway, route table.
- Security group rules must permit port 22 *from wherever Terraform is running*, which for a CI
  runner is often an address you cannot predict.
- The key must match, and the OS user must be right.

When it fails, it fails slowly — `timeout` has to elapse first — and the resource is left created
but tainted. This is why lab15 attaches the provisioner to `terraform_data` and asks you to supply
your own reachable host: it isolates the SSH mechanics from the networking, which lab10 handles
separately.

The target instance in lab15 is launched with `aws ec2 run-instances` rather than by Terraform, and
because that command names no subnet it needs the region's **default VPC**. Along with lab21 it is
one of only two labs in the track that still do. Check and create before you start:

```bash
aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[].VpcId' --output text

aws ec2 create-default-vpc
```

Without one, `run-instances` fails with `VPCIdNotSpecified: No default VPC for this user`.

## Lifecycle timing

```hcl
provisioner "local-exec" {
  when       = destroy
  on_failure = continue
  command    = "echo cleaning up ${self.input}"
}
```

| Argument | Values | Effect |
|---|---|---|
| `when` | `create` (default), `destroy` | Run after creation, or before destruction |
| `on_failure` | `fail` (default), `continue` | Abort the apply, or log and carry on |

Destroy-time provisioners have a sharp edge: a failing one **blocks the destroy**, and since
`on_failure = fail` is the default, you can end up unable to tear down your own infrastructure
until you edit the configuration. They also cannot reference anything except `self`, and they are
skipped entirely if the resource was never successfully created. Use `on_failure = continue` on
anything destroy-time.

## Tainting on failure

When a provisioner fails, the resource still exists — the API call that created it already
succeeded — but Terraform marks it **tainted** in state. The next `apply` will destroy and recreate
it, on the assumption that a half-configured object is worse than none.

This is the failure mode people find most surprising: a typo in a bootstrap script causes an
instance to be rebuilt on every subsequent apply until the script is fixed.

## What to use instead

Almost every provisioner has a better declarative answer. This is the table to consult before
writing one:

| What you want | Use instead of a provisioner |
|---|---|
| Install packages, write files, start services on a new VM | **`user_data`** — cloud-init, runs on the instance at first boot with no network path from Terraform. This is what lab10 and lab22 do |
| Configure existing servers, repeatedly and idempotently | **Ansible**, run as a separate step after `terraform apply` |
| Build a machine image with software preinstalled | **Packer**, then reference the resulting AMI |
| Copy a file to an object store | **`aws_s3_object`** — a real resource, tracked in state |
| Render a config file from Terraform values | **`templatefile()`** into `user_data` or an `aws_s3_object` |
| Wait for something to become ready | Provider `timeouts` blocks, or health checks in the consuming system |
| Run database migrations | Your application's release pipeline, not infrastructure provisioning |
| Send a notification after apply | Your CI job, after Terraform exits |

`user_data` deserves the emphasis. Compare lab15's `remote-exec` with what lab10 does:

```hcl
resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>${local.name} is live</h1>" > /var/www/html/index.html
  EOT
}
```

Same outcome — a configured web server — with none of the fragility. `user_data` is an argument on
the instance, so it appears in the plan, is stored in state, and needs no inbound connectivity from
Terraform at all. The instance configures itself. Note that changing `user_data` replaces the
instance by default, which is usually the right behaviour for immutable infrastructure.

## Pitfalls

- **Not idempotent by default.** Your script runs again in full on every replacement. Guard it.
- **Invisible in the plan.** A reviewer cannot see what the command will do.
- **Secrets leak.** Anything in `inline` or `command` may appear in Terraform's log output, and in
  CI logs. Never interpolate a password into a command.
- **`depends_on` is often needed.** A provisioner only inherits dependencies from values it
  actually references. If it needs a route table that it does not mention, say so explicitly.
- **No partial retry.** A `remote-exec` with five `inline` commands that fails on the fourth reruns
  all five next time.

## Command reference

```bash
cd terraform/labs/lab14-local-exec-provisioner
terraform init
terraform apply                                   # watch the command output inline
terraform apply -replace=terraform_data.local_action   # force it to run again
terraform destroy

cd ../lab15-remote-exec-provisioner
export TF_VAR_host=203.0.113.10                   # a host you can already SSH to
export TF_VAR_private_key_path=~/.ssh/lab.pem
terraform init
terraform apply
terraform destroy
```

## Where next

- The declarative alternative in a full build: [`08-capstone.md`](08-capstone.md) and lab10's `user_data`
- Separate state files for one configuration, the next topic at lab16:
  [`12-workspaces.md`](12-workspaces.md)
- Remote state, which lab17 onwards depends on: [`13-remote-state.md`](13-remote-state.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 14: local-exec Provisioner](../labmanuals/lab14-local-exec-provisioner.md) | Run a command on the machine running Terraform, on resource create |
| [Lab 15: remote-exec Provisioner](../labmanuals/lab15-remote-exec-provisioner.md) | SSH `connection` block and `inline` commands against a reachable host |
