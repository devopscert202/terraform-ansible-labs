# GitHub Pages setup

This repo publishes lab manuals, docs, and **offline HTML catalogs** via Jekyll on GitHub Pages.

**Site URL:** https://devopscert202.github.io/terraform-ansible-labs/

## One-time repo settings

1. Open **Settings → Pages** on GitHub
2. Under **Build and deployment**, set **Source** to **GitHub Actions**

## Deploy workflow

Pushes to `main` run [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), which:

1. Builds the site with Jekyll (`actions/jekyll-build-pages`)
2. Publishes HTML under `ansible/**/html/` and `terraform/**/html/` as static files
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

| Track | URL |
|-------|-----|
| Ansible essentials | https://devopscert202.github.io/terraform-ansible-labs/ansible/essentials/html/index.html |
| Ansible extended | https://devopscert202.github.io/terraform-ansible-labs/ansible/extended/html/index.html |
| Terraform essentials | https://devopscert202.github.io/terraform-ansible-labs/terraform/essentials/html/index.html |
| Terraform extended | https://devopscert202.github.io/terraform-ansible-labs/terraform/extended/html/index.html |

## Local Jekyll preview (optional)

```bash
gem install github-pages
bundle exec jekyll serve   # if Gemfile added later
# or
jekyll serve --baseurl /terraform-ansible-labs
```
