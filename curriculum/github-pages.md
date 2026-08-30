# GitHub Pages setup

This repo publishes lab manuals, docs, and **offline HTML catalogs** via Jekyll on GitHub Pages.

**Site URL:** https://devopscert202.github.io/terraform-ansible-labs/

## One-time repo settings

1. Open **Settings → Pages** on GitHub
2. Under **Build and deployment**, set **Source** to **GitHub Actions**

## Deploy workflow

Pushes to `main` run [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), which:

1. Builds the site with Jekyll (`actions/jekyll-build-pages`)
2. Publishes HTML under `ansible/**/html/` and `terraform/html/` as static files
3. Renders `index.md` and Markdown lab manuals with the Cayman theme

## If workflow push fails (OAuth `workflow` scope)

The `devopscert202` GitHub CLI token may need the `workflow` scope:

```bash
gh auth switch -u devopscert202
gh auth refresh -h github.com -s workflow
cd terraform-ansible-labs
git add .github/workflows/pages.yml
git commit -m "Add GitHub Pages deploy workflow"
git push origin main
```

## HTML catalog links (live)

| Page | URL |
|-------|-----|
| Ansible essentials | https://devopscert202.github.io/terraform-ansible-labs/ansible/essentials/html/index.html |
| Ansible extended | https://devopscert202.github.io/terraform-ansible-labs/ansible/extended/html/index.html |
| Terraform track catalog | https://devopscert202.github.io/terraform-ansible-labs/terraform/html/index.html |
| Terraform 101 (read first) | https://devopscert202.github.io/terraform-ansible-labs/terraform/html/terraform-101.html |
| Terraform AWS primer (read second) | https://devopscert202.github.io/terraform-ansible-labs/terraform/html/aws-primer.html |
| Terraform concepts (all topics) | https://devopscert202.github.io/terraform-ansible-labs/terraform/html/concepts.html |

The Terraform track lives at one flat depth (`terraform/html/`), so its four pages are two levels
below the site root, not three. The three former tier pages (`basic.html`, `intermediate.html`,
`advanced.html`) were replaced by the single `concepts.html`, which carries every topic from lab00
to lab24 in one sequence with a sticky topic index. All four pages are generated; never hand-edit
them. Regenerate before
pushing:

```bash
python3 curriculum/gen_terraform_html.py   # index, basic, intermediate, advanced
python3 curriculum/gen_terraform_101.py    # terraform-101
python3 curriculum/gen_aws_primer.py       # aws-primer
```

The shared nav lives in `curriculum/tf_style.py`, so a nav change means re-running all three
generators or some pages will publish with a stale nav.

`_config.yml` publishes the whole directory via `include: terraform/html` and preserves the
generated files with `keep_files: terraform/html`, so a new page in that directory is published
automatically with no config change.

## Local Jekyll preview (optional)

```bash
gem install github-pages
bundle exec jekyll serve   # if Gemfile added later
# or
jekyll serve --baseurl /terraform-ansible-labs
```
