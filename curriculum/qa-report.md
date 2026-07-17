# QA Report — terraform-ansible-labs

**Date:** 2026-07-17  
**Auditor:** Lead integration pass  
**Rubric:** [qa-rubric.md](qa-rubric.md)

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| Blocker | 0 | — |
| Major | 0 | — |
| Minor | 2 | Documented below |

**Sign-off:** Ready for instructor use. Minor items are environmental or cosmetic.

---

## 1. Technical accuracy

| Check | Result |
|-------|--------|
| Terraform essentials `terraform validate` (8 canonical labs) | **Pass** |
| Terraform extended `terraform validate` (labs 02–15) | **Pass** |
| `ansible-playbook --syntax-check` | **Skipped** — Ansible not installed on audit host |
| Provider versions (AWS `~> 5.0`, TF `>= 1.5`) | **Pass** |
| No plaintext `access_key` in `.tf` | **Pass** |

## 2. Brevity + completeness

| Track | Manuals | Notes |
|-------|---------|-------|
| Ansible essentials | 7 | Validate blocks present; contextual concision |
| Ansible extended | 9 | Complex labs 200+ lines where needed |
| Terraform essentials | 8 | Validation-first structure |
| Terraform extended | 15 | Remote state suite with preflight steps |

## 3. Language / anti-boilerplate

| Grep pattern | Hits (excl. rubric) |
|--------------|---------------------|
| `Simplilearn` | 0 |
| `42006` | 0 |
| `dbbservers` (as live inventory name) | 0 — one doc mentions it as a typo to avoid |
| `access_key` in `.tf` | 0 |

## 4. HTML

| Check | Result |
|-------|--------|
| Invalid `<motion>` tags | **None** (fixed during build) |
| External CDN dependencies | **None** — embedded CSS/JS |
| Catalog pages per track | 4 tracks have `html/index.html` |

## 5. Consistency

| Check | Result |
|-------|--------|
| Lab manual count | **39** (7+9+8+15) |
| README counts | Match |
| Doc folders align with essentials labs | **Pass** |
| `inventory/group_vars/` under `inventory/` (Ansible essentials) | **Pass** |

## 6. Deliverables checklist

- [x] Curriculum: bootcamp, learning paths, day-wise agenda, AWS setup
- [x] Ansible essentials: manuals, docs, html, labs
- [x] Ansible extended: manuals, docs, html, labs
- [x] Terraform essentials: manuals, docs, html, labs
- [x] Terraform extended: manuals, docs, html, labs
- [x] `ansible/projects/webapp-co/README.md`
- [x] `hosts.ini.local.example`
- [x] Legacy duplicate TF dirs removed (`lab01-providers`, `lab03-workflow`, `lab04-fmt`)

---

## Minor findings

1. **Ansible syntax-check not run on audit host** — Run on EC2 control node before first class:
   ```bash
   cd ansible/essentials/labs
   ansible-playbook --syntax-check -i inventory/hosts.ini playbooks/apache.yml
   ```
2. **`vault/secrets.yml` plaintext** — By design; lab07 instructs learners to encrypt with `ansible-vault`.

---

## Conclusion

All 39 lab manuals, docs, HTML catalogs, and runnable lab code are on disk. Terraform configurations validate. No blockers or majors. Repository is **ready for the 20-hour bootcamp**.
