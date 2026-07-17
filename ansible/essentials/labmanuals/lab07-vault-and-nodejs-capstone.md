# Lab 07: Vault and Node.js Capstone

> **Goal:** Encrypt a secret with Ansible Vault and deploy Node.js using a playbook.
> **Time:** ~75 min · **Files:** `labs/vault/secrets.yml`, `labs/playbooks/nodejs.yml`

## Before you start

- [lab06](lab06-roles-create.md) complete

## Steps

### Step 1 — Create a vault password file (lab only)

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
echo 'lab-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass
```

Use a secrets manager in production — not a plain file.

### Step 2 — Encrypt secrets

```bash
ansible-vault encrypt vault/secrets.yml --encrypt-password-file ~/.vault_pass
```

If already encrypted in repo, decrypt then re-encrypt to practice:

```bash
ansible-vault view vault/secrets.yml --encrypt-password-file ~/.vault_pass
```

**Validate** — File begins with `$ANSIBLE_VAULT;`.

### Step 3 — Run Node.js playbook with vault

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --encrypt-password-file ~/.vault_pass
```

**Validate**

```text
failed=0
```

### Step 4 — Verify Node.js

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "node --version"
```

**Validate**

```text
v20.
```

(or your installed major version)

## Done when

- [ ] Vault file encrypts and decrypts at runtime
- [ ] `node --version` works on webservers

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Vault password error | Wrong `--encrypt-password-file` | Match password used at encrypt time |
| Node install failed | Repo/key issue | Check playbook uses Node 20 setup for Ubuntu 22.04 |

## Cleanup

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=nodejs state=absent autoremove=yes"
rm -f ~/.vault_pass
```

---
*Source: Lesson 6 AP-02, Lesson 5 LEP · Deep dive: [vault doc](../docs/07-vault/ansible-vault.md) · Ansible essentials complete*
