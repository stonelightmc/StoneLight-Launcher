# Security Policy

Do not commit:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
```

`accounts.json` can contain Microsoft Minecraft access and refresh tokens.

This launcher is a public desktop client and uses PKCE. Do not add or publish a client secret.

Current public Client ID:

```text
28e78bd7-fb55-4391-b9dd-5d596a718c65
```

Redirect URI:

```text
http://localhost
```
