# Ansible Vault

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Ansible Vault encrypts sensitive values inside YAML files so secrets can live in Git beside playbooks and inventory. At runtime, Ansible decrypts vault blobs in memory when you supply a password via prompt, file, or environment variable.

**Do not** commit production vault passwords or `~/.vault_pass` files. Labs use a local password file for practice only.

Lab files: `vault/secrets.yml` (encrypted), `playbooks/nodejs.yml` (loads via `vars_files`).

**Interactive reference:** [roles-and-vault.html](../../html/roles-and-vault.html)

---

## Key Concepts

| Term | Definition |
|------|------------|
| **Vault file** | Entire YAML file encrypted (`$ANSIBLE_VAULT;...`) |
| **Vault string** | Single encrypted value embedded in YAML (`!vault`) |
| **Vault ID** | Label for multiple passwords (`--vault-id`) |
| **Vault password** | Symmetric key—never commit to Git |

### Encryption Flow

```
Plain secrets.yml          ansible-vault encrypt          Ciphertext in Git
┌─────────────────┐        ─────────────────────►        ┌──────────────────┐
│ api_token: xxx  │                                      │ $ANSIBLE_VAULT;  │
│ db_password: y  │                                      │ 1.1;AES256...    │
└─────────────────┘                                      └────────┬─────────┘
                                                                  │
                     vault password (CI secret, not in repo)       │
                              │                                    │
                              └──────────► decrypt in memory ◄─────┘
                                              │
                                              ▼
                                    tasks use {{ api_token }}
```

---

## CLI Reference

| Task | Command |
|------|---------|
| Encrypt file | `ansible-vault encrypt vault/secrets.yml --vault-password-file ~/.vault_pass` |
| Decrypt file | `ansible-vault decrypt vault/secrets.yml --vault-password-file ~/.vault_pass` |
| View | `ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass` |
| Edit | `ansible-vault edit vault/secrets.yml --vault-password-file ~/.vault_pass` |
| Rekey | `ansible-vault rekey vault/secrets.yml --vault-password-file ~/.vault_pass --new-vault-password-file ~/.new_pass` |
| Encrypt string | `ansible-vault encrypt_string 'secret' --name api_token --vault-password-file ~/.vault_pass` |
| Create encrypted file | `ansible-vault create vault/new.yml --vault-password-file ~/.vault_pass` |

Encrypted files begin with:

```text
$ANSIBLE_VAULT;1.1;AES256
```

---

## Lab Setup (Training Only)

```bash
cd ansible/essentials/labs

# 1. Plaintext secrets (edit values first)
cat vault/secrets.yml
# api_token: "lab-api-token-abc123xyz"
# db_password: "lab-db-pass-secret"

# 2. Password file (chmod 600)
echo 'lab-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass

# 3. Encrypt
ansible-vault encrypt vault/secrets.yml --vault-password-file ~/.vault_pass

# 4. Verify
ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass
head -1 vault/secrets.yml   # $ANSIBLE_VAULT
```

---

## Loading Vault in Playbooks

`playbooks/nodejs.yml`:

```yaml
---
- name: Install Node.js 20.x
  hosts: webservers
  become: true
  vars_files:
    - ../vault/secrets.yml
  tasks:
    - name: Show token length (uses vault var)
      ansible.builtin.debug:
        msg: "api_token length is {{ api_token | length }}"
```

Run with decryption:

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml \
  --vault-password-file ~/.vault_pass
```

Without password → playbook fails to load `vars_files` (expected fail-closed behavior).

### Alternative: --ask-vault-pass

```bash
ansible-playbook playbooks/nodejs.yml -i inventory/hosts.ini.local --ask-vault-pass
```

---

## encrypt_string Pattern

Embed one secret in a public vars file:

```bash
ansible-vault encrypt_string 'mysecret' --name db_password \
  --vault-password-file ~/.vault_pass
```

Output (paste into YAML):

```yaml
db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  6638...
```

Useful when most of a file is non-secret.

---

## ansible.cfg Vault Options

```ini
[defaults]
vault_password_file = ~/.vault_pass   # lab only — not for production repos

