# GIMS Automation Skill

Claude Code Skill для управления автоматизацией GIMS - скрипты, типы источников данных, активаторы.

## Установка

### 1. Установить зависимости

```bash
pip install httpx
```

### 2. Настроить переменные окружения

Добавить в `~/.bashrc` (или `~/.zshrc`):

```bash
# GIMS API Configuration
export GIMS_URL="https://gims.example.com"
export GIMS_ACCESS_TOKEN="eyJ..."
export GIMS_REFRESH_TOKEN="eyJ..."
export GIMS_VERIFY_SSL="true"  # false для self-signed сертификатов
```

Применить изменения:

```bash
source ~/.bashrc
```

#### Получение JWT токенов

1. Войдите в GIMS через веб-интерфейс
2. Откройте Developer Tools → Application → Cookies
3. Скопируйте значения `access_token` и `refresh_token`

#### Автоматическое обновление токена

Skill автоматически обновляет access token при получении ошибки 401 (токен истёк). Для этого используется refresh token.

При истечении refresh token потребуется получить новые токены из браузера.

### 3. Добавить Skill в проект

Скопировать папку в каталог skills проекта или в персональные skills:

```bash
# Вариант 1: В проект
cp -r gims-automations-developer /path/to/project/.claude/skills/

# Вариант 2: Глобально (персональные skills)
cp -r gims-automations-developer ~/.claude/skills/
```

### 4. Проверить работу

```bash
cd gims-automations-developer/scripts
python gims_scripts.py list
python gims_references.py value-types
```

### 5. Проверка подключения

После настройки запустите Claude Code CLI и попросите:

```
Покажи список папок скриптов
```

Если подключение работает, вы увидите структуру папок GIMS.

## Структура

```
gims-automations-developer/
├── SKILL.md                      # Инструкции для Claude
├── README.md                     # Эта документация
└── scripts/
    ├── gims_client.py            # HTTP клиент для GIMS API
    ├── gims_scripts.py           # CLI для скриптов
    ├── gims_datasource_types.py  # CLI для типов источников данных
    ├── gims_activator_types.py   # CLI для типов активаторов
    ├── gims_references.py        # CLI для справочников
    └── gims_logs.py              # CLI для логов (SSE streaming)
```

## Использование

После установки Claude Code автоматически использует этот Skill при запросах про GIMS автоматизацию.

## Примеры промптов

### Работа со скриптами

```
Покажи все скрипты в папке monitoring
```

```
Найди скрипты, связанные с Prometheus
```

```
Покажи код скрипта check_health
```

```
Создай скрипт для проверки доступности HTTP-сервиса.
Скрипт должен:
- Принимать URL как параметр
- Делать HTTP GET запрос
- Возвращать статус и время ответа
- Обрабатывать таймауты и ошибки
```

```
Добавь логирование в скрипт check_prometheus_metrics
```

### Работа с типами источников данных

```
Покажи все типы источников данных
```

```
Покажи структуру типа PostgreSQL — его свойства и методы
```

```
Покажи только код метода execute_query типа PostgreSQL
```

```
Создай тип источника данных для Prometheus.

Свойства:
- url (строка, обязательное) — URL Prometheus сервера
- timeout (число) — таймаут запросов в секундах, по умолчанию 30

Методы:
- query(promql) — выполнить PromQL запрос, вернуть результат
- query_range(promql, start, end, step) — запрос с временным диапазоном
```

### Работа с типами активаторов

```
Покажи все типы активаторов
```

```
Покажи код и свойства активатора ScheduleActivator
```

```
Создай тип активатора для запуска по расписанию cron.

Свойства:
- cron_expression (строка, обязательное) — cron выражение
- timezone (строка) — часовой пояс, по умолчанию UTC
- enabled (логическое) — включён ли активатор
```

### Поиск и анализ

```
Найди все скрипты, которые используют requests.get
```

```
Найди методы источников данных, которые работают с JSON
```

### Сбор логов выполнения

```
Получи логи работы скрипта id 5 в течение 60 секунд
```

```
Получи логи скрипта 10, выбери только записи с текстом 'ERROR'
```

## CLI команды

Каждый скрипт поддерживает `--help` для получения справки:

```bash
python gims_scripts.py --help
python gims_scripts.py list --help
python gims_datasource_types.py create-method --help
```

## Разработка

### Добавление новых команд

1. Добавить функцию `cmd_<name>(args)` в соответствующий скрипт
2. Добавить субпарсер в функции `main()`
3. Добавить хендлер в словарь `handlers`
4. Обновить SKILL.md

### Тестирование

```bash
cd scripts

# Скрипты
python gims_scripts.py list
python gims_scripts.py get 1

# Типы источников данных
python gims_datasource_types.py list
python gims_datasource_types.py get 1

# Активаторы
python gims_activator_types.py list

# Справочники
python gims_references.py value-types
python gims_references.py sections
```

## Лицензия

Внутренний инструмент.
