# Publish this code on GitHub

Create a new, empty repository under your personal GitHub account. Use the contents of this distribution as the repository root. Keep your full working backup separately.

From a terminal in this distribution's root folder:

```bash
git init
git add .
git status --short
```

Review the staged file list. It should contain source files, Markdown instructions, the header-only CSV template, `requirements.txt`, and `.gitignore`. It should not contain recording files, Excel workbooks, research results, or the full working ZIP.

Then create the initial commit:

```bash
git commit -m "Add noEMA analysis source and setup instructions"
git branch -M main
```

Connect the new empty repository using its own URL, then push:

```text
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_REPOSITORY_URL` with the actual URL shown by GitHub. These commands require Git and GitHub authentication. No account or remote repository is included in this ZIP.

The distribution includes a `.gitignore` file, which Finder may hide. Using `git add .` from this folder includes it. Avoid manually copying only the visible files and accidentally leaving it behind.

Original authorship notes are in `NOTICE.md`. No new project-wide license was selected during packaging. Confirm the original code's provenance before applying a license to the repository.
