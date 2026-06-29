# GitHub publishing checklist

Before first push, check that these files are not present in the commit:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
```

Recommended publish flow:

```text
git init
git add .
git status
git commit -m "Initial StoneLight Launcher source"
git branch -M main
git remote add origin <your repository URL>
git push -u origin main
```

For releases, upload:

```text
StoneLightLauncher_v0_5_24_GitHub.zip
```
