# Security Policy

## Do not commit private data

Do not commit:

```text
accounts.json
user_settings.json
instances.json
data/
*.log
.env
.env.*
secrets.*
*_token*
*_secret*
*_api_key*
```

`accounts.json` can contain Microsoft Minecraft access and refresh tokens.

Logs may contain local paths, usernames, account state, launch arguments, crash data or other information
that should not be published without review.

## OAuth and Microsoft authentication

This launcher is a public desktop client and uses PKCE. Do not add or publish a client secret.

Current public Client ID:

```text
28e78bd7-fb55-4391-b9dd-5d596a718c65
```

Redirect URI:

```text
http://localhost:8765/callback
```

The public Client ID is not a secret. Access tokens, refresh tokens and account files are secret.

## API keys and backend services

Do not commit or embed third-party API keys in the public desktop client, repository, releases, examples,
logs or screenshots.

This includes, but is not limited to:

```text
CurseForge API keys
backend service secrets
proxy shared secrets
private signing keys
private deployment tokens
```

CurseForge or other private API keys must be stored server-side, for example in backend environment
variables, and must not be returned to launcher clients.

Backend services should expose only limited endpoints needed by the launcher, validate requests, apply
reasonable rate limits, avoid unrestricted proxy behavior, and avoid logging secrets.

## Reporting security issues

If you discover a security issue, leaked token, leaked API key, unsafe backend behavior, or a release that
contains private data, contact the StoneLight project administrators privately instead of opening a public
issue.
