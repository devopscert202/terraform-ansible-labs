# Terraform Provisioners

## Objective (conceptual)

**Provisioners** run scripts on create or destroy to perform actions providers cannot express declaratively. They are a **last resort**: prefer cloud-init, configuration management (Ansible), or native resource attributes. Provisioners couple infrastructure creation to machine-local scripts and complicate idempotency.

The mental model: Terraform builds the **hardware/API object**; provisioners run **one-off glue** on a narrow lifecycle hook (`create`, `destroy`). If Ansible could configure it, Ansible probably should.

**Interactive reference:** [Provisioners](../../html/provisioners.html)

## local-exec (Lab 04)

Runs a command on the machine running Terraform—no SSH required.

```hcl
variable "message" {
  type    = string
  default = "local-exec completed"
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

`terraform_data` is a lightweight resource useful for demonstrating hooks without creating cloud objects.

## remote-exec (Lab 05)

Runs commands over SSH after the resource exists. Requires a `connection` block and reachable host.

```hcl
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

- `private_key_path` is sensitive—pass via `TF_VAR_` or tfvars, never commit keys.
- Target host must exist and accept SSH before `remote-exec` runs.

## Lifecycle hooks

| Hook | Runs when |
|------|-----------|
| `create` | After resource created (default) |
| `destroy` | Before resource destroyed |

`when = create` or `when = destroy` restricts timing. Failed provisioners mark the resource tainted.

## Better alternatives

| Need | Prefer |
|------|--------|
| Install packages on VM | cloud-init `user_data` or Ansible playbook |
| Run database migrations | CI job or app release pipeline |
| Notify Slack | `null_resource` + external data, or event-driven automation |
| Copy files | `aws_s3_object`, SSH with Ansible `copy` module |

## Provisioner pitfalls

- Non-idempotent scripts re-run on replacement—guard with checks.
- `local-exec` depends on shell/OS on the runner (CI vs laptop).
- Destroy-time provisioners block destroy if they fail.
- Secrets in `inline` commands appear in logs and state.

## terraform_data as provisioner host

Both extended provisioner labs attach scripts to `terraform_data`—a resource type with no cloud cost that still participates in the dependency graph. Real EC2 instances can host `remote-exec` too, but only after the instance resource reports an IP and passes SSH checks.

## Ordering with depends_on

If a provisioner must run after another resource (for example, security group attached), add explicit `depends_on`—provisioners do not always infer dependencies from interpolated values alone.

## Connection block fields

| Field | Purpose |
|-------|---------|
| `type` | `ssh` or `winrm` |
| `host` | Target address |
| `user` | SSH username |
| `private_key` | Key material via `file()` |
| `timeout` | Handshake wait (seconds) |

Use `bastion_host` patterns for jump hosts in real networks—essentials labs assume direct SSH.

## Operational commands (reference)

```bash
cd terraform/extended/labs/lab04-local-exec-provisioner
terraform init
terraform apply
terraform taint terraform_data.local_action   # observe reprovision on next apply

cd ../lab05-remote-exec-provisioner
export TF_VAR_host=10.0.1.10
export TF_VAR_private_key_path=~/.ssh/lab.pem
terraform apply
terraform destroy
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 04: local-exec Provisioner](../../labmanuals/lab04-local-exec-provisioner.md) | Run host-side command on resource create |
| [Lab 05: remote-exec Provisioner](../../labmanuals/lab05-remote-exec-provisioner.md) | SSH connection block and inline commands |
