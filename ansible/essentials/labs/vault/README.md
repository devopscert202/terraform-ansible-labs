# Vault secrets (lab07)

`secrets.yml` ships as **plaintext** so you can practice `ansible-vault encrypt`.

```bash
ansible-vault encrypt secrets.yml --vault-password-file ~/.vault_pass
```

Do not commit `~/.vault_pass` or production secrets to Git.

Variables used by `playbooks/nodejs.yml`:

- `api_token` — demonstrated in debug task (length only)
- `db_password` — reserved for extended scenarios
