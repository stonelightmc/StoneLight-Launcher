# Microsoft / Minecraft login setup

StoneLight Launcher uses Microsoft OAuth login through `minecraft-launcher-lib`.

## Configured values

```text
Application (client) ID:
28e78bd7-fb55-4391-b9dd-5d596a718c65

Redirect URI:
http://localhost:8765/callback

Client secret:
not used
```

## Required Azure settings

```text
Microsoft Entra ID
→ App registrations
→ StoneLight Launcher
→ Authentication
```

Add platform:

```text
Mobile and desktop applications
```

Add redirect URI:

```text
http://localhost:8765/callback
```

Enable:

```text
Advanced settings
→ Allow public client flows = Yes
```

## Minecraft API permission

New Azure apps must request permission to use the Minecraft API.

Form:

```text
https://aka.ms/mce-reviewappid
```

If permission is missing, login can fail with:

```text
AzureAppNotPermitted
Invalid app registration
403 Forbidden
```

## v0.6.69 account chooser

Microsoft login now adds:

```text
prompt=select_account
```

to the OAuth authorization URL. This asks Microsoft to show the account chooser instead of silently using the already active browser session, making it easier to add a second or third licensed account.

## v0.6.69 hotfix

Fixed a missing `urllib.parse` import used by the Microsoft account chooser URL patch.
