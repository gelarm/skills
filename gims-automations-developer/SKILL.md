---
name: gims-automations
description: Управление автоматизацией GIMS - скрипты, типы источников данных, активаторы. Используй когда нужно создать/изменить/удалить скрипты или типы в GIMS.
allowed-tools: Bash, Read, Write, Glob, Grep
---

# GIMS Automation Skill

Управление скриптами, типами источников данных и активаторами в GIMS через Python CLI скрипты.

## Конфигурация

Скрипты используют переменные окружения. Убедись что они установлены:

```bash
# Проверка переменных
echo $GIMS_URL
echo $GIMS_ACCESS_TOKEN
```

Требуемые переменные:
- `GIMS_URL` - URL сервера GIMS (например: https://gims.example.com)
- `GIMS_ACCESS_TOKEN` - JWT access token
- `GIMS_REFRESH_TOKEN` - JWT refresh token
- `GIMS_VERIFY_SSL` - проверка SSL (true/false, по умолчанию true)

Токены можно получить через интерфейс GIMS (Профиль → API Токены).

## Путь к скриптам

Все скрипты находятся в подпапке `scripts/` этого skill.

При вызове команд используй относительный путь от корня skill:

```bash
# Скрипты находятся в gims-automations-developer/scripts/
python scripts/gims_scripts.py [команды]
python scripts/gims_datasource_types.py [команды]
# и т.д.
```

## Доступные команды

Для получения справки по любой команде используй флаг `--help`:

```bash
python scripts/gims_scripts.py --help
python scripts/gims_scripts.py create --help
```

### Скрипты (gims_scripts.py)

```bash
# Папки
python scripts/gims_scripts.py list-folders
python scripts/gims_scripts.py create-folder --name "Название"
python scripts/gims_scripts.py create-folder --name "Вложенная" --parent-folder-id 1
python scripts/gims_scripts.py delete-folder <folder_id>

# Список скриптов
python scripts/gims_scripts.py list
python scripts/gims_scripts.py list --folder-id 1

# Получение скрипта
python scripts/gims_scripts.py get <script_id>              # Без кода
python scripts/gims_scripts.py get <script_id> --include-code  # С кодом
python scripts/gims_scripts.py get-code <script_id>         # Только код

# Создание/изменение скрипта
python scripts/gims_scripts.py create --name "Название" --code "print('hello')"
python scripts/gims_scripts.py create --name "Из файла" --code-file /path/to/code.py
python scripts/gims_scripts.py update <script_id> --name "Новое имя"
python scripts/gims_scripts.py update <script_id> --code "новый код"
python scripts/gims_scripts.py update <script_id> --code-file /path/to/code.py
python scripts/gims_scripts.py delete <script_id>

# Поиск по коду
python scripts/gims_scripts.py search --query "текст"
python scripts/gims_scripts.py search --query "ТЕКСТ" --case-sensitive
python scripts/gims_scripts.py search --query "точный текст" --exact-match
```

### Типы источников данных (gims_datasource_types.py)

```bash
# Папки
python scripts/gims_datasource_types.py list-folders
python scripts/gims_datasource_types.py create-folder --name "Название"
python scripts/gims_datasource_types.py update-folder <folder_id> --name "Новое"
python scripts/gims_datasource_types.py delete-folder <folder_id>

# Типы
python scripts/gims_datasource_types.py list
python scripts/gims_datasource_types.py list --folder-id 1
python scripts/gims_datasource_types.py get <type_id>           # Метаданные + свойства + методы (без кода)
python scripts/gims_datasource_types.py get <type_id> --no-methods
python scripts/gims_datasource_types.py get <type_id> --no-properties
python scripts/gims_datasource_types.py create --name "Название" --code "код"
python scripts/gims_datasource_types.py update <type_id> --code "новый код"
python scripts/gims_datasource_types.py delete <type_id>
python scripts/gims_datasource_types.py search --query "regex" --search-in both

# Свойства
python scripts/gims_datasource_types.py list-properties <type_id>
python scripts/gims_datasource_types.py create-property --type-id <id> --name "Имя" --label "label" --value-type-id 1 --section-id 1
python scripts/gims_datasource_types.py update-property <property_id> --name "Новое"
python scripts/gims_datasource_types.py delete-property <property_id>

# Методы
python scripts/gims_datasource_types.py list-methods <type_id>
python scripts/gims_datasource_types.py get-method <method_id>
python scripts/gims_datasource_types.py get-method-code <method_id>  # Только код метода
python scripts/gims_datasource_types.py create-method --type-id <id> --name "method" --code "код"
python scripts/gims_datasource_types.py update-method <method_id> --code "новый код"
python scripts/gims_datasource_types.py delete-method <method_id>

# Параметры методов
python scripts/gims_datasource_types.py list-params <method_id>
python scripts/gims_datasource_types.py create-param --method-id <id> --name "param" --label "param_label" --value-type-id 1
python scripts/gims_datasource_types.py update-param <param_id> --name "новое"
python scripts/gims_datasource_types.py delete-param <param_id>
```

### Типы активаторов (gims_activator_types.py)

```bash
# Папки
python scripts/gims_activator_types.py list-folders
python scripts/gims_activator_types.py create-folder --name "Название"
python scripts/gims_activator_types.py update-folder <folder_id> --name "Новое"
python scripts/gims_activator_types.py delete-folder <folder_id>

# Типы
python scripts/gims_activator_types.py list
python scripts/gims_activator_types.py list --folder-id 1
python scripts/gims_activator_types.py get <type_id>           # Метаданные + свойства (без кода)
python scripts/gims_activator_types.py get <type_id> --include-code
python scripts/gims_activator_types.py get-code <type_id>      # Только код
python scripts/gims_activator_types.py create --name "Название" --code "код"
python scripts/gims_activator_types.py update <type_id> --code "новый код"
python scripts/gims_activator_types.py delete <type_id>
python scripts/gims_activator_types.py search --query "regex" --search-in both

# Свойства
python scripts/gims_activator_types.py list-properties <type_id>
python scripts/gims_activator_types.py create-property --type-id <id> --name "Имя" --label "label" --value-type-id 1 --section-id 1
python scripts/gims_activator_types.py update-property <property_id> --name "Новое"
python scripts/gims_activator_types.py delete-property <property_id>
```

### Справочники (gims_references.py)

```bash
# Типы значений (для свойств и параметров)
python scripts/gims_references.py value-types

# Секции свойств
python scripts/gims_references.py sections
```

### Логи выполнения (gims_logs.py)

```bash
# Стриминг логов скрипта (SSE)
python scripts/gims_logs.py stream <script_id>
python scripts/gims_logs.py stream <script_id> --timeout 60
python scripts/gims_logs.py stream <script_id> --tail 10      # Показать последние 10 строк
python scripts/gims_logs.py stream <script_id> --filter "ERROR"
python scripts/gims_logs.py stream <script_id> --keep-timestamp
python scripts/gims_logs.py stream <script_id> --end-markers "DONE" "END"
```

## Важные замечания

### Код в ответах

По умолчанию код скриптов, методов и активаторов **не включается** в ответ (отображается как `[FILTERED]`). Это сделано для экономии токенов.

Для получения кода используй:
- `--include-code` флаг
- Отдельные команды `get-code` / `get-method-code`

### Свойства в GIMS

При создании свойств нужно указать:
- `value_type_id` - тип значения (получи через `gims_references.py value-types`)
- `section_name_id` - секция свойства (получи через `gims_references.py sections`)

**Важно:** Не используй типы 'Список' или 'Справочник' - используй 'Объект' вместо них.

### Методы DataSource Types

Методы DataSource Type имеют собственные параметры (аргументы). Каждый параметр также требует `value_type_id`.

В коде метода параметры доступны как обычные переменные по имени label.

### Активаторы

В коде активатора свойства доступны напрямую по имени label (без `self`).

### Поиск

Поиск поддерживает regex. По умолчанию поиск регистронезависимый.

- `--search-in name` - поиск по имени (по умолчанию)
- `--search-in code` - поиск в коде
- `--search-in both` - поиск везде

### Логи

Команда `stream` использует SSE для получения логов в реальном времени:
- По умолчанию показывает только **новые** записи (tail=0)
- Завершается при обнаружении маркера окончания (по умолчанию "END SCRIPT")
- Или по таймауту

## Примеры типичных задач

### Создать новый скрипт

```bash
python scripts/gims_scripts.py create --name "Мой скрипт" --code-file /tmp/script.py
```

### Изменить код существующего скрипта

```bash
# 1. Получить текущий код
python scripts/gims_scripts.py get-code 123 > /tmp/script.py

# 2. Отредактировать файл

# 3. Загрузить обновлённый код
python scripts/gims_scripts.py update 123 --code-file /tmp/script.py
```

### Найти скрипты использующие определённую функцию

```bash
python scripts/gims_scripts.py search --query "my_function"
```

### Создать DataSource Type с методом

```bash
# 1. Создать тип
python scripts/gims_datasource_types.py create --name "MyType" --code "# init code"

# 2. Создать метод (допустим тип получил id=5)
python scripts/gims_datasource_types.py create-method --type-id 5 --name "get_data" --code "return data"

# 3. Добавить параметр к методу (допустим метод получил id=10)
python scripts/gims_datasource_types.py create-param --method-id 10 --name "ID записи" --label "record_id" --value-type-id 1
```

### Мониторинг выполнения скрипта

```bash
# Запустить скрипт в GIMS вручную, затем:
python scripts/gims_logs.py stream 123 --timeout 120
```
