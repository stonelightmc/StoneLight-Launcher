# Localization

StoneLight Launcher v0.5.34 includes a first localization layer.

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


## v0.5.34 deeper pass

The localization layer now also translates:

```text
- CTkTextbox.insert() content
- common dynamic status fragments
- grey helper comments in instance/settings/login windows
- Microsoft OAuth callback success page
```

Some low-level technical logs from installers/loaders may still remain untranslated because they are intended for diagnostics.


## v0.5.34

Fixed localization of `CTkComboBox` values and selected text. This fixes the account selector placeholder:

```text
Нет аккаунтов
```

which is now translated as:

```text
No accounts
Немає акаунтів
Аккаунт жоқ
```


## v0.5.34

Fixed two localization edge cases:

```text
StoneLight Launcher
```

is protected as a brand name and is no longer translated as `StoneСвітла Launcher` or similar.

Instance type suffixes are now localized:

```text
официальная      → official / офіційна / ресми
пользовательская → custom / користувацька / пайдаланушы
```


## v0.5.34

Added localized theme names:

```text
Laconic / Лаконічна / Лаконикалық
Neon / Неон / Неон
Retro Future / Ретро-футуризм / Ретро-футуризм
```