[vault]
vault_identity_list = prod@~/.vault_pass_prod,staging@~/.vault_pass_stg
```

Multi-environment teams use `vault_identity_list` with `--vault-id`.

---

## Node.js Capstone Notes

Lab playbook installs **Node.js 20 LTS** on Ubuntu 22.04 using:

1. `ansible.builtin.apt` prerequisites (`ca-certificates`, `curl`, `gnupg`)
2. `ansible.builtin.get_url` for NodeSource GPG key → `/etc/apt/keyrings/nodesource.gpg`
3. `ansible.builtin.apt_repository` with `signed-by=` (modern apt)
4. `ansible.builtin.apt` install `nodejs`

**Avoid** deprecated patterns from old training:

| Deprecated | Use instead |
|------------|-------------|
| `apt_key` module | `get_url` + `signed-by` in repo line |
| Node 0.10 / Nodesource setup script | Node 20.x apt repo in playbook |
| Plaintext secrets in Git | `ansible-vault encrypt` |

Verify after run:

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "node --version"
```

---

## Security Model

| Safe in Git | Never in Git |
|-------------|--------------|
| `$ANSIBLE_VAULT` ciphertext | Vault password |
| Playbooks referencing vars | `~/.vault_pass` |
| Encrypted group_vars | Decrypted secrets in logs |

### Debug Hygiene

```yaml
# GOOD — metadata only
msg: "api_token length is {{ api_token | length }}"

# BAD — leaks secret to job output
msg: "token is {{ api_token }}"
```

### Production Alternatives

| Lab pattern | Production |
|-------------|------------|
| `~/.vault_pass` | CI/CD secret variable |
| Single shared password | Per-env keys in KMS |
| Secrets in app repo | Dedicated secrets repo or SOPS |
| Manual encrypt | Automated rotation pipeline |

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Decryption failed` | Wrong password | Verify `~/.vault_pass`; try `--ask-vault-pass` |
| `api_token` undefined | Missing vars_files or decrypt | Add `vars_files`; pass password flag |
| Playbook works locally, fails in CI | CI missing vault secret | Inject password via CI vars |
| File not encrypted | Forgot encrypt step | `ansible-vault encrypt ...` |
| `view` shows garbage | File corrupted | Restore from Git; re-encrypt |
| Mixed plain/encrypted | Partial edit | Re-encrypt entire file |
| Rekey loop | Wrong new password file | Test `view` with new pass immediately |

### Diagnostic Commands

```bash
file vault/secrets.yml                    # should show ASCII text with ANSIBLE_VAULT
ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass
ansible-playbook playbooks/nodejs.yml --syntax-check --vault-password-file ~/.vault_pass
```

---

## Vault with Inventory and group_vars

You can encrypt entire `group_vars/production.yml` or use `vault/` subdirectory:

```
group_vars/
└── webservers/
    ├── vars.yml          # public
    └── vault.yml         # encrypted secrets
```

Ansible auto-loads both when using directory style `group_vars/webservers/`.

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 07 | Vault + Node.js capstone | [lab07](../../labmanuals/lab07-vault-and-nodejs-capstone.md) |

**HTML companion:** [roles-and-vault.html](../../html/roles-and-vault.html)

---

## Cleanup (Lab)

```bash
rm -f ~/.vault_pass
ansible webservers -i inventory/hosts.ini.local -b \
  -m ansible.builtin.apt -a "name=nodejs state=absent autoremove=yes"
```

Re-encrypt `vault/secrets.yml` before sharing repo if you decrypted for experiments.

---

## Next Steps

1. Complete [Lab 07 capstone](../../labmanuals/lab07-vault-and-nodejs-capstone.md).
2. Continue to [Terraform essentials](../../../../terraform/essentials/labmanuals/) for full IaC + CM pipeline.
3. Optional: [Ansible Extended](../../extended/labmanuals/) — break-fix drills include vault handler scenarios.

---

## Quick Reference

```bash
ansible-vault encrypt vault/secrets.yml --vault-password-file ~/.vault_pass
ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass
ansible-playbook playbooks/nodejs.yml -i inventory/hosts.ini.local \
  --vault-password-file ~/.vault_pass
```

```yaml
vars_files:
  - ../vault/secrets.yml
```
