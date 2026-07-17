# Ansible Vault

## Overview

Ansible Vault encrypts sensitive values inside YAML files so secrets can live in Git beside your playbooks. At runtime, Ansible decrypts vault files when you supply a password or password file.

**Do not** commit production vault passwords. Labs use a local `~/.vault_pass` file for practice only.

## Key concepts

| Task | Command |
|------|---------|
| Encrypt file | `ansible-vault encrypt vault/secrets.yml --encrypt-password-file ~/.vault_pass` |
| View encrypted | `ansible-vault view vault/secrets.yml --encrypt-password-file ~/.vault_pass` |
| Edit encrypted | `ansible-vault edit vault/secrets.yml --encrypt-password-file ~/.vault_pass` |
| Run playbook | `ansible-playbook site.yml --encrypt-password-file ~/.vault_pass` |

Encrypted files begin with `$ANSIBLE_VAULT;`.

Load secrets in a playbook:

```yaml
vars_files:
  - ../vault/secrets.yml
```

## Node.js capstone notes

The lab07 playbook installs **Node.js 20 LTS** on Ubuntu 22.04 using the modern NodeSource repository pattern—signed key in `/etc/apt/keyrings/`, `ansible.builtin.apt_repository`, and `ansible.builtin.apt`. Avoid deprecated `apt_key` and ancient Node 0.10 examples from older course PDFs.

## Diagram

[Roles and Vault](../html/roles-and-vault.html)

## Hands-on labs

- [lab07 — Vault and Node.js capstone](../../labmanuals/lab07-vault-and-nodejs-capstone.md)

## Next steps

- Continue to [Terraform essentials](../../../terraform/essentials/labmanuals/) in the 20-hour bootcamp
- Optional depth: [Ansible extended](../../extended/labmanuals/)
