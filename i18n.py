
LANGUAGE_NAMES = {
    "en": "English",
    "uk": "Українська",
    "kk": "Қазақша",
}

LABEL_TO_LANGUAGE = {v: k for k, v in LANGUAGE_NAMES.items()}

_current_language = "en"


def normalize_language(language: str | None) -> str:
    language = (language or "en").strip().lower()
    if language in ("ua", "uk-ua", "ukrainian"):
        return "uk"
    if language in ("kz", "kk-kz", "kazakh"):
        return "kk"
    if language not in LANGUAGE_NAMES:
        return "en"
    return language


def set_language(language: str | None):
    global _current_language
    _current_language = normalize_language(language)


def get_language() -> str:
    return _current_language


def language_label(language: str | None = None) -> str:
    return LANGUAGE_NAMES.get(normalize_language(language or _current_language), LANGUAGE_NAMES["en"])


def language_code_from_label(label: str | None) -> str:
    return LABEL_TO_LANGUAGE.get((label or "").strip(), normalize_language(label))


TRANSLATIONS = {
    "en": {
        "Фильтр": "Filter",
        "Выбрать": "Select",
        "Отмена": "Cancel",
        "Всего: {len(self.items)}. Показано: {len(self.filtered_items)}.": "Total: {len(self.items)}. Shown: {len(self.filtered_items)}.",
        "Ничего не выбрано.": "Nothing selected.",
        "Выбор версии Minecraft": "Select Minecraft version",
        "Фильтр, например: 1.20.4 или 24w": "Filter, e.g. 1.20.4 or 24w",
        "Обновить список": "Refresh list",
        "Загрузка списка версий...": "Loading version list...",
        "Загрузка...": "Loading...",
        "включая снапшоты": "including snapshots",
        "только release": "release only",
        "Версия не выбрана.": "No version selected.",
        "Вход Microsoft / Minecraft": "Microsoft / Minecraft login",
        "1. Открыть вход Microsoft": "1. Open Microsoft login",
        "Вход в лицензионный Microsoft/Minecraft аккаунт": "Licensed Microsoft/Minecraft account login",
        "Вернуть localhost:8765": "Restore localhost:8765",
        "Резервный ручной режим: вставь redirect URL сюда, если автоперехват не сработал": "Manual fallback: paste the redirect URL here if auto-callback fails",
        "Вставить": "Paste",
        "Завершить вручную": "Complete manually",
        "Закрыть": "Close",
        "Не указан Microsoft Azure App Client ID.": "Microsoft Azure App Client ID is missing.",
        "Автоперехват поддерживает только localhost redirect URI.": "Auto-callback supports localhost redirect URI only.",
        "Открыт браузер Microsoft login.": "Microsoft login browser opened.",
        "После входа лаунчер должен завершить авторизацию автоматически.": "After login, the launcher should complete authorization automatically.",
        "Получен callback от Microsoft. Завершаю вход...": "Microsoft callback received. Completing login...",
        "Нет redirect URL. Повтори вход или вставь URL вручную.": "No redirect URL. Repeat login or paste the URL manually.",
        "Сначала нажми «Открыть вход Microsoft», чтобы создать secure login session.": "Press “Open Microsoft login” first to create a secure login session.",
        "Глобальные настройки запуска": "Global launch settings",
        "Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.": "These settings apply to every instance, including the official StoneLight instance.",
        "Минимум RAM, МБ": "Minimum RAM, MB",
        "Максимум RAM, МБ": "Maximum RAM, MB",
        "Запускать Minecraft в полноэкранном режиме": "Launch Minecraft in fullscreen mode",
        "Сохранить": "Save",
        "RAM должен быть числом, например 512 и 4096.": "RAM must be a number, for example 512 and 4096.",
        "Минимум RAM не должен быть меньше 256 МБ.": "Minimum RAM must not be below 256 MB.",
        "Максимум RAM не должен быть меньше 1024 МБ.": "Maximum RAM must not be below 1024 MB.",
        "Минимум RAM не может быть больше максимума.": "Minimum RAM cannot be greater than maximum RAM.",
        "Максимум RAM выглядит слишком большим. Проверь значение.": "Maximum RAM looks too high. Check the value.",
        "Создать сборку": "Create instance",
        "Новая сборка": "New instance",
        "Название": "Name",
        "Например: Test Fabric": "Example: Test Fabric",
        "Показывать снапшоты": "Show snapshots",
        "Модлоадер": "Mod loader",
        "Версия loader": "Loader version",
        "Загрузить": "Load",
        "Пустая сборка создаётся без модпака. Для vanilla список версий loader не нужен.": "An empty instance is created without a modpack. Vanilla does not need loader versions.",
        "Создать": "Create",
        "Для vanilla модлоадер не нужен.": "Vanilla does not need a mod loader.",
        "Запуск": "Launch",
        "Папки": "Folders",
        "Настройки": "Settings",
        "Консоль": "Console",
        "Аккаунт": "Account",
        "Параметры запуска": "Launch parameters",
        "Сборка": "Instance",
        "Глобальные параметры": "Global settings",
        "Память и полноэкранный режим задаются глобально для всех сборок. Java, Minecraft и модлоадер меняются на вкладке «Настройки».": "Memory and fullscreen mode are global for all instances. Java, Minecraft and loader are changed on the Settings tab.",
        "Играть": "Play",
        "Обновить": "Update",
        "Остановить": "Stop",
        "Папка сборки": "Instance folder",
        "Проверить Forge": "Check Forge",
        "Готово.": "Ready.",
        "Выбери папку выше.": "Choose a folder above.",
        "Открыть выбранную папку": "Open selected folder",
        "Настройки сборки": "Instance settings",
        "Java этой сборки": "Java for this instance",
        "auto = скачать/использовать portable Java": "auto = download/use portable Java",
        "Установить рекомендуемую Java": "Install recommended Java",
        "Установить выбранный preset": "Install selected preset",
        "Добавлять сервер в servers.dat": "Add server to servers.dat",
        "Сохранить настройки сборки": "Save instance settings",
        "Очистить": "Clear",
        "Открыть launcher.log": "Open launcher.log",
        "Открыть папку logs": "Open logs folder",
        "Официальная сборка StoneLight защищена от редактирования версии, loader и модпака.": "The official StoneLight instance is protected from editing version, loader and modpack.",
        "После смены версии/loader нажми «Обновить / установить», чтобы скачать Minecraft и установить модлоадер.": "After changing version/loader, press “Update / install” to download Minecraft and install the loader.",
        "Вывод игры появляется во вкладке «Консоль». Для полного вывода лучше указывать java.exe, а не javaw.exe.": "Game output appears on the Console tab. For full output, use java.exe instead of javaw.exe.",
        "Нет аккаунтов": "No accounts",
        "Нет сборок": "No instances",
        "Выбранная": "Selected",
        "Выбранный": "Selected",
        "Открыть окно сборки": "Open instance window",
        "Удалить сборку": "Delete instance",
        "Папка": "Folder",
        "Войти Microsoft": "Microsoft login",
        "Обновить лицензию": "Refresh license",
        "Удалить аккаунт": "Delete account",
        "Offline-ник": "Offline nickname",
        "Доступно после входа в лицензионный аккаунт": "Available after licensed account login",
        "Добавить offline": "Add offline",
        "Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.": "Offline accounts are allowed only after logging into at least one licensed account.",
        "Java выбранной сборки": "Java for selected instance",
        "Глобальные настройки запуска": "Global launch settings",
        "Играть выбранную": "Play selected",
        "Обновить / установить": "Update / install",
        "Открыть лог": "Open log",
        "Готов к запуску.": "Ready to launch.",
        "Добро пожаловать в StoneLight Launcher v0.5.31\n": "Welcome to StoneLight Launcher v0.5.31\n",
        "полноэкранный": "fullscreen",
        "оконный": "windowed",
        "Полноэкранный": "Fullscreen",
        "Оконный": "Windowed",
        "Режим": "Mode",
        "не выбран": "not selected",
        "Автоматически по версии Minecraft": "Automatically by Minecraft version",
        "Используется": "Used",
        "Рекомендация": "Recommendation",
        "Рекомендуется: ": "Recommended: ",
        "Глобально для всех сборок: RAM {min}–{max} МБ, режим: {mode}.": "Global for all instances: RAM {min}–{max} MB, mode: {mode}.",
        "Пустая vanilla-сборка": "Empty vanilla instance",
        "Пустая сборка с loader: {loader}": "Empty instance with loader: {loader}",
        "StoneLight: модпак + сервер в списке + защита от удаления": "StoneLight: modpack + server in list + deletion protection",
        "Нет выбранной сборки.": "No instance selected.",
        "Официальную сборку StoneLight нельзя удалить.": "The official StoneLight instance cannot be deleted.",
        "Нет выбранного аккаунта. Войди в лицензионный Microsoft/Minecraft аккаунт.": "No account selected. Log into a licensed Microsoft/Minecraft account.",
        "Не указан Microsoft Azure App Client ID. Нажми «Войти Microsoft» и укажи Client ID.": "Microsoft Azure App Client ID is missing. Press “Microsoft login” and enter Client ID.",
        "Обновление нужно только для лицензионных Microsoft-аккаунтов.": "Refresh is needed only for licensed Microsoft accounts.",
        "Выбери java.exe или javaw.exe": "Choose java.exe or javaw.exe",
        "Выбери java.exe или javaw.exe для этой сборки": "Choose java.exe or javaw.exe for this instance",
        "Неизвестный тип аккаунта.": "Unknown account type.",
        "ОШИБКА: ": "ERROR: ",
        "Уже выполняется задача.": "A task is already running.",
        "Сборка обновлена/установлена.": "Instance updated/installed.",
        "Ручной установщик нужен только для Forge-сборок.": "Manual installer is only needed for Forge instances.",
        "Ручной Forge Installer": "Manual Forge Installer",
        "Проверка Forge нужна только для Forge-сборок.": "Forge check is only needed for Forge instances.",
        "Проверка Forge завершена.": "Forge check completed.",
        "Папка пустая.": "Folder is empty.",
        "Для этого preset нельзя определить версию Java.": "Cannot determine Java version for this preset.",
        "Язык": "Language",
        "GitHub": "GitHub",
        "Open GitHub": "Open GitHub",
        "Language changed.": "Language changed.",
    },
    "uk": {
        "Фильтр": "Фільтр",
        "Выбрать": "Вибрати",
        "Отмена": "Скасувати",
        "Ничего не выбрано.": "Нічого не вибрано.",
        "Выбор версии Minecraft": "Вибір версії Minecraft",
        "Фильтр, например: 1.20.4 или 24w": "Фільтр, наприклад: 1.20.4 або 24w",
        "Обновить список": "Оновити список",
        "Загрузка списка версий...": "Завантаження списку версій...",
        "Загрузка...": "Завантаження...",
        "Вход Microsoft / Minecraft": "Вхід Microsoft / Minecraft",
        "1. Открыть вход Microsoft": "1. Відкрити вхід Microsoft",
        "Вход в лицензионный Microsoft/Minecraft аккаунт": "Вхід у ліцензійний Microsoft/Minecraft акаунт",
        "Вернуть localhost:8765": "Повернути localhost:8765",
        "Резервный ручной режим: вставь redirect URL сюда, если автоперехват не сработал": "Резервний ручний режим: встав redirect URL сюди, якщо автоперехоплення не спрацювало",
        "Вставить": "Вставити",
        "Завершить вручную": "Завершити вручну",
        "Закрыть": "Закрити",
        "Открыт браузер Microsoft login.": "Відкрито браузер входу Microsoft.",
        "После входа лаунчер должен завершить авторизацию автоматически.": "Після входу лаунчер має завершити авторизацію автоматично.",
        "Получен callback от Microsoft. Завершаю вход...": "Отримано callback від Microsoft. Завершую вхід...",
        "Глобальные настройки запуска": "Глобальні налаштування запуску",
        "Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.": "Ці параметри застосовуються до всіх збірок без винятку, включно з офіційною збіркою StoneLight.",
        "Минимум RAM, МБ": "Мінімум RAM, МБ",
        "Максимум RAM, МБ": "Максимум RAM, МБ",
        "Запускать Minecraft в полноэкранном режиме": "Запускати Minecraft у повноекранному режимі",
        "Сохранить": "Зберегти",
        "Создать сборку": "Створити збірку",
        "Новая сборка": "Нова збірка",
        "Название": "Назва",
        "Например: Test Fabric": "Наприклад: Test Fabric",
        "Показывать снапшоты": "Показувати снапшоти",
        "Модлоадер": "Модлоадер",
        "Версия loader": "Версія loader",
        "Загрузить": "Завантажити",
        "Создать": "Створити",
        "Для vanilla модлоадер не нужен.": "Для vanilla модлоадер не потрібен.",
        "Запуск": "Запуск",
        "Папки": "Папки",
        "Настройки": "Налаштування",
        "Консоль": "Консоль",
        "Аккаунт": "Акаунт",
        "Параметры запуска": "Параметри запуску",
        "Сборка": "Збірка",
        "Глобальные параметры": "Глобальні параметри",
        "Играть": "Грати",
        "Обновить": "Оновити",
        "Остановить": "Зупинити",
        "Папка сборки": "Папка збірки",
        "Проверить Forge": "Перевірити Forge",
        "Готово.": "Готово.",
        "Открыть выбранную папку": "Відкрити вибрану папку",
        "Настройки сборки": "Налаштування збірки",
        "Java этой сборки": "Java цієї збірки",
        "Установить рекомендуемую Java": "Встановити рекомендовану Java",
        "Установить выбранный preset": "Встановити вибраний preset",
        "Добавлять сервер в servers.dat": "Додавати сервер у servers.dat",
        "Сохранить настройки сборки": "Зберегти налаштування збірки",
        "Очистить": "Очистити",
        "Открыть launcher.log": "Відкрити launcher.log",
        "Открыть папку logs": "Відкрити папку logs",
        "Нет аккаунтов": "Немає акаунтів",
        "Нет сборок": "Немає збірок",
        "Выбранная": "Вибрана",
        "Выбранный": "Вибраний",
        "Открыть окно сборки": "Відкрити вікно збірки",
        "Удалить сборку": "Видалити збірку",
        "Папка": "Папка",
        "Войти Microsoft": "Увійти Microsoft",
        "Обновить лицензию": "Оновити ліцензію",
        "Удалить аккаунт": "Видалити акаунт",
        "Offline-ник": "Offline-нік",
        "Доступно после входа в лицензионный аккаунт": "Доступно після входу в ліцензійний акаунт",
        "Добавить offline": "Додати offline",
        "Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.": "Offline-акаунти дозволені лише після входу хоча б в один ліцензійний акаунт.",
        "Java выбранной сборки": "Java вибраної збірки",
        "Играть выбранную": "Грати вибрану",
        "Обновить / установить": "Оновити / встановити",
        "Открыть лог": "Відкрити лог",
        "Готов к запуску.": "Готовий до запуску.",
        "Добро пожаловать в StoneLight Launcher v0.5.31\n": "Ласкаво просимо до StoneLight Launcher v0.5.31\n",
        "полноэкранный": "повноекранний",
        "оконный": "віконний",
        "Полноэкранный": "Повноекранний",
        "Оконный": "Віконний",
        "Режим": "Режим",
        "не выбран": "не вибрано",
        "Используется": "Використовується",
        "Рекомендация": "Рекомендація",
        "Рекомендуется: ": "Рекомендовано: ",
        "Глобально для всех сборок: RAM {min}–{max} МБ, режим: {mode}.": "Глобально для всіх збірок: RAM {min}–{max} МБ, режим: {mode}.",
        "Пустая vanilla-сборка": "Порожня vanilla-збірка",
        "Пустая сборка с loader: {loader}": "Порожня збірка з loader: {loader}",
        "StoneLight: модпак + сервер в списке + защита от удаления": "StoneLight: модпак + сервер у списку + захист від видалення",
        "Нет выбранной сборки.": "Не вибрано збірку.",
        "Официальную сборку StoneLight нельзя удалить.": "Офіційну збірку StoneLight не можна видалити.",
        "Нет выбранного аккаунта. Войди в лицензионный Microsoft/Minecraft аккаунт.": "Не вибрано акаунт. Увійди в ліцензійний Microsoft/Minecraft акаунт.",
        "Неизвестный тип аккаунта.": "Невідомий тип акаунта.",
        "ОШИБКА: ": "ПОМИЛКА: ",
        "Уже выполняется задача.": "Завдання вже виконується.",
        "Сборка обновлена/установлена.": "Збірку оновлено/встановлено.",
        "Папка пустая.": "Папка порожня.",
        "Язык": "Мова",
        "Language": "Мова",
        "Open GitHub": "Відкрити GitHub",
        "Language changed.": "Мову змінено.",
    },
    "kk": {
        "Фильтр": "Сүзгі",
        "Выбрать": "Таңдау",
        "Отмена": "Бас тарту",
        "Ничего не выбрано.": "Ештеңе таңдалмады.",
        "Выбор версии Minecraft": "Minecraft нұсқасын таңдау",
        "Фильтр, например: 1.20.4 или 24w": "Сүзгі, мысалы: 1.20.4 немесе 24w",
        "Обновить список": "Тізімді жаңарту",
        "Загрузка списка версий...": "Нұсқалар тізімі жүктелуде...",
        "Загрузка...": "Жүктелуде...",
        "Вход Microsoft / Minecraft": "Microsoft / Minecraft кіру",
        "1. Открыть вход Microsoft": "1. Microsoft кіруін ашу",
        "Вход в лицензионный Microsoft/Minecraft аккаунт": "Лицензиялық Microsoft/Minecraft аккаунтына кіру",
        "Вернуть localhost:8765": "localhost:8765 қайтару",
        "Резервный ручной режим: вставь redirect URL сюда, если автоперехват не сработал": "Қолмен резерв режимі: автотосу істемесе, redirect URL осында қой",
        "Вставить": "Қою",
        "Завершить вручную": "Қолмен аяқтау",
        "Закрыть": "Жабу",
        "Открыт браузер Microsoft login.": "Microsoft login браузері ашылды.",
        "После входа лаунчер должен завершить авторизацию автоматически.": "Кіргеннен кейін лаунчер авторизацияны автоматты аяқтауы керек.",
        "Получен callback от Microsoft. Завершаю вход...": "Microsoft callback алынды. Кіру аяқталуда...",
        "Глобальные настройки запуска": "Жалпы іске қосу баптаулары",
        "Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.": "Бұл параметрлер барлық жинақтарға қолданылады, соның ішінде ресми StoneLight жинағына да.",
        "Минимум RAM, МБ": "Ең аз RAM, МБ",
        "Максимум RAM, МБ": "Ең көп RAM, МБ",
        "Запускать Minecraft в полноэкранном режиме": "Minecraft толық экранда іске қосылсын",
        "Сохранить": "Сақтау",
        "Создать сборку": "Жинақ жасау",
        "Новая сборка": "Жаңа жинақ",
        "Название": "Атауы",
        "Например: Test Fabric": "Мысалы: Test Fabric",
        "Показывать снапшоты": "Снапшоттарды көрсету",
        "Модлоадер": "Модлоадер",
        "Версия loader": "Loader нұсқасы",
        "Загрузить": "Жүктеу",
        "Создать": "Жасау",
        "Для vanilla модлоадер не нужен.": "Vanilla үшін модлоадер қажет емес.",
        "Запуск": "Іске қосу",
        "Папки": "Қалталар",
        "Настройки": "Баптаулар",
        "Консоль": "Консоль",
        "Аккаунт": "Аккаунт",
        "Параметры запуска": "Іске қосу параметрлері",
        "Сборка": "Жинақ",
        "Глобальные параметры": "Жалпы параметрлер",
        "Играть": "Ойнау",
        "Обновить": "Жаңарту",
        "Остановить": "Тоқтату",
        "Папка сборки": "Жинақ қалтасы",
        "Проверить Forge": "Forge тексеру",
        "Готово.": "Дайын.",
        "Открыть выбранную папку": "Таңдалған қалтаны ашу",
        "Настройки сборки": "Жинақ баптаулары",
        "Java этой сборки": "Осы жинақтың Java-сы",
        "Установить рекомендуемую Java": "Ұсынылған Java орнату",
        "Установить выбранный preset": "Таңдалған preset орнату",
        "Добавлять сервер в servers.dat": "Серверді servers.dat файлына қосу",
        "Сохранить настройки сборки": "Жинақ баптауларын сақтау",
        "Очистить": "Тазалау",
        "Открыть launcher.log": "launcher.log ашу",
        "Открыть папку logs": "logs қалтасын ашу",
        "Нет аккаунтов": "Аккаунт жоқ",
        "Нет сборок": "Жинақ жоқ",
        "Выбранная": "Таңдалған",
        "Выбранный": "Таңдалған",
        "Открыть окно сборки": "Жинақ терезесін ашу",
        "Удалить сборку": "Жинақты жою",
        "Папка": "Қалта",
        "Войти Microsoft": "Microsoft кіру",
        "Обновить лицензию": "Лицензияны жаңарту",
        "Удалить аккаунт": "Аккаунтты жою",
        "Offline-ник": "Offline ник",
        "Доступно после входа в лицензионный аккаунт": "Лицензиялық аккаунтқа кіргеннен кейін қолжетімді",
        "Добавить offline": "Offline қосу",
        "Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.": "Offline аккаунттар кемінде бір лицензиялық аккаунт кіргеннен кейін ғана рұқсат.",
        "Java выбранной сборки": "Таңдалған жинақтың Java-сы",
        "Играть выбранную": "Таңдалғанды ойнау",
        "Обновить / установить": "Жаңарту / орнату",
        "Открыть лог": "Логты ашу",
        "Готов к запуску.": "Іске қосуға дайын.",
        "Добро пожаловать в StoneLight Launcher v0.5.31\n": "StoneLight Launcher v0.5.31-ға қош келдіңіз\n",
        "полноэкранный": "толық экран",
        "оконный": "терезелік",
        "Полноэкранный": "Толық экран",
        "Оконный": "Терезелік",
        "Режим": "Режим",
        "не выбран": "таңдалмаған",
        "Используется": "Қолданылады",
        "Рекомендация": "Ұсыныс",
        "Рекомендуется: ": "Ұсынылады: ",
        "Глобально для всех сборок: RAM {min}–{max} МБ, режим: {mode}.": "Барлық жинақтарға ортақ: RAM {min}–{max} МБ, режим: {mode}.",
        "Пустая vanilla-сборка": "Бос vanilla жинағы",
        "Пустая сборка с loader: {loader}": "Loader бар бос жинақ: {loader}",
        "StoneLight: модпак + сервер в списке + защита от удаления": "StoneLight: модпак + тізімдегі сервер + жоюдан қорғау",
        "Нет выбранной сборки.": "Жинақ таңдалмаған.",
        "Официальную сборку StoneLight нельзя удалить.": "Ресми StoneLight жинағын жоюға болмайды.",
        "Нет выбранного аккаунта. Войди в лицензионный Microsoft/Minecraft аккаунт.": "Аккаунт таңдалмаған. Лицензиялық Microsoft/Minecraft аккаунтына кір.",
        "Неизвестный тип аккаунта.": "Белгісіз аккаунт түрі.",
        "ОШИБКА: ": "ҚАТЕ: ",
        "Уже выполняется задача.": "Тапсырма орындалып жатыр.",
        "Сборка обновлена/установлена.": "Жинақ жаңартылды/орнатылды.",
        "Папка пустая.": "Қалта бос.",
        "Язык": "Тіл",
        "Language": "Тіл",
        "Open GitHub": "GitHub ашу",
        "Language changed.": "Тіл өзгертілді.",
    }
}

