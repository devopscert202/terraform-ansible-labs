# Ansible Vault

## Objective (conceptual)

**Ansible Vault** encrypts sensitive YAML at rest—passwords, API tokens, database strings—so playbooks and group_vars can live in git without plaintext secrets. At runtime, Ansible decrypts vault blobs when you supply a password or password file.

The mental model: Vault is a **lockbox inside your repo**; `--vault-password-file` is the key you never commit.

**Interactive reference:** [Roles and Vault](../../html/roles-and-vault.html)

## Vault file structure

Encrypted files are still YAML—values are ciphertext blobs:

```yaml
---
api_token: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          66386439653...
db_password: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          3361...
```

Lab placeholder before encryption (`vault/secrets.yml`):

```yaml
---
api_token: "replace-me-in-lab"
db_password: "replace-me-in-lab"
```

Replace values, then encrypt with `ansible-vault encrypt`.

## Create and edit secrets

```bash
ansible-vault create vault/secrets.yml
ansible-vault encrypt vault/secrets.yml
ansible-vault edit vault/secrets.yml
ansible-vault view vault/secrets.yml
ansible-vault decrypt vault/secrets.yml   # avoid on shared repos
```

## Running playbooks with vault

Use **`--vault-password-file`**, not deprecated or incorrect flag names:

```bash
ansible-playbook playbooks/nodejs.yml \
  --vault-password-file ~/.ansible/vault-pass.txt
```

Or prompt interactively:

```bash
ansible-playbook playbooks/nodejs.yml --ask-vault-pass
```

Store password files outside git with restrictive permissions (`chmod 600`).

## Referencing vault variables

Load via `vars_files` or `include_vars` in play:

```yaml
- name: Deploy app with secrets
  hosts: webservers
  become: true
  vars_files:
    - ../vault/secrets.yml
  tasks:
    - name: Show token length only
      ansible.builtin.debug:
        msg: "Token configured ({{ api_token | length }} chars)"
```

Never `debug` raw secrets in production logs.

## Encrypting single values

```bash
ansible-vault encrypt_string 's3cr3t' --name 'db_password'
```

Paste output into group_vars; useful for one secret without encrypting entire file.

## Vault in CI

- Inject vault password from secret manager into a ephemeral file.
- Pass `--vault-password-file` to `ansible-playbook` in pipeline.
- Rotate vault password with `ansible-vault rekey` when people leave the team.

## Vault vs other secret stores

| Approach | When |
|----------|------|
| Ansible Vault | Small teams, git-native secrets |
| HashiCorp Vault / cloud SM | Central rotation, dynamic credentials |
| Environment vars on control node | CI-only ephemeral secrets |

Essentials labs use Vault; enterprise platforms often combine Vault with external stores.

## Security practices

- Do not commit `vault-pass.txt` or `.vault_password`.
- Use different vault IDs per environment when needed (`--encrypt-vault-id`).
- Limit who can decrypt production vault files via repo permissions.

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible-vault encrypt vault/secrets.yml
ansible-playbook playbooks/nodejs.yml --syntax-check \
  --vault-password-file ~/.ansible/vault-pass.txt
ansible-vault rekey vault/secrets.yml
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 07: Vault and Node.js Capstone](../../labmanuals/lab07-vault-and-nodejs-capstone.md) | Encrypt secrets, run playbook with vault password file |
