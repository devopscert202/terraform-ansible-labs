# Lab 07: Vault and Node.js Capstone

> **Goal:** Encrypt secrets with Ansible Vault, run a multi-task Node.js 20 deployment playbook that loads vault variables, and validate the full Ansible Essentials toolchain end to end.
> **Time:** ~90 min · **Difficulty:** Advanced · **Files:** `labs/vault/secrets.yml`, `labs/playbooks/nodejs.yml`

## Overview

Production Ansible repos store **secrets in version control** by encrypting them with **Ansible Vault**. At runtime, you supply a password (or password file) so Ansible decrypts variables before tasks execute. This capstone lab encrypts `vault/secrets.yml`, runs `playbooks/nodejs.yml` with `--vault-password-file`, and verifies Node.js 20 on all web servers.

The Node.js playbook demonstrates modern Ubuntu packaging patterns: GPG key in `/etc/apt/keyrings/`, `ansible.builtin.apt_repository`, and `ansible.builtin.apt` — not deprecated `apt_key` or legacy Node 0.x installers.

This lab ties together inventory (lab 01–02), ad hoc validation (lab 03), playbooks (lab 04–05), roles (lab 06), and secrets management.

## Learning objectives

By the end of this lab you will be able to:

- Create a vault password file for lab use (`~/.vault_pass`)
- Encrypt, view, and edit vault files with `ansible-vault`
- Load encrypted secrets via `vars_files` in a playbook
- Run playbooks with `--vault-password-file` / `--ask-vault-pass`
- Walk through each task in `playbooks/nodejs.yml` and explain its purpose
- Verify Node.js installation without exposing secret values in logs
- Apply security hygiene: never commit vault passwords or plaintext secrets
- Troubleshoot vault decryption and NodeSource repository errors

## Prerequisites