# Extra UI translations added in v0.5.31.
# These cover helper comments, small grey hints, dynamic status text, and common diagnostic fragments.
SUPPLEMENTAL_TRANSLATIONS = {'en': {'\n\nЛаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.\nПосле установки в открывшемся окне нажми «Проверить Forge» или «Играть».': '\n'
                                                                                                                                                                          '\n'
                                                                                                                                                                          'The '
                                                                                                                                                                          'launcher '
                                                                                                                                                                          'will '
                                                                                                                                                                          'create '
                                                                                                                                                                          'launcher_profiles.json '
                                                                                                                                                                          'in '
                                                                                                                                                                          'advance '
                                                                                                                                                                          'so '
                                                                                                                                                                          'old '
                                                                                                                                                                          'Forge '
                                                                                                                                                                          'accepts '
                                                                                                                                                                          'this '
                                                                                                                                                                          'folder.\n'
                                                                                                                                                                          'After '
                                                                                                                                                                          'installing, '
                                                                                                                                                                          'click '
                                                                                                                                                                          '“Check '
                                                                                                                                                                          'Forge” '
                                                                                                                                                                          'or '
                                                                                                                                                                          '“Play” '
                                                                                                                                                                          'in '
                                                                                                                                                                          'the '
                                                                                                                                                                          'launcher.',
        'Сейчас откроется Forge Installer.\n\nВ нём выбери Install client и укажи папку сборки:\n\n': 'Forge Installer will open now.\n'
                                                                                                      '\n'
                                                                                                      'Choose Install client and select this instance folder:\n'
                                                                                                      '\n',
        'Лаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.': 'The launcher will create launcher_profiles.json in advance so old '
                                                                                            'Forge accepts this folder.',
        'После установки в открывшемся окне нажми «Проверить Forge» или «Играть».': 'After installing, click “Check Forge” or “Play” in the launcher.',
        'Путь установки должен быть именно папкой сборки выше, а не обычной .minecraft.': 'The install path must be the instance folder above, not the regular '
                                                                                          '.minecraft folder.',
        'В Forge Installer выбери: Install client.': 'In Forge Installer choose: Install client.',
        'Лаунчер больше не ждёт закрытия Forge Installer, чтобы GUI не зависал. Установи Forge в открывшемся окне, затем вернись в лаунчер.': 'The launcher no '
                                                                                                                                              'longer waits '
                                                                                                                                              'for Forge '
                                                                                                                                              'Installer to '
                                                                                                                                              'close, so the '
                                                                                                                                              'GUI does not '
                                                                                                                                              'freeze. Install '
                                                                                                                                              'Forge in the '
                                                                                                                                              'opened window, '
                                                                                                                                              'then return to '
                                                                                                                                              'the launcher.',
        'Forge Installer запущен. Заверши установку в его окне, затем нажми «Проверить Forge».': 'Forge Installer started. Finish installation in its window, '
                                                                                                 'then click “Check Forge”.',
        'Forge Installer запущен. Если окно не появилось, открой fallback .cmd из data\\cache\\forge_installers. После установки нажми «Проверить Forge» или «Играть».': 'Forge '
                                                                                                                                                                         'Installer '
                                                                                                                                                                         'started. '
                                                                                                                                                                         'If '
                                                                                                                                                                         'the '
                                                                                                                                                                         'window '
                                                                                                                                                                         'did '
                                                                                                                                                                         'not '
                                                                                                                                                                         'appear, '
                                                                                                                                                                         'open '
                                                                                                                                                                         'the '
                                                                                                                                                                         'fallback '
                                                                                                                                                                         '.cmd '
                                                                                                                                                                         'from '
                                                                                                                                                                         'data\\cache\\forge_installers. '
                                                                                                                                                                         'After '
                                                                                                                                                                         'installation, '
                                                                                                                                                                         'click '
                                                                                                                                                                         '“Check '
                                                                                                                                                                         'Forge” '
                                                                                                                                                                         'or '
                                                                                                                                                                         '“Play”.',
        'Пароль в лаунчер не вводится: вход выполняется в браузере Microsoft. После успешного входа лаунчер автоматически примет ответ через локальный callback.': 'Do '
                                                                                                                                                                   'not '
                                                                                                                                                                   'enter '
                                                                                                                                                                   'your '
                                                                                                                                                                   'password '
                                                                                                                                                                   'in '
                                                                                                                                                                   'the '
                                                                                                                                                                   'launcher: '
                                                                                                                                                                   'login '
                                                                                                                                                                   'happens '
                                                                                                                                                                   'in '
                                                                                                                                                                   'the '
                                                                                                                                                                   'Microsoft '
                                                                                                                                                                   'browser '
                                                                                                                                                                   'page. '
                                                                                                                                                                   'After '
                                                                                                                                                                   'successful '
                                                                                                                                                                   'login, '
                                                                                                                                                                   'the '
                                                                                                                                                                   'launcher '
                                                                                                                                                                   'will '
                                                                                                                                                                   'receive '
                                                                                                                                                                   'the '
                                                                                                                                                                   'response '
                                                                                                                                                                   'automatically '
                                                                                                                                                                   'through '
                                                                                                                                                                   'the '
                                                                                                                                                                   'local '
                                                                                                                                                                   'callback.',
        'Готово. Нажми «Открыть вход Microsoft». Локальный callback будет запущен автоматически.\n': 'Ready. Click “Open Microsoft login”. The local callback '
                                                                                                     'will start automatically.\n',
        'Локальный callback запущен: ': 'Local callback started: ',
        'Вход завершён': 'Login completed',
        'Можно вернуться в StoneLight Launcher. Это окно браузера можно закрыть.': 'You can return to StoneLight Launcher. This browser tab can be closed.',
        '--- История вывода запущенной сборки ---': '--- Running instance output history ---',
        'Консоль сборки готова.\n': 'Instance console is ready.\n',
        'Java сборки': 'Instance Java',
        'Сборка: ': 'Instance: ',
        'Сборка не найдена.': 'Instance not found.',
        'Добавлен аккаунт: ': 'Added account: ',
        'Ошибка завершения входа: ': 'Login completion error: ',
        'Не удалось вставить из буфера: ': 'Could not paste from clipboard: ',
        'Не удалось открыть лог: ': 'Could not open log: ',
        'Не удалось открыть папку сборки: ': 'Could not open instance folder: ',
        'Ошибка чтения папки: ': 'Folder read error: ',
        'Ошибка: ': 'Error: ',
        'Не удалось запустить локальный callback-сервер на порту ': 'Could not start local callback server on port ',
        '. Возможно, порт занят или заблокирован. Детали: ': '. The port may be busy or blocked. Details: ',
        'Фильтр версии loader': 'Loader version filter',
        'Версии ': 'Versions ',
        'Загружаю версии ': 'Loading versions ',
        'Найдено версий ': 'Found versions ',
        'Не найдено автоматически поддерживаемых версий ': 'No automatically supported versions found for ',
        'Всего версий: ': 'Total versions: ',
        'Всего: ': 'Total: ',
        '. Показано: ': '. Shown: ',
        'версии': 'versions',
        'для Minecraft ': 'for Minecraft ',
        ' для Minecraft ': ' for Minecraft ',
        ' для ': ' for ',
        ' из списка? Папка на диске не удаляется.': ' from the list? The folder on disk will not be deleted.',
        'Удалить сборку ': 'Delete instance ',
        'Удалить аккаунт ': 'Delete account ',
        ' установлена и сохранена для сборки: ': ' installed and saved for instance: ',
        '. Preset auto скачает/использует portable Java в data/java.': '. The auto preset will download/use portable Java in data/java.',
        '. Выбери нужную в открытом списке.': '. Choose the needed one in the opened list.',
        '. Можно оставить поле пустым: лаунчер попробует взять последнюю доступную, если loader это поддерживает.': '. You may leave the field empty: the '
                                                                                                                    'launcher will try to use the latest '
                                                                                                                    'available version if the loader supports '
                                                                                                                    'it.',
        'Рекомендация для ': 'Recommendation for ',
        'Рекомендация Java': 'Java recommendation',
        'Автоматически по версии Minecraft': 'Automatically by Minecraft version',
        'Вывод игры появляется во вкладке «Консоль». Для полного вывода лучше указывать java.exe, а не javaw.exe.': 'Game output appears on the “Console” tab. '
                                                                                                                    'For full output, use java.exe instead of '
                                                                                                                    'javaw.exe.',
        'Память и полноэкранный режим задаются глобально для всех сборок. Java, Minecraft и модлоадер меняются на вкладке «Настройки».': 'Memory and '
                                                                                                                                         'fullscreen mode are '
                                                                                                                                         'global for all '
                                                                                                                                         'instances. Java, '
                                                                                                                                         'Minecraft, and the '
                                                                                                                                         'mod loader are '
                                                                                                                                         'changed on the '
                                                                                                                                         '“Settings” tab.',
        'Пустая сборка создаётся без модпака. Для vanilla список версий loader не нужен.': 'An empty instance is created without a modpack. Vanilla does not '
                                                                                           'need a loader version list.',
        'Официальная сборка StoneLight защищена от редактирования версии, loader и модпака.': 'The official StoneLight instance is protected from editing its '
                                                                                              'version, loader, and modpack.',
        'После смены версии/loader нажми «Обновить / установить», чтобы скачать Minecraft и установить модлоадер.': 'After changing the version/loader, click '
                                                                                                                    '“Update / install” to download Minecraft '
                                                                                                                    'and install the loader.',
        'Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.': 'These settings apply to every instance, including '
                                                                                                            'the official StoneLight instance.',
        'Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.': 'Offline accounts are allowed only after logging into at least '
                                                                                              'one licensed account.',
        'Доступно после входа в лицензионный аккаунт': 'Available after licensed account login',
        'Выбери папку выше.': 'Choose a folder above.',
        'Папка пустая.': 'The folder is empty.',
        'Готово.': 'Ready.',
        'Готов к запуску.': 'Ready to launch.',
        'Minecraft запущен.': 'Minecraft started.',
        'Repair завершён.': 'Repair completed.',
        'Проверка Forge завершена.': 'Forge check completed.',
        'Сборка обновлена/установлена.': 'Instance updated/installed.',
        'ОШИБКА: ': 'ERROR: ',
        ' МБ': ' MB',
        '. Режим: ': '. Mode: '},
 'uk': {'\n\nЛаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.\nПосле установки в открывшемся окне нажми «Проверить Forge» или «Играть».': '\n'
                                                                                                                                                                          '\n'
                                                                                                                                                                          'Лаунчер '
                                                                                                                                                                          'заздалегідь '
                                                                                                                                                                          'створить '
                                                                                                                                                                          'launcher_profiles.json, '
                                                                                                                                                                          'щоб '
                                                                                                                                                                          'старий '
                                                                                                                                                                          'Forge '
                                                                                                                                                                          'прийняв '
                                                                                                                                                                          'цю '
                                                                                                                                                                          'папку.\n'
                                                                                                                                                                          'Після '
                                                                                                                                                                          'встановлення '
                                                                                                                                                                          'натисни '
                                                                                                                                                                          '«Перевірити '
                                                                                                                                                                          'Forge» '
                                                                                                                                                                          'або '
                                                                                                                                                                          '«Грати».',
        'Сейчас откроется Forge Installer.\n\nВ нём выбери Install client и укажи папку сборки:\n\n': 'Зараз відкриється Forge Installer.\n'
                                                                                                      '\n'
                                                                                                      'У ньому вибери Install client і вкажи папку збірки:\n'
                                                                                                      '\n',
        'Лаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.': 'Лаунчер заздалегідь створить launcher_profiles.json, щоб старий '
                                                                                            'Forge прийняв папку.',
        'После установки в открывшемся окне нажми «Проверить Forge» или «Играть».': 'Після встановлення натисни «Перевірити Forge» або «Грати».',
        'Путь установки должен быть именно папкой сборки выше, а не обычной .minecraft.': 'Шлях встановлення має бути саме папкою збірки вище, а не звичайною '
                                                                                          '.minecraft.',
        'В Forge Installer выбери: Install client.': 'У Forge Installer вибери: Install client.',
        'Лаунчер больше не ждёт закрытия Forge Installer, чтобы GUI не зависал. Установи Forge в открывшемся окне, затем вернись в лаунчер.': 'Лаунчер більше '
                                                                                                                                              'не чекає '
                                                                                                                                              'закриття Forge '
                                                                                                                                              'Installer, щоб '
                                                                                                                                              'інтерфейс не '
                                                                                                                                              'зависав. '
                                                                                                                                              'Встанови Forge '
                                                                                                                                              'у відкритому '
                                                                                                                                              'вікні, потім '
                                                                                                                                              'повернися в '
                                                                                                                                              'лаунчер.',
        'Forge Installer запущен. Заверши установку в его окне, затем нажми «Проверить Forge».': 'Forge Installer запущено. Заверши встановлення в його вікні, '
                                                                                                 'потім натисни «Перевірити Forge».',
        'Forge Installer запущен. Если окно не появилось, открой fallback .cmd из data\\cache\\forge_installers. После установки нажми «Проверить Forge» или «Играть».': 'Forge '
                                                                                                                                                                         'Installer '
                                                                                                                                                                         'запущено. '
                                                                                                                                                                         'Якщо '
                                                                                                                                                                         'вікно '
                                                                                                                                                                         'не '
                                                                                                                                                                         'з’явилось, '
                                                                                                                                                                         'відкрий '
                                                                                                                                                                         'fallback '
                                                                                                                                                                         '.cmd '
                                                                                                                                                                         'з '
                                                                                                                                                                         'data\\cache\\forge_installers. '
                                                                                                                                                                         'Після '
                                                                                                                                                                         'встановлення '
                                                                                                                                                                         'натисни '
                                                                                                                                                                         '«Перевірити '
                                                                                                                                                                         'Forge» '
                                                                                                                                                                         'або '
                                                                                                                                                                         '«Грати».',
        'Пароль в лаунчер не вводится: вход выполняется в браузере Microsoft. После успешного входа лаунчер автоматически примет ответ через локальный callback.': 'Пароль '
                                                                                                                                                                   'у '
                                                                                                                                                                   'лаунчер '
                                                                                                                                                                   'не '
                                                                                                                                                                   'вводиться: '
                                                                                                                                                                   'вхід '
                                                                                                                                                                   'відбувається '
                                                                                                                                                                   'у '
                                                                                                                                                                   'браузері '
                                                                                                                                                                   'Microsoft. '
                                                                                                                                                                   'Після '
                                                                                                                                                                   'успішного '
                                                                                                                                                                   'входу '
                                                                                                                                                                   'лаунчер '
                                                                                                                                                                   'автоматично '
                                                                                                                                                                   'прийме '
                                                                                                                                                                   'відповідь '
                                                                                                                                                                   'через '
                                                                                                                                                                   'локальний '
                                                                                                                                                                   'callback.',
        'Готово. Нажми «Открыть вход Microsoft». Локальный callback будет запущен автоматически.\n': 'Готово. Натисни «Відкрити вхід Microsoft». Локальний '
                                                                                                     'callback запуститься автоматично.\n',
        'Локальный callback запущен: ': 'Локальний callback запущено: ',
        'Вход завершён': 'Вхід завершено',
        'Можно вернуться в StoneLight Launcher. Это окно браузера можно закрыть.': 'Можна повернутися до StoneLight Launcher. Це вікно браузера можна закрити.',
        '--- История вывода запущенной сборки ---': '--- Історія виводу запущеної збірки ---',
        'Консоль сборки готова.\n': 'Консоль збірки готова.\n',
        'Java сборки': 'Java збірки',
        'Сборка: ': 'Збірка: ',
        'Сборка не найдена.': 'Збірку не знайдено.',
        'Добавлен аккаунт: ': 'Додано акаунт: ',
        'Ошибка завершения входа: ': 'Помилка завершення входу: ',
        'Не удалось вставить из буфера: ': 'Не вдалося вставити з буфера: ',
        'Не удалось открыть лог: ': 'Не вдалося відкрити лог: ',
        'Не удалось открыть папку сборки: ': 'Не вдалося відкрити папку збірки: ',
        'Ошибка чтения папки: ': 'Помилка читання папки: ',
        'Ошибка: ': 'Помилка: ',
        'Не удалось запустить локальный callback-сервер на порту ': 'Не вдалося запустити локальний callback-сервер на порту ',
        '. Возможно, порт занят или заблокирован. Детали: ': '. Можливо, порт зайнятий або заблокований. Деталі: ',
        'Фильтр версии loader': 'Фільтр версії loader',
        'Версии ': 'Версії ',
        'Загружаю версии ': 'Завантажую версії ',
        'Найдено версий ': 'Знайдено версій ',
        'Не найдено автоматически поддерживаемых версий ': 'Не знайдено автоматично підтримуваних версій ',
        'Всего версий: ': 'Усього версій: ',
        'Всего: ': 'Усього: ',
        '. Показано: ': '. Показано: ',
        'версии': 'версії',
        'для Minecraft ': 'для Minecraft ',
        ' для Minecraft ': ' для Minecraft ',
        ' для ': ' для ',
        ' из списка? Папка на диске не удаляется.': ' зі списку? Папка на диску не видаляється.',
        'Удалить сборку ': 'Видалити збірку ',
        'Удалить аккаунт ': 'Видалити акаунт ',
        ' установлена и сохранена для сборки: ': ' встановлена й збережена для збірки: ',
        '. Preset auto скачает/использует portable Java в data/java.': '. Preset auto завантажить/використає portable Java у data/java.',
        '. Выбери нужную в открытом списке.': '. Вибери потрібну у відкритому списку.',
        '. Можно оставить поле пустым: лаунчер попробует взять последнюю доступную, если loader это поддерживает.': '. Можна залишити поле порожнім: лаунчер '
                                                                                                                    'спробує взяти останню доступну, якщо '
                                                                                                                    'loader це підтримує.',
        'Рекомендация для ': 'Рекомендація для ',
        'Рекомендация Java': 'Рекомендація Java',
        'Автоматически по версии Minecraft': 'Автоматично за версією Minecraft',
        'Вывод игры появляется во вкладке «Консоль». Для полного вывода лучше указывать java.exe, а не javaw.exe.': 'Вивід гри з’являється на вкладці '
                                                                                                                    '«Консоль». Для повного виводу краще '
                                                                                                                    'вказувати java.exe, а не javaw.exe.',
        'Память и полноэкранный режим задаются глобально для всех сборок. Java, Minecraft и модлоадер меняются на вкладке «Настройки».': 'Пам’ять і '
                                                                                                                                         'повноекранний режим '
                                                                                                                                         'задаються глобально '
                                                                                                                                         'для всіх збірок. '
                                                                                                                                         'Java, Minecraft і '
                                                                                                                                         'модлоадер змінюються '
                                                                                                                                         'на вкладці '
                                                                                                                                         '«Налаштування».',
        'Пустая сборка создаётся без модпака. Для vanilla список версий loader не нужен.': 'Порожня збірка створюється без модпака. Для vanilla список версій '
                                                                                           'loader не потрібен.',
        'Официальная сборка StoneLight защищена от редактирования версии, loader и модпака.': 'Офіційна збірка StoneLight захищена від редагування версії, '
                                                                                              'loader і модпака.',
        'После смены версии/loader нажми «Обновить / установить», чтобы скачать Minecraft и установить модлоадер.': 'Після зміни версії/loader натисни '
                                                                                                                    '«Оновити / встановити», щоб завантажити '
                                                                                                                    'Minecraft і встановити модлоадер.',
        'Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.': 'Ці параметри застосовуються до всіх збірок без '
                                                                                                            'винятку, включно з офіційною StoneLight-збіркою.',
        'Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.': 'Offline-акаунти дозволені лише після входу хоча б в один '
                                                                                              'ліцензійний акаунт.',
        'Доступно после входа в лицензионный аккаунт': 'Доступно після входу в ліцензійний акаунт',
        'Выбери папку выше.': 'Вибери папку вище.',
        'Папка пустая.': 'Папка порожня.',
        'Готово.': 'Готово.',
        'Готов к запуску.': 'Готовий до запуску.',
        'Minecraft запущен.': 'Minecraft запущено.',
        'Repair завершён.': 'Repair завершено.',
        'Проверка Forge завершена.': 'Перевірку Forge завершено.',
        'Сборка обновлена/установлена.': 'Збірку оновлено/встановлено.',
        'ОШИБКА: ': 'ПОМИЛКА: ',
        ' МБ': ' МБ',
        '. Режим: ': '. Режим: '},
 'kk': {'\n\nЛаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.\nПосле установки в открывшемся окне нажми «Проверить Forge» или «Играть».': '\n'
                                                                                                                                                                          '\n'
                                                                                                                                                                          'Лаунчер '
                                                                                                                                                                          'ескі '
                                                                                                                                                                          'Forge '
                                                                                                                                                                          'осы '
                                                                                                                                                                          'қалтаны '
                                                                                                                                                                          'қабылдауы '
                                                                                                                                                                          'үшін '
                                                                                                                                                                          'launcher_profiles.json '
                                                                                                                                                                          'файлын '
                                                                                                                                                                          'алдын '
                                                                                                                                                                          'ала '
                                                                                                                                                                          'жасайды.\n'
                                                                                                                                                                          'Орнатқаннан '
                                                                                                                                                                          'кейін '
                                                                                                                                                                          '«Forge '
                                                                                                                                                                          'тексеру» '
                                                                                                                                                                          'немесе '
                                                                                                                                                                          '«Ойнау» '
                                                                                                                                                                          'батырмасын '
                                                                                                                                                                          'бас.',
        'Сейчас откроется Forge Installer.\n\nВ нём выбери Install client и укажи папку сборки:\n\n': 'Қазір Forge Installer ашылады.\n'
                                                                                                      '\n'
                                                                                                      'Оның ішінде Install client таңда да, жинақ қалтасын '
                                                                                                      'көрсет:\n'
                                                                                                      '\n',
        'Лаунчер заранее создаст launcher_profiles.json, чтобы старый Forge принял папку.': 'Лаунчер ескі Forge осы қалтаны қабылдауы үшін '
                                                                                            'launcher_profiles.json файлын алдын ала жасайды.',
        'После установки в открывшемся окне нажми «Проверить Forge» или «Играть».': 'Орнатқаннан кейін «Forge тексеру» немесе «Ойнау» батырмасын бас.',
        'Путь установки должен быть именно папкой сборки выше, а не обычной .minecraft.': 'Орнату жолы жоғарыдағы жинақ қалтасы болуы керек, кәдімгі '
                                                                                          '.minecraft емес.',
        'В Forge Installer выбери: Install client.': 'Forge Installer ішінде таңда: Install client.',
        'Лаунчер больше не ждёт закрытия Forge Installer, чтобы GUI не зависал. Установи Forge в открывшемся окне, затем вернись в лаунчер.': 'Интерфейс қатып '
                                                                                                                                              'қалмауы үшін '
                                                                                                                                              'лаунчер Forge '
                                                                                                                                              'Installer '
                                                                                                                                              'жабылуын '
                                                                                                                                              'күтпейді. '
                                                                                                                                              'Ашылған '
                                                                                                                                              'терезеде Forge '
                                                                                                                                              'орнатып, '
                                                                                                                                              'лаунчерге қайта '
                                                                                                                                              'орал.',
        'Forge Installer запущен. Заверши установку в его окне, затем нажми «Проверить Forge».': 'Forge Installer іске қосылды. Оның терезесінде орнатуды '
                                                                                                 'аяқтап, «Forge тексеру» бас.',
        'Forge Installer запущен. Если окно не появилось, открой fallback .cmd из data\\cache\\forge_installers. После установки нажми «Проверить Forge» или «Играть».': 'Forge '
                                                                                                                                                                         'Installer '
                                                                                                                                                                         'іске '
                                                                                                                                                                         'қосылды. '
                                                                                                                                                                         'Терезе '
                                                                                                                                                                         'шықпаса, '
                                                                                                                                                                         'data\\cache\\forge_installers '
                                                                                                                                                                         'ішіндегі '
                                                                                                                                                                         'fallback '
                                                                                                                                                                         '.cmd '
                                                                                                                                                                         'файлын '
                                                                                                                                                                         'аш. '
                                                                                                                                                                         'Орнатқаннан '
                                                                                                                                                                         'кейін '
                                                                                                                                                                         '«Forge '
                                                                                                                                                                         'тексеру» '
                                                                                                                                                                         'немесе '
                                                                                                                                                                         '«Ойнау» '
                                                                                                                                                                         'бас.',
        'Пароль в лаунчер не вводится: вход выполняется в браузере Microsoft. После успешного входа лаунчер автоматически примет ответ через локальный callback.': 'Құпиясөз '
                                                                                                                                                                   'лаунчерге '
                                                                                                                                                                   'енгізілмейді: '
                                                                                                                                                                   'кіру '
                                                                                                                                                                   'Microsoft '
                                                                                                                                                                   'браузер '
                                                                                                                                                                   'бетінде '
                                                                                                                                                                   'өтеді. '
                                                                                                                                                                   'Сәтті '
                                                                                                                                                                   'кіргеннен '
                                                                                                                                                                   'кейін '
                                                                                                                                                                   'лаунчер '
                                                                                                                                                                   'жауапты '
                                                                                                                                                                   'жергілікті '
                                                                                                                                                                   'callback '
                                                                                                                                                                   'арқылы '
                                                                                                                                                                   'автоматты '
                                                                                                                                                                   'қабылдайды.',
        'Готово. Нажми «Открыть вход Microsoft». Локальный callback будет запущен автоматически.\n': 'Дайын. «Microsoft кіруін ашу» бас. Жергілікті callback '
                                                                                                     'автоматты іске қосылады.\n',
        'Локальный callback запущен: ': 'Жергілікті callback іске қосылды: ',
        'Вход завершён': 'Кіру аяқталды',
        'Можно вернуться в StoneLight Launcher. Это окно браузера можно закрыть.': 'StoneLight Launcher-ге оралуға болады. Бұл браузер терезесін жабуға '
                                                                                   'болады.',
        '--- История вывода запущенной сборки ---': '--- Іске қосылған жинақ шығару тарихы ---',
        'Консоль сборки готова.\n': 'Жинақ консолі дайын.\n',
        'Java сборки': 'Жинақ Java-сы',
        'Сборка: ': 'Жинақ: ',
        'Сборка не найдена.': 'Жинақ табылмады.',
        'Добавлен аккаунт: ': 'Аккаунт қосылды: ',
        'Ошибка завершения входа: ': 'Кіруді аяқтау қатесі: ',
        'Не удалось вставить из буфера: ': 'Буферден қою мүмкін болмады: ',
        'Не удалось открыть лог: ': 'Логты ашу мүмкін болмады: ',
        'Не удалось открыть папку сборки: ': 'Жинақ қалтасын ашу мүмкін болмады: ',
        'Ошибка чтения папки: ': 'Қалтаны оқу қатесі: ',
        'Ошибка: ': 'Қате: ',
        'Не удалось запустить локальный callback-сервер на порту ': 'Жергілікті callback серверін мына портта іске қосу мүмкін болмады: ',
        '. Возможно, порт занят или заблокирован. Детали: ': '. Порт бос емес немесе бұғатталған болуы мүмкін. Мәліметтер: ',
        'Фильтр версии loader': 'Loader нұсқасының сүзгісі',
        'Версии ': 'Нұсқалар ',
        'Загружаю версии ': 'Нұсқалар жүктелуде ',
        'Найдено версий ': 'Табылған нұсқалар ',
        'Не найдено автоматически поддерживаемых версий ': 'Автоматты қолдау көрсетілетін нұсқалар табылмады ',
        'Всего версий: ': 'Барлық нұсқалар: ',
        'Всего: ': 'Барлығы: ',
        '. Показано: ': '. Көрсетілді: ',
        'версии': 'нұсқалар',
        'для Minecraft ': 'Minecraft үшін ',
        ' для Minecraft ': ' Minecraft үшін ',
        ' для ': ' үшін ',
        ' из списка? Папка на диске не удаляется.': ' тізімнен жойылсын ба? Дискідегі қалта жойылмайды.',
        'Удалить сборку ': 'Жинақты жою ',
        'Удалить аккаунт ': 'Аккаунтты жою ',
        ' установлена и сохранена для сборки: ': ' орнатылды және жинақ үшін сақталды: ',
        '. Preset auto скачает/использует portable Java в data/java.': '. Auto preset data/java ішіндегі portable Java-ны жүктейді/қолданады.',
        '. Выбери нужную в открытом списке.': '. Ашылған тізімнен керегін таңда.',
        '. Можно оставить поле пустым: лаунчер попробует взять последнюю доступную, если loader это поддерживает.': '. Өрісті бос қалдыруға болады: loader '
                                                                                                                    'қолдаса, лаунчер соңғы қолжетімді нұсқаны '
                                                                                                                    'қолдануға тырысады.',
        'Рекомендация для ': 'Ұсыныс: ',
        'Рекомендация Java': 'Java ұсынысы',
        'Автоматически по версии Minecraft': 'Minecraft нұсқасына қарай автоматты',
        'Вывод игры появляется во вкладке «Консоль». Для полного вывода лучше указывать java.exe, а не javaw.exe.': 'Ойын шығысы «Консоль» қойындысында '
                                                                                                                    'көрсетіледі. Толық шығару үшін java.exe '
                                                                                                                    'көрсеткен дұрыс, javaw.exe емес.',
        'Память и полноэкранный режим задаются глобально для всех сборок. Java, Minecraft и модлоадер меняются на вкладке «Настройки».': 'Жад және толық экран '
                                                                                                                                         'режимі барлық '
                                                                                                                                         'жинаққа ортақ. Java, '
                                                                                                                                         'Minecraft және '
                                                                                                                                         'модлоадер '
                                                                                                                                         '«Баптаулар» '
                                                                                                                                         'қойындысында '
                                                                                                                                         'өзгертіледі.',
        'Пустая сборка создаётся без модпака. Для vanilla список версий loader не нужен.': 'Бос жинақ модпаксыз жасалады. Vanilla үшін loader нұсқалары тізімі '
                                                                                           'қажет емес.',
        'Официальная сборка StoneLight защищена от редактирования версии, loader и модпака.': 'Ресми StoneLight жинағында нұсқа, loader және модпак '
                                                                                              'өзгертілмейді.',
        'После смены версии/loader нажми «Обновить / установить», чтобы скачать Minecraft и установить модлоадер.': 'Нұсқа/loader өзгергеннен кейін Minecraft '
                                                                                                                    'жүктеу және модлоадер орнату үшін '
                                                                                                                    '«Жаңарту / орнату» бас.',
        'Эти параметры применяются ко всем сборкам без исключения, включая официальную StoneLight-сборку.': 'Бұл параметрлер барлық жинақтарға қолданылады, '
                                                                                                            'соның ішінде ресми StoneLight жинағына да.',
        'Offline-аккаунты разрешены только после входа хотя бы в один лицензионный аккаунт.': 'Offline аккаунттар кемінде бір лицензиялық аккаунтқа кіргеннен '
                                                                                              'кейін ғана рұқсат.',
        'Доступно после входа в лицензионный аккаунт': 'Лицензиялық аккаунтқа кіргеннен кейін қолжетімді',
        'Выбери папку выше.': 'Жоғарыдағы қалтаны таңда.',
        'Папка пустая.': 'Қалта бос.',
        'Готово.': 'Дайын.',
        'Готов к запуску.': 'Іске қосуға дайын.',
        'Minecraft запущен.': 'Minecraft іске қосылды.',
        'Repair завершён.': 'Repair аяқталды.',
        'Проверка Forge завершена.': 'Forge тексеруі аяқталды.',
        'Сборка обновлена/установлена.': 'Жинақ жаңартылды/орнатылды.',
        'ОШИБКА: ': 'ҚАТЕ: ',
        ' МБ': ' МБ',
        '. Режим: ': '. Режим: '}}

