# Localization

StoneLight Launcher v0.5.26 includes a first localization layer.

Supported languages:

```text
en - English, default
uk - Ukrainian
kk - Kazakh
```

The selected language is stored in:

```text
user_settings.json
```

Translations are stored in:

```text
i18n.py
```

This first pass covers the main launcher UI, account controls, instance controls, global settings, common buttons, and Microsoft login window. Some dynamic diagnostic messages and low-level logs may still appear in Russian/English and can be migrated gradually.