- [ ] [Lab 06 — Ansible roles](lab06-roles-create.md) complete
- [ ] `inventory/hosts.ini.local` with working `webservers` (`web1`, `web2`)
- [ ] Ubuntu 22.04 targets with outbound HTTPS to `deb.nodesource.com`
- [ ] Ansible Core 2.14+ on control node
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Vault concepts and password file | `~/.vault_pass` |
| [2](#ex2) | Encrypt and inspect secrets.yml | `ansible-vault` CLI |
| [3](#ex3) | Read nodejs.yml playbook | Task-by-task |
| [4](#ex4) | Run Node.js deployment | Full apply |
| [5](#ex5) | Validate Node.js and vault variable use | Verification |
| [6](#ex6) | Vault operations and security review | Edit, rekey, hygiene |
| [7](#ex7) | Capstone integration checklist | End-to-end |

## Secrets reference

**`vault/secrets.yml` (plaintext before encryption):**

```yaml
---
api_token: "replace-me-in-lab"
db_password: "replace-me-in-lab"
```

**`playbooks/nodejs.yml`:**

```yaml
---
- name: Install Node.js 20.x
  hosts: webservers
  become: true
  vars_files:
    - ../vault/secrets.yml
  tasks:
    - name: Install prerequisites
      ansible.builtin.apt:
        name:
          - ca-certificates
          - curl
          - gnupg
        state: present
        update_cache: true

    - name: Create keyrings directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"

    - name: Add NodeSource GPG key
      ansible.builtin.get_url:
        url: https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key
        dest: /etc/apt/keyrings/nodesource.gpg
        mode: "0644"

    - name: Add NodeSource repository
      ansible.builtin.apt_repository:
        repo: "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main"
        filename: nodesource
        state: present

    - name: Install nodejs
      ansible.builtin.apt:
        name: nodejs
        state: present
        update_cache: true

    - name: Show token length (uses vault var)
      ansible.builtin.debug:
        msg: "api_token length is {{ api_token | length }}"
```

**Lab vault password:** `lab-vault-password` (stored in `~/.vault_pass`)

---

## Exercise 1 — Vault concepts and password file

<a id="ex1"></a>

### Step 1.1 — Change to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
pwd
```

**Validate**

```text
.../ansible/essentials/labs
```

**What happened:** Vault commands and playbooks use paths relative to `labs/`.

### Step 1.2 — Read vault README

```bash
cat vault/README.md
```

**Validate** — documents encrypt command and variables `api_token`, `db_password`.

**What happened:** `secrets.yml` ships **plaintext** in the repo so you practice encryption. Production repos commit only encrypted blobs.

### Step 1.3 — Inspect plaintext secrets (before encryption)

```bash
cat vault/secrets.yml
```

**Validate**

```yaml
api_token: "replace-me-in-lab"
db_password: "replace-me-in-lab"
```

If file already starts with `$ANSIBLE_VAULT;`, skip to Step 1.5 — it is already encrypted.

**What happened:** These variables load into play memory when `vars_files` references this path and vault password is supplied.

### Step 1.4 — Create vault password file

```bash
echo 'lab-vault-password' > ~/.vault_pass
chmod 600 ~/.vault_pass
```

**Validate**

```bash
ls -l ~/.vault_pass
```

```text
-rw------- ... /home/ubuntu/.vault_pass
```

**What happened:** Password file mode `600` restricts read to owner. **Never commit** `~/.vault_pass` to Git. In CI/CD use secret managers (Vault, AWS Secrets Manager, GitHub Actions secrets) to inject passwords at runtime.

### Step 1.5 — Confirm password file is git-ignored (on your machine)

```bash
git check-ignore -v ~/.vault_pass 2>/dev/null || echo "Not in repo path (expected)"
```

**Validate** — not tracked in repository.

**What happened:** Defense in depth — even if you accidentally `git add`, global gitignore or path outside repo should protect lab password file.

---

## Exercise 2 — Encrypt and inspect secrets.yml

<a id="ex2"></a>

### Step 2.1 — Encrypt secrets file

If `vault/secrets.yml` is still plaintext:

```bash
ansible-vault encrypt vault/secrets.yml --vault-password-file ~/.vault_pass
```

**Validate**

```bash
head -1 vault/secrets.yml
```

```text
$ANSIBLE_VAULT;1.1;AES256
```

**What happened:** Ansible replaces file contents with AES256-encrypted text. Only the header is human-readable.

### Step 2.2 — Attempt to cat encrypted file

```bash
cat vault/secrets.yml
```

**Validate** — ciphertext blocks, not `api_token` plaintext.

**What happened:** This is safe to commit (with caution) — without the password, secrets are not recoverable from repo alone.

### Step 2.3 — View decrypted content with ansible-vault

```bash
ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass
```

**Validate**

```yaml
api_token: replace-me-in-lab
db_password: replace-me-in-lab
```

**What happened:** `view` decrypts to stdout without writing plaintext back to disk.

### Step 2.4 — Edit secrets with ansible-vault (optional customization)

```bash
ansible-vault edit vault/secrets.yml --vault-password-file ~/.vault_pass
```

Change `api_token` to a unique lab value, e.g. `my-lab-token-abc123`. Save and exit editor.

**Validate**

```bash
ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass | grep api_token
```

Shows your updated token string.

**What happened:** `edit` decrypts to temp file, re-encrypts on save — preferred over decrypt/edit/encrypt manual cycle.

### Step 2.5 — Verify encryption with strings grep

```bash
grep -c 'api_token' vault/secrets.yml || echo "api_token not in ciphertext (good)"
```

**Validate** — plaintext key name should not appear in encrypted file.

**What happened:** Variable **names** are inside encrypted payload — but ciphertext should not contain obvious plaintext values.

---

## Exercise 3 — Read nodejs.yml playbook

<a id="ex3"></a>

### Step 3.1 — Display full playbook

```bash
cat playbooks/nodejs.yml
```

**Validate** — matches reference block: `vars_files`, five tasks, FQCN modules.

**What happened:** Read before run — production change management requires understanding each task.

### Step 3.2 — Trace vars_files path

```bash
realpath playbooks/nodejs.yml vault/secrets.yml
```

**Validate** — `../vault/secrets.yml` from `playbooks/` resolves to `labs/vault/secrets.yml`.

**What happened:** Relative paths in playbooks resolve from the playbook file location, not cwd.

### Step 3.3 — Syntax-check (vault not required for syntax)

```bash
ansible-playbook --syntax-check playbooks/nodejs.yml
```

**Validate** — passes (syntax check does not decrypt vault).

**What happened:** Syntax check validates YAML and module parameters only.

### Step 3.4 — List tasks

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --list-tasks
```

**Validate**

```text
Install prerequisites
Add NodeSource GPG key
Add NodeSource repository
Install nodejs
Show token length (uses vault var)
```

**What happened:** Five-task pipeline: prerequisites → trust key → apt repo → package → debug proof of vault var.

### Step 3.5 — Task-by-task purpose

| Task | Module | Purpose |
|------|--------|---------|
| Install prerequisites | `ansible.builtin.apt` | `ca-certificates`, `curl`, `gnupg` for HTTPS apt |
| Add NodeSource GPG key | `ansible.builtin.get_url` | Download signing key to `/etc/apt/keyrings/` |
| Add NodeSource repository | `ansible.builtin.apt_repository` | Modern signed-by repo line for Node 20.x |
| Install nodejs | `ansible.builtin.apt` | Install Node.js 20 LTS package |
| Show token length | `ansible.builtin.debug` | Prove `api_token` loaded without printing secret |

**Validate** — you can explain each row without reading the file.

---

## Exercise 4 — Run Node.js deployment

<a id="ex4"></a>

### Step 4.1 — Baseline — node not installed

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "node --version" || true
```

**Validate** — `command not found` or non-zero rc before install.

**What happened:** Establishes pre-state for capstone verification.

### Step 4.2 — Run playbook WITH vault password file

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --vault-password-file ~/.vault_pass
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=...   unreachable=0   failed=0
web2   : ok=...   changed=...   unreachable=0   failed=0
```

`failed=0` on every host.

**What happened:** Ansible decrypts `vault/secrets.yml` into play variables before tasks run. Apt tasks may take several minutes on first run.

### Step 4.3 — Find debug output for token length

Scroll playbook output for:

```text
TASK [Show token length (uses vault var)] ***
ok: [web1] => {
    "msg": "api_token length is 18"
}
```

(length depends on your `api_token` value)

**Validate** — message shows numeric length, **not** the token itself.

**What happened:** Safe logging pattern — never `debug: var=api_token` in production. Length proves variable resolution.

### Step 4.4 — Run without vault password (expect failure)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml 2>&1 | tail -5
```

**Validate** — error about vault password required or decryption failure.

**What happened:** Proves secrets are protected — playbook cannot load `vars_files` encrypted entry without credentials.

### Step 4.5 — Re-run with vault (idempotency)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --vault-password-file ~/.vault_pass
```

**Validate** — `changed=0` on apt/repo tasks; debug still `ok`.

**What happened:** Second run confirms idempotent package and repository management.

---

## Exercise 5 — Validate Node.js and vault variable use

<a id="ex5"></a>

### Step 5.1 — Check node version on all webservers

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "node --version"
```

**Validate**

```text
v20.
```

(major version 20 — e.g. `v20.19.0`)

**What happened:** NodeSource `node_20.x` track delivers Node 20 LTS on Ubuntu 22.04.

### Step 5.2 — Check npm included

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "npm --version"
```

**Validate** — semver string, e.g. `10.x.x`.

**What happened:** NodeSource `nodejs` package bundles npm.

### Step 5.3 — Verify NodeSource apt source file

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "cat /etc/apt/sources.list.d/nodesource.list"
```

**Validate** — line contains `deb.nodesource.com/node_20.x` and `signed-by=/etc/apt/keyrings/nodesource.gpg`.

**What happened:** Matches `ansible.builtin.apt_repository` `filename: nodesource` parameter.

### Step 5.4 — Verify GPG key file

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "ls -l /etc/apt/keyrings/nodesource.gpg"
```

**Validate**

```text
-rw-r--r-- ... /etc/apt/keyrings/nodesource.gpg
```

**What happened:** Modern apt requires keyring path in repo line — replaces deprecated `apt_key`.

### Step 5.5 — Confirm db_password loaded but unused

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --vault-password-file ~/.vault_pass -e "ansible_python_interpreter=/usr/bin/python3" --tags never 2>/dev/null; ansible-vault view vault/secrets.yml --vault-password-file ~/.vault_pass | grep db_password
```

**Validate** — `db_password` exists in vault for extended scenarios; playbook does not log it.

**What happened:** Loading entire vault file is normal — unused vars stay in memory for child roles or future tasks.

### Step 5.6 — Quick Node eval

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "node -e \"console.log(process.version)\""
```

**Validate** — prints `v20.x.x`.

---

## Exercise 6 — Vault operations and security review

<a id="ex6"></a>

### Step 6.1 — Rekey vault file (optional advanced)

Practice changing vault password:

```bash
ansible-vault rekey vault/secrets.yml --vault-password-file ~/.vault_pass --new-vault-password-file ~/.vault_pass
```

(Using same file is no-op practice — in real rekey, `--new-vault-password-file` points to a new password)

**Validate** — command succeeds; `view` still works with `~/.vault_pass`.

**What happened:** Rekey rotates encryption without decrypting secrets to plaintext on disk permanently.

### Step 6.2 — Decrypt for emergency recovery (lab only)

```bash
cp vault/secrets.yml vault/secrets.yml.encrypted.bak
ansible-vault decrypt vault/secrets.yml --vault-password-file ~/.vault_pass
head -3 vault/secrets.yml
```

**Validate** — plaintext YAML visible.

**What happened:** Decrypt only when necessary — immediately re-encrypt:

```bash
ansible-vault encrypt vault/secrets.yml --vault-password-file ~/.vault_pass
```

**Validate** — file starts with `$ANSIBLE_VAULT;` again.

### Step 6.3 — Security checklist review

| Practice | Lab | Production |
|----------|-----|------------|
| Vault password in `~/.vault_pass` | Yes | Use CI secret injection |
| Commit encrypted secrets | Practice | Yes, with tight access |
| Commit vault password | **Never** | **Never** |
| `debug` with secret values | Avoid | **Never** |
| `no_log: true` on sensitive tasks | Not shown | **Always** for credentials |

**Validate** — you can articulate each row.

### Step 6.4 — Alternative: ask vault password interactively

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/nodejs.yml --ask-vault-pass
```

Enter `lab-vault-password` when prompted.

**Validate** — playbook succeeds.

**What happened:** Interactive prompt suits human runs; password file suits automation.

### Step 6.5 — Review interactive Vault diagram

Open in browser:

- [Roles and Vault overview](../html/roles-and-vault.html)

---

## Exercise 7 — Capstone integration checklist

<a id="ex7"></a>

### Step 7.1 — Inventory ping

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — all `pong`.

### Step 7.2 — Group variables present

```bash
ansible-inventory -i inventory/hosts.ini.local --host web1 | grep -E 'app_env|webserver_port'
```

**Validate** — `production` and `80`.

### Step 7.3 — Apache from role still active

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate** — `active` (if lab 06 was completed).

### Step 7.4 — MOTD from lab 05 (optional)

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "head -1 /etc/motd"
```

**Validate** — `Welcome to web1` if MOTD not cleaned up.

### Step 7.5 — Node.js from lab 07

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "node --version"
```

**Validate** — `v20.x`.

### Step 7.6 — Document your Ansible Essentials stack

You have now applied:

1. **Static inventory** — `hosts.ini.local`
2. **Group vars** — `group_vars/webservers.yml`
3. **Ad hoc modules** — ping, command, apt
4. **Playbooks** — apache, vars-demo, nodejs
5. **Templates** — `motd.j2`
6. **Roles** — `webserver`
7. **Vault** — encrypted `secrets.yml`

**Validate** — complete [Done when](#done-when) checklist below.

---

## Key takeaways

- Ansible Vault encrypts YAML files at rest; runtime decryption requires password or password file
- `vars_files` loads vault-encrypted files when playbook runs with vault credentials
- Never print secrets in `debug` — use length checks or `no_log: true`
- Node.js 20 on Ubuntu 22.04 uses NodeSource with `signed-by` keyring pattern
- `ansible-vault encrypt|view|edit|decrypt|rekey` manage secret file lifecycle
- Capstone integrates every prior lab into a production-shaped workflow
- Replace `~/.vault_pass` with enterprise secret management before real deployments

## Done when

- [ ] `~/.vault_pass` exists with mode `600` and password `lab-vault-password`
- [ ] `vault/secrets.yml` is encrypted (`$ANSIBLE_VAULT;` header)
- [ ] `ansible-vault view` shows `api_token` and `db_password`
- [ ] `ansible-playbook playbooks/nodejs.yml --vault-password-file ~/.vault_pass` completes with `failed=0`
- [ ] Debug task shows `api_token length is N` without revealing the token
- [ ] `node --version` returns `v20.x` on all webservers
- [ ] Playbook fails without vault password (security proof)
- [ ] You completed capstone integration checks in exercise 7

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Decryption failed` | Wrong password in `~/.vault_pass` | Recreate with `lab-vault-password`; re-encrypt secrets |
| `Vault password required` | Missing `--vault-password-file` | Add flag or use `--ask-vault-pass` |
| `ERROR! Attempting to decrypt but no vault secrets found` | File not encrypted but playbook expects vault | Run `ansible-vault encrypt vault/secrets.yml` |
| NodeSource 404 or GPG error | Network egress blocked | Verify HTTPS outbound; check corporate proxy |
| `Failed to lock apt` | Concurrent apt | Wait; retry playbook |
| `nodejs` wrong version | Old Node from Ubuntu repo | Ensure NodeSource repo task changed; `apt-cache policy nodejs` |
| `Undefined variable: api_token` | Vault not decrypted | Pass vault password; verify `vars_files` path |
| get_url failed on GPG key | TLS or DNS issue | `curl -I https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key` from target |
| Debug shows length 0 | Empty api_token in vault | `ansible-vault edit vault/secrets.yml` and set value |

## Cleanup

Remove Node.js packages (optional):

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=nodejs state=absent autoremove=yes"
```

Remove NodeSource repo (optional):

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt_repository -a "repo='deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main' filename=nodesource state=absent"
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/etc/apt/keyrings/nodesource.gpg state=absent"
```

Remove vault password file:

```bash
rm -f ~/.vault_pass
```

Restore encrypted vault backup if you created one:

```bash
# Only if you saved secrets.yml.encrypted.bak during exercise 6
mv vault/secrets.yml.encrypted.bak vault/secrets.yml
```

Decrypt secrets for next learner (lab environment reset only):

```bash
ansible-vault decrypt vault/secrets.yml --vault-password-file ~/.vault_pass
```

**Validate** — lab targets returned to desired state; no vault password file on shared systems.

## Reference links

- [Ansible Vault](../docs/07-vault/ansible-vault.md)
- [Interactive roles and Vault](../html/roles-and-vault.html)
- [Vault documentation](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [NodeSource distributions](https://github.com/nodesource/distributions)
- [20-hour bootcamp](../../../curriculum/20-hour-bootcamp.md)
- [Terraform essentials next](../../../terraform/essentials/labmanuals/)

## Bootcamp completion

Congratulations — you have completed the **Ansible Essentials** lab track:

| Lab | Skill |
|-----|-------|
| 01 | Static INI inventory |
| 02 | Groups and group_vars |
| 03 | Ad hoc commands |
| 04 | Playbooks and handlers |
| 05 | Variables and Jinja templates |
| 06 | Roles |
| 07 | Vault and Node.js capstone |

Continue to Terraform essentials or Ansible extended modules per the [bootcamp curriculum](../../../curriculum/20-hour-bootcamp.md).

## Next steps

- [Lab manual index](README.md)
- [Interactive catalog](../html/index.html)
- [Ansible extended track](../../extended/labmanuals/) (optional)

---
*Source: Ansible Essentials bootcamp · Lesson 6 AP-02, Lesson 5 LEP · Ansible Essentials complete*