for _language, _mapping in SUPPLEMENTAL_TRANSLATIONS.items():
    TRANSLATIONS.setdefault(_language, {}).update(_mapping)


# v0.5.31: account ComboBox placeholder capitalization fallback.
for _lang, _value in {
    "en": "No accounts",
    "uk": "Немає акаунтів",
    "kk": "Аккаунт жоқ",
}.items():
    TRANSLATIONS.setdefault(_lang, {})["Нет Аккаунтов"] = _value


# v0.5.31: theme selector.
for _lang, _mapping in {
    "en": {
        "Theme": "Theme",
        "Dark": "Dark",
        "Light": "Light",
        "Theme changed.": "Theme changed.",
    },
    "uk": {
        "Theme": "Тема",
        "Dark": "Темна",
        "Light": "Світла",
        "Theme changed.": "Тему змінено.",
    },
    "kk": {
        "Theme": "Тақырып",
        "Dark": "Қараңғы",
        "Light": "Жарық",
        "Theme changed.": "Тақырып өзгертілді.",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.31: protect brand names and translate instance type suffixes.
for _lang, _mapping in {
    "en": {
        "StoneLight": "StoneLight",
        "StoneLight Launcher": "StoneLight Launcher",
        "официальная": "official",
        "пользовательская": "custom",
        "официальная сборка": "official instance",
        "пользовательская сборка": "custom instance",
    },
    "uk": {
        "StoneLight": "StoneLight",
        "StoneLight Launcher": "StoneLight Launcher",
        "официальная": "офіційна",
        "пользовательская": "користувацька",
        "официальная сборка": "офіційна збірка",
        "пользовательская сборка": "користувацька збірка",
    },
    "kk": {
        "StoneLight": "StoneLight",
        "StoneLight Launcher": "StoneLight Launcher",
        "официальная": "ресми",
        "пользовательская": "пайдаланушы",
        "официальная сборка": "ресми жинақ",
        "пользовательская сборка": "пайдаланушы жинағы",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.31: extra theme names.
for _lang, _mapping in {
    "en": {
        "Laconic": "Laconic",
        "Neon": "Neon",
        "Retro Future": "Retro Future",
    },
    "uk": {
        "Laconic": "Лаконічна",
        "Neon": "Неон",
        "Retro Future": "Ретро-футуризм",
    },
    "kk": {
        "Laconic": "Лаконикалық",
        "Neon": "Неон",
        "Retro Future": "Ретро-футуризм",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: update manager UI.
for _lang, _mapping in {
    "en": {
        "Проверить обновления": "Check updates",
        "Проверяю обновления...": "Checking for updates...",
        "Обновлений не найдено.": "No updates found.",
        "Скачиваю обновление лаунчера...": "Downloading launcher update...",
        "Обновление скачано. Применить и перезапустить лаунчер сейчас?": "Update downloaded. Apply and restart the launcher now?",
        "Скачать обновление лаунчера?": "Download launcher update?",
        "Доступно обновление официальной StoneLight-сборки.": "Official StoneLight instance update is available.",
        "Применить метаданные и запустить обновление сборки?": "Apply metadata and start updating the instance?",
        "Лаунчер сейчас закроется, обновит файлы и запустится заново.": "The launcher will close, update files, and start again.",
        "Продолжить?": "Continue?",
    },
    "uk": {
        "Проверить обновления": "Перевірити оновлення",
        "Проверяю обновления...": "Перевіряю оновлення...",
        "Обновлений не найдено.": "Оновлень не знайдено.",
        "Скачиваю обновление лаунчера...": "Завантажую оновлення лаунчера...",
        "Обновление скачано. Применить и перезапустить лаунчер сейчас?": "Оновлення завантажено. Застосувати й перезапустити лаунчер зараз?",
        "Скачать обновление лаунчера?": "Завантажити оновлення лаунчера?",
        "Доступно обновление официальной StoneLight-сборки.": "Доступне оновлення офіційної StoneLight-збірки.",
        "Применить метаданные и запустить обновление сборки?": "Застосувати метадані й запустити оновлення збірки?",
        "Лаунчер сейчас закроется, обновит файлы и запустится заново.": "Лаунчер зараз закриється, оновить файли й запуститься знову.",
        "Продолжить?": "Продовжити?",
    },
    "kk": {
        "Проверить обновления": "Жаңартуларды тексеру",
        "Проверяю обновления...": "Жаңартулар тексерілуде...",
        "Обновлений не найдено.": "Жаңарту табылмады.",
        "Скачиваю обновление лаунчера...": "Лаунчер жаңартуы жүктелуде...",
        "Обновление скачано. Применить и перезапустить лаунчер сейчас?": "Жаңарту жүктелді. Қазір қолданып, лаунчерді қайта іске қосу керек пе?",
        "Скачать обновление лаунчера?": "Лаунчер жаңартуын жүктеу керек пе?",
        "Доступно обновление официальной StoneLight-сборки.": "Ресми StoneLight жинағының жаңартуы қолжетімді.",
        "Применить метаданные и запустить обновление сборки?": "Метадеректерді қолданып, жинақты жаңартуды бастау керек пе?",
        "Лаунчер сейчас закроется, обновит файлы и запустится заново.": "Лаунчер жабылып, файлдарды жаңартып, қайта іске қосылады.",
        "Продолжить?": "Жалғастыру?",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: official StoneLight pre-launch update flow.
for _lang, _mapping in {
    "en": {
        "Проверяю обновление StoneLight перед запуском...": "Checking StoneLight update before launch...",
        "Обновить StoneLight до": "Update StoneLight to",
        "перед запуском?": "before launch?",
        "Запустить текущую версию StoneLight без обновления?": "Launch the current StoneLight version without updating?",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "Could not check StoneLight updates. Launch the current version?",
        "Официальная сборка StoneLight обновлена.": "Official StoneLight instance has been updated.",
        "Официальная сборка StoneLight обновлена до": "Official StoneLight instance updated to",
        "Обновление StoneLight применено. Запускаю новую версию...": "StoneLight update applied. Launching the new version...",
        "Обновлений StoneLight перед запуском не найдено.": "No StoneLight updates found before launch.",
    },
    "uk": {
        "Проверяю обновление StoneLight перед запуском...": "Перевіряю оновлення StoneLight перед запуском...",
        "Обновить StoneLight до": "Оновити StoneLight до",
        "перед запуском?": "перед запуском?",
        "Запустить текущую версию StoneLight без обновления?": "Запустити поточну версію StoneLight без оновлення?",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "Не вдалося перевірити оновлення StoneLight. Запустити поточну версію?",
        "Официальная сборка StoneLight обновлена.": "Офіційну збірку StoneLight оновлено.",
        "Официальная сборка StoneLight обновлена до": "Офіційну збірку StoneLight оновлено до",
        "Обновление StoneLight применено. Запускаю новую версию...": "Оновлення StoneLight застосовано. Запускаю нову версію...",
        "Обновлений StoneLight перед запуском не найдено.": "Оновлень StoneLight перед запуском не знайдено.",
    },
    "kk": {
        "Проверяю обновление StoneLight перед запуском...": "Іске қосу алдында StoneLight жаңартуы тексерілуде...",
        "Обновить StoneLight до": "StoneLight-ты мына нұсқаға жаңарту",
        "перед запуском?": "іске қоспас бұрын?",
        "Запустить текущую версию StoneLight без обновления?": "StoneLight-тың ағымдағы нұсқасын жаңартусыз іске қосу керек пе?",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "StoneLight жаңартуларын тексеру мүмкін болмады. Ағымдағы нұсқаны іске қосу керек пе?",
        "Официальная сборка StoneLight обновлена.": "Ресми StoneLight жинағы жаңартылды.",
        "Официальная сборка StoneLight обновлена до": "Ресми StoneLight жинағы жаңартылды:",
        "Обновление StoneLight применено. Запускаю новую версию...": "StoneLight жаңартуы қолданылды. Жаңа нұсқа іске қосылуда...",
        "Обновлений StoneLight перед запуском не найдено.": "Іске қосу алдында StoneLight жаңартуы табылмады.",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: update service messages.
for _lang, _mapping in {
    "en": {
        "Автопроверка обновлений не удалась: {error}": "Auto-check for updates failed: {error}",
        "Доступна новая версия лаунчера: {version}": "New launcher version available: {version}",
        "Обновление лаунчера скачано. Скрипт применения: {script}": "Launcher update downloaded. Apply script: {script}",
        "Метаданные официальной сборки обновлены. Запускаю обновление сборки...": "Official instance metadata updated. Starting instance update...",
        "Официальная сборка StoneLight обновлена до {latest}.": "Official StoneLight instance updated to {latest}.",
        "Не удалось проверить обновления StoneLight: {error}": "Could not check StoneLight updates: {error}",
        "ОШИБКА: {error}": "ERROR: {error}",
        "Запуск StoneLight отменён пользователем.": "StoneLight launch canceled by user.",
        "Запуск StoneLight отменён: обновление не применено.": "StoneLight launch canceled: update was not applied.",
        "Запуск StoneLight отменён.": "StoneLight launch canceled.",
        "Некорректный GitHub repo для обновлений.": "Invalid GitHub repository for updates.",
        "В репозитории {repo} не найден latest release.": "No latest release found in repository {repo}.",
        "Нет URL для скачивания обновления.": "No URL for downloading the update.",
        "Не найден asset официальной сборки.": "Official instance asset was not found.",
        "Архив обновления не найден: {path}": "Update archive not found: {path}",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "Could not check StoneLight updates. Launch the current version?",
        "Запустить текущую версию StoneLight без обновления?": "Launch the current StoneLight version without updating?",
        "Обновить StoneLight до {latest} перед запуском?": "Update StoneLight to {latest} before launch?",
        "Доступно обновление официальной StoneLight-сборки.\n\nНовый архив: {asset}\nMinecraft: {latest}\n\n{suffix}": "Official StoneLight instance update is available.\n\nNew archive: {asset}\nMinecraft: {latest}\n\n{suffix}",
        "Применить метаданные и запустить обновление сборки?": "Apply metadata and start updating the instance?",
        "Обновление StoneLight применено. Запускаю новую версию...": "StoneLight update applied. Launching the new version...",
        "Обновлений StoneLight перед запуском не найдено.": "No StoneLight updates found before launch.",
        "Проверяю обновление StoneLight перед запуском...": "Checking StoneLight update before launch...",
    },
    "uk": {
        "Автопроверка обновлений не удалась: {error}": "Автоперевірка оновлень не вдалася: {error}",
        "Доступна новая версия лаунчера: {version}": "Доступна нова версія лаунчера: {version}",
        "Обновление лаунчера скачано. Скрипт применения: {script}": "Оновлення лаунчера завантажено. Скрипт застосування: {script}",
        "Метаданные официальной сборки обновлены. Запускаю обновление сборки...": "Метадані офіційної збірки оновлено. Запускаю оновлення збірки...",
        "Официальная сборка StoneLight обновлена до {latest}.": "Офіційну збірку StoneLight оновлено до {latest}.",
        "Не удалось проверить обновления StoneLight: {error}": "Не вдалося перевірити оновлення StoneLight: {error}",
        "ОШИБКА: {error}": "ПОМИЛКА: {error}",
        "Запуск StoneLight отменён пользователем.": "Запуск StoneLight скасовано користувачем.",
        "Запуск StoneLight отменён: обновление не применено.": "Запуск StoneLight скасовано: оновлення не застосовано.",
        "Запуск StoneLight отменён.": "Запуск StoneLight скасовано.",
        "Некорректный GitHub repo для обновлений.": "Некоректний GitHub-репозиторій для оновлень.",
        "В репозитории {repo} не найден latest release.": "У репозиторії {repo} не знайдено latest release.",
        "Нет URL для скачивания обновления.": "Немає URL для завантаження оновлення.",
        "Не найден asset официальной сборки.": "Asset офіційної збірки не знайдено.",
        "Архив обновления не найден: {path}": "Архів оновлення не знайдено: {path}",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "Не вдалося перевірити оновлення StoneLight. Запустити поточну версію?",
        "Запустить текущую версию StoneLight без обновления?": "Запустити поточну версію StoneLight без оновлення?",
        "Обновить StoneLight до {latest} перед запуском?": "Оновити StoneLight до {latest} перед запуском?",
        "Доступно обновление официальной StoneLight-сборки.\n\nНовый архив: {asset}\nMinecraft: {latest}\n\n{suffix}": "Доступне оновлення офіційної StoneLight-збірки.\n\nНовий архів: {asset}\nMinecraft: {latest}\n\n{suffix}",
        "Применить метаданные и запустить обновление сборки?": "Застосувати метадані й запустити оновлення збірки?",
        "Обновление StoneLight применено. Запускаю новую версию...": "Оновлення StoneLight застосовано. Запускаю нову версію...",
        "Обновлений StoneLight перед запуском не найдено.": "Оновлень StoneLight перед запуском не знайдено.",
        "Проверяю обновление StoneLight перед запуском...": "Перевіряю оновлення StoneLight перед запуском...",
    },
    "kk": {
        "Автопроверка обновлений не удалась: {error}": "Жаңартуларды автоматты тексеру сәтсіз аяқталды: {error}",
        "Доступна новая версия лаунчера: {version}": "Лаунчердің жаңа нұсқасы қолжетімді: {version}",
        "Обновление лаунчера скачано. Скрипт применения: {script}": "Лаунчер жаңартуы жүктелді. Қолдану скрипті: {script}",
        "Метаданные официальной сборки обновлены. Запускаю обновление сборки...": "Ресми жинақ метадеректері жаңартылды. Жинақ жаңартуы басталуда...",
        "Официальная сборка StoneLight обновлена до {latest}.": "Ресми StoneLight жинағы {latest} нұсқасына жаңартылды.",
        "Не удалось проверить обновления StoneLight: {error}": "StoneLight жаңартуларын тексеру мүмкін болмады: {error}",
        "ОШИБКА: {error}": "ҚАТЕ: {error}",
        "Запуск StoneLight отменён пользователем.": "StoneLight іске қосуын пайдаланушы тоқтатты.",
        "Запуск StoneLight отменён: обновление не применено.": "StoneLight іске қосылмады: жаңарту қолданылмады.",
        "Запуск StoneLight отменён.": "StoneLight іске қосылмады.",
        "Некорректный GitHub repo для обновлений.": "Жаңартулар үшін GitHub репозиторийі дұрыс емес.",
        "В репозитории {repo} не найден latest release.": "{repo} репозиторийінде latest release табылмады.",
        "Нет URL для скачивания обновления.": "Жаңартуды жүктеу URL мекенжайы жоқ.",
        "Не найден asset официальной сборки.": "Ресми жинақ asset-і табылмады.",
        "Архив обновления не найден: {path}": "Жаңарту архиві табылмады: {path}",
        "Не удалось проверить обновления StoneLight. Запустить текущую версию?": "StoneLight жаңартуларын тексеру мүмкін болмады. Ағымдағы нұсқаны іске қосу керек пе?",
        "Запустить текущую версию StoneLight без обновления?": "StoneLight-тың ағымдағы нұсқасын жаңартусыз іске қосу керек пе?",
        "Обновить StoneLight до {latest} перед запуском?": "Іске қоспас бұрын StoneLight-ты {latest} нұсқасына жаңарту керек пе?",
        "Доступно обновление официальной StoneLight-сборки.\n\nНовый архив: {asset}\nMinecraft: {latest}\n\n{suffix}": "Ресми StoneLight жинағының жаңартуы қолжетімді.\n\nЖаңа архив: {asset}\nMinecraft: {latest}\n\n{suffix}",
        "Применить метаданные и запустить обновление сборки?": "Метадеректерді қолданып, жинақ жаңартуын бастау керек пе?",
        "Обновление StoneLight применено. Запускаю новую версию...": "StoneLight жаңартуы қолданылды. Жаңа нұсқа іске қосылуда...",
        "Обновлений StoneLight перед запуском не найдено.": "Іске қосу алдында StoneLight жаңартуы табылмады.",
        "Проверяю обновление StoneLight перед запуском...": "Іске қосу алдында StoneLight жаңартуы тексерілуде...",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: shorter update buttons and clearer update-service messages.
for _lang, _mapping in {
    "en": {
        "Обновления": "Updates",
        "Установить": "Install",
        "Лог": "Log",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "No launcher or StoneLight build updates found.",
        "Доступна новая версия лаунчера: {latest}\nТекущая версия: {current}\n\nСкачать обновление лаунчера?": "New launcher version available: {latest}\nCurrent version: {current}\n\nDownload launcher update?",
    },
    "uk": {
        "Обновления": "Оновлення",
        "Установить": "Встановити",
        "Лог": "Лог",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "Оновлень лаунчера та StoneLight-збірки не знайдено.",
        "Доступна новая версия лаунчера: {latest}\nТекущая версия: {current}\n\nСкачать обновление лаунчера?": "Доступна нова версія лаунчера: {latest}\nПоточна версія: {current}\n\nЗавантажити оновлення лаунчера?",
    },
    "kk": {
        "Обновления": "Жаңартулар",
        "Установить": "Орнату",
        "Лог": "Лог",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "Лаунчер және StoneLight жинағы үшін жаңарту табылмады.",
        "Доступна новая версия лаунчера: {latest}\nТекущая версия: {current}\n\nСкачать обновление лаунчера?": "Лаунчердің жаңа нұсқасы қолжетімді: {latest}\nАғымдағы нұсқа: {current}\n\nЛаунчер жаңартуын жүктеу керек пе?",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: dynamic update-error localization and missing launcher release handling.
for _lang, _mapping in {
    "en": {
        "В репозитории {repo} не найден latest release.": "No latest release was found in repository {repo}.",
        "Архив обновления не найден: {path}": "Update archive was not found: {path}",
        "Не удалось проверить обновления StoneLight: {error}": "Could not check StoneLight updates: {error}",
        "ОШИБКА: {error}": "ERROR: {error}",
    },
    "uk": {
        "В репозитории {repo} не найден latest release.": "У репозиторії {repo} не знайдено latest release.",
        "Архив обновления не найден: {path}": "Архів оновлення не знайдено: {path}",
        "Не удалось проверить обновления StoneLight: {error}": "Не вдалося перевірити оновлення StoneLight: {error}",
        "ОШИБКА: {error}": "ПОМИЛКА: {error}",
    },
    "kk": {
        "В репозитории {repo} не найден latest release.": "{repo} репозиторийінде latest release табылмады.",
        "Архив обновления не найден: {path}": "Жаңарту архиві табылмады: {path}",
        "Не удалось проверить обновления StoneLight: {error}": "StoneLight жаңартуларын тексеру мүмкін болмады: {error}",
        "ОШИБКА: {error}": "ҚАТЕ: {error}",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: update flow cleanup and startup message localization.
for _lang, _mapping in {
    "en": {
        "Готов к запуску.": "Ready to launch.",
        "Готово.": "Ready.",
        "Добро пожаловать в StoneLight Launcher v{version}": "Welcome to StoneLight Launcher v{version}",
        "Запускаю локальную установку/обновление сборки: {name}": "Starting local install/update for instance: {name}",
        "Устанавливаю/обновляю выбранную сборку...": "Installing/updating the selected instance...",
        "Сборка обновлена/установлена.": "Instance updated/installed.",
        "Проверка StoneLight-сборки пропущена: выбрана не официальная сборка.": "StoneLight build check skipped: the selected instance is not the official build.",
        "Автопроверка обновлений не удалась: {error}": "Auto-check for updates failed: {error}",
        "Minecraft запущен.": "Minecraft started.",
        "Repair завершён.": "Repair completed.",
    },
    "uk": {
        "Готов к запуску.": "Готовий до запуску.",
        "Готово.": "Готово.",
        "Добро пожаловать в StoneLight Launcher v{version}": "Ласкаво просимо до StoneLight Launcher v{version}",
        "Запускаю локальную установку/обновление сборки: {name}": "Запускаю локальне встановлення/оновлення збірки: {name}",
        "Устанавливаю/обновляю выбранную сборку...": "Встановлюю/оновлюю вибрану збірку...",
        "Сборка обновлена/установлена.": "Збірку оновлено/встановлено.",
        "Проверка StoneLight-сборки пропущена: выбрана не официальная сборка.": "Перевірку StoneLight-збірки пропущено: вибрано не офіційну збірку.",
        "Автопроверка обновлений не удалась: {error}": "Автоперевірка оновлень не вдалася: {error}",
        "Minecraft запущен.": "Minecraft запущено.",
        "Repair завершён.": "Repair завершено.",
    },
    "kk": {
        "Готов к запуску.": "Іске қосуға дайын.",
        "Готово.": "Дайын.",
        "Добро пожаловать в StoneLight Launcher v{version}": "StoneLight Launcher v{version} қолданбасына қош келдіңіз",
        "Запускаю локальную установку/обновление сборки: {name}": "Жинақты жергілікті орнату/жаңарту басталды: {name}",
        "Устанавливаю/обновляю выбранную сборку...": "Таңдалған жинақ орнатылуда/жаңартылуда...",
        "Сборка обновлена/установлена.": "Жинақ жаңартылды/орнатылды.",
        "Проверка StoneLight-сборки пропущена: выбрана не официальная сборка.": "StoneLight жинағын тексеру өткізіліп жіберілді: ресми жинақ таңдалмаған.",
        "Автопроверка обновлений не удалась: {error}": "Жаңартуларды автоматты тексеру сәтсіз аяқталды: {error}",
        "Minecraft запущен.": "Minecraft іске қосылды.",
        "Repair завершён.": "Repair аяқталды.",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)


# v0.5.52: centralized service/status/log localization.
for _lang, _mapping in {
    "en": {
        "Запущенный процесс этой сборки не найден.": "No running process was found for this instance.",
        "Проверка обновлений заняла слишком много времени и была остановлена.": "Update check took too long and was stopped.",
        "Проверка обновлений остановлена по таймауту.": "Update check stopped by timeout.",
        "Проверяю обновления...": "Checking for updates...",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "No launcher or StoneLight build updates found.",
        "Доступно обновление официальной StoneLight-сборки.": "Official StoneLight instance update is available.",
        "Обновлений StoneLight перед запуском не найдено.": "No StoneLight updates found before launch.",
        "Запуск StoneLight отменён.": "StoneLight launch canceled.",
        "Запуск StoneLight отменён пользователем.": "StoneLight launch canceled by user.",
        "Готов к запуску.": "Ready to launch.",
        "Готово.": "Ready.",
    },
    "uk": {
        "Запущенный процесс этой сборки не найден.": "Запущений процес цієї збірки не знайдено.",
        "Проверка обновлений заняла слишком много времени и была остановлена.": "Перевірка оновлень тривала занадто довго й була зупинена.",
        "Проверка обновлений остановлена по таймауту.": "Перевірку оновлень зупинено за таймаутом.",
        "Проверяю обновления...": "Перевіряю оновлення...",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "Оновлень лаунчера та StoneLight-збірки не знайдено.",
        "Доступно обновление официальной StoneLight-сборки.": "Доступне оновлення офіційної StoneLight-збірки.",
        "Обновлений StoneLight перед запуском не найдено.": "Оновлень StoneLight перед запуском не знайдено.",
        "Запуск StoneLight отменён.": "Запуск StoneLight скасовано.",
        "Запуск StoneLight отменён пользователем.": "Запуск StoneLight скасовано користувачем.",
        "Готов к запуску.": "Готовий до запуску.",
        "Готово.": "Готово.",
    },
    "kk": {
        "Запущенный процесс этой сборки не найден.": "Бұл жинақтың іске қосылған процесі табылмады.",
        "Проверка обновлений заняла слишком много времени и была остановлена.": "Жаңартуларды тексеру тым ұзаққа созылып, тоқтатылды.",
        "Проверка обновлений остановлена по таймауту.": "Жаңартуларды тексеру таймаут бойынша тоқтатылды.",
        "Проверяю обновления...": "Жаңартулар тексерілуде...",
        "Обновлений лаунчера и StoneLight-сборки не найдено.": "Лаунчер және StoneLight жинағы үшін жаңарту табылмады.",
        "Доступно обновление официальной StoneLight-сборки.": "Ресми StoneLight жинағының жаңартуы қолжетімді.",
        "Обновлений StoneLight перед запуском не найдено.": "Іске қосу алдында StoneLight жаңартуы табылмады.",
        "Запуск StoneLight отменён.": "StoneLight іске қосылмады.",
        "Запуск StoneLight отменён пользователем.": "StoneLight іске қосуын пайдаланушы тоқтатты.",
        "Готов к запуску.": "Іске қосуға дайын.",
        "Готово.": "Дайын.",
    },
}.items():
    TRANSLATIONS.setdefault(_lang, {}).update(_mapping)

def tr(text: str | None) -> str | None:
    if text is None:
        return None

    language = normalize_language(_current_language)
    source = str(text)
    mapping = TRANSLATIONS.get(language, {})

    exact = mapping.get(source)
    if exact is not None:
        return exact

    # Deep fallback translates only Russian/Cyrillic source fragments.
    # English UI keys such as "Light" must not be replaced inside brand names
    # like "StoneLight Launcher".
    def has_cyrillic(value: str) -> bool:
        return any(("А" <= ch <= "я") or ch in "ЁёІіЇїЄєҐґ" for ch in value)

    protected_fragments = ("StoneLight", "Minecraft", "GitHub", "Microsoft", "Java", "Forge", "Fabric", "Quilt", "NeoForge")
    result = source

    for src, dst in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        if not src or src not in result:
            continue

        # Exact translations above still handle normal English labels.
        # Substring fallback is intentionally limited to Cyrillic fragments.
        if not has_cyrillic(src):
            continue

        for protected in protected_fragments:
            if protected in src:
                break
        else:
            result = result.replace(src, dst)

    return result
