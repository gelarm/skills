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

---

## Code Conventions

**ВАЖНО**: ВНИМАТЕЛЬНО ИЗУЧИТЕ И СЛЕДУЙТЕ ЭТИМ КОНВЕНЦИЯМ ПРИ НАПИСАНИИ КОДА ДЛЯ GIMS.

### Scripts

- Скрипты — это Python-код, выполняемый в Celery tasks в GIMS sandbox
- Используй `print_help()` для просмотра доступных встроенных функций
- Доступ к источникам данных через переменную `ds`
- Доступ к свойствам активатора через переменную `props`

**КРИТИЧЕСКИ ВАЖНО: Возврат значений из скриптов**

Если скрипт должен вернуть вычисленное значение (как результат Celery task), присвой это значение специальной переменной `return_result_` в конце скрипта:

```python
# Скрипт, вычисляющий и возвращающий значение
data = ds.my_datasource.fetch_data()
processed = process_data(data)

# Возврат значения - ОБЯЗАТЕЛЬНО используй переменную return_result_
return_result_ = processed
```

Переменная `return_result_` — ЕДИНСТВЕННЫЙ способ вернуть значение из скрипта. НЕ используй оператор `return` на уровне скрипта.

### DataSource Type Methods

**КРИТИЧЕСКИ ВАЖНО: Структура кода метода**

Методы НЕ используют оператор `return` для возврата значений. Вместо этого:
1. Определи **входные параметры** (`input_type=true`) — передаются при вызове метода
2. Определи **выходные параметры** (`input_type=false`) — возвращаются как dict из метода
3. В коде метода присваивай значения переменным выходных параметров

```python
# Метод с входным параметром 'promql' и выходным параметром 'result'
# Вход: promql (string) - доступен как переменная
# Выход: result (any) - должен быть присвоен

import requests

response = requests.get(
    f"{self.url}/api/v1/query",
    params={"query": promql},
    timeout=self.timeout
)

# Присваивание выходному параметру - возвращается как {"result": ...}
result = response.json()["data"]["result"]
```

**Ключевые правила для кода методов:**

1. **НЕТ оператора `return`** на уровне метода - значения возвращаются через выходные параметры
2. **Доступ к свойствам типа источника данных** через `self.property_label` (например, `self.url`, `self.timeout`)
3. **Вызов других методов** того же типа через `self.method_name(param=value)` - возвращает dict, если метод имеет выходные параметры
4. **Выходные параметры ДОЛЖНЫ быть присвоены** - всегда присваивай значения всем выходным параметрам
5. **Внутренние вспомогательные функции** могут быть определены, но они НЕ должны использовать `self`

```python
# Пример: Метод, вызывающий другой метод
# Метод: query_range с входами (promql, start, end, step) и выходом (result)

def format_time(timestamp):
    # Внутренняя функция-помощник - здесь нельзя использовать self
    return timestamp.isoformat()

response = requests.get(
    f"{self.url}/api/v1/query_range",
    params={
        "query": promql,
        "start": format_time(start),
        "end": format_time(end),
        "step": step
    },
    timeout=self.timeout
)

# Присваивание выходного параметра
result = response.json()["data"]["result"]
```

**Вызов методов источников данных из скриптов/активаторов:**

```python
# Доступ к источнику данных по имени, передача параметров как keyword arguments
response = gims_fault_ds.list_alerts(filter=alert_filter, limit=limit_alarms)
# response — это dict: {"result": [...], "count": 100}
```

### Activator Type Code

**КРИТИЧЕСКИ ВАЖНО: Доступ к свойствам в активаторах**

Свойства активатора доступны **напрямую по имени label** (НЕ через `self` или `props`):

```python
# Активатор со свойствами: interval (int), target_url (str), threshold (int)

# ПРАВИЛЬНО - доступ к свойствам напрямую по label
if interval > 0:
    response = requests.get(target_url, timeout=30)
    if response.status_code != 200 and threshold > 0:
        log.warning(f"Check failed: {response.status_code}")

# НЕПРАВИЛЬНО - не используй self или props
# self.interval  - НЕПРАВИЛЬНО
# props.interval - НЕПРАВИЛЬНО
```

**Структура активатора:**

```python
# Свойства доступны как переменные (по имени label)
# ds - доступ к источникам данных
# log - логгер

def check_health():
    """Внутренняя функция - может использоваться для организации логики."""
    # Доступ к методам источника данных
    result = ds.my_datasource.get_status()
    return result.get("status") == "ok"

# Основная логика активатора
if check_health():
    log.info("System is healthy")
else:
    log.error("System check failed")
```

### Value Type Restrictions

**ВАЖНО:** НЕ используй эти типы значений для свойств и параметров методов:
- `Список` (List) - вызывает ошибки
- `Справочник` (Dictionary) - вызывает ошибки

**Используй вместо них:**
- `Объект` (Object) - работает корректно для сложных структур данных

---

## GIMS Built-in Functions Reference

Все сценарии и активаторы GIMS выполняются в специальном sandbox-окружении с предопределёнными переменными и функциями. Код пишется на Python 3.10.

### Встроенные переменные сценариев

| Переменная | Тип | Описание |
|------------|-----|----------|
| `script_id` | int | ID сценария из БД |
| `script_name` | str | Имя сценария из БД |
| `activator_id` | int/None | ID активатора (None, если запущен из редактора портала) |
| `activator_name` | str | Имя активатора (пустое, если запущен из редактора) |
| `activator_server_name` | str | Имя сервера активатора из Конфигуратора |
| `activator_server_address` | str | Адрес сервера активатора из Конфигуратора |
| `cluster_id` | int | ID кластера из БД |
| `server_id` | int | ID сервера из БД |

### Встроенные переменные активаторов

| Переменная | Тип | Описание |
|------------|-----|----------|
| `activator_id` | int | ID активатора из БД |
| `activator_name` | str | Имя активатора из БД |
| `cluster_id` | int | ID кластера из БД |
| `cluster_name` | str | Имя кластера из БД |
| `server_id` | int | ID сервера из БД |

### Функции логирования

Доступны в сценариях, активаторах и методах источников данных.

| Функция | Описание |
|---------|----------|
| `set_level_log(level)` | Установить уровень логирования. `level`: `'DEBUG'`, `'INFO'`, `'WARNING'`, `'ERROR'` |
| `set_log_prefix(prefix='', is_add_obj_name=False)` | Установить префикс для всех сообщений лога |
| `get_log_prefix()` | Получить текущий префикс сообщений |
| `print(text)` | Вывести сообщение с уровнем INFO (функция переопределена в GIMS) |
| `print_err(text)` | Вывести сообщение с уровнем ERROR |
| `print_wrn(text)` | Вывести сообщение с уровнем WARNING |
| `print_dbg(text)` | Вывести сообщение с уровнем DEBUG |

**Пример:**
```python
set_level_log('DEBUG')
set_log_prefix('[MyScript]', is_add_obj_name=True)
print('Начало обработки')  # INFO: [MyScript] Начало обработки
print_dbg(f'Параметры: {params}')  # DEBUG: [MyScript] Параметры: {...}
print_err('Ошибка подключения')  # ERROR: [MyScript] Ошибка подключения
```

### Функции импорта и загрузки

| Функция | Описание |
|---------|----------|
| `load_data_sources(ids_list=None, names_list=None, like_name=None, type_names_list=None, like_type_name=None)` | Загрузить массив источников данных по фильтрам |
| `import_script(script_name)` | Импортировать сценарий как Python-модуль. Возвращает имя модуля для использования |
| `include_script(script_name, propagate_exit=True, only_return_code=False)` | Включить код сценария в текущую точку выполнения |
| `get_script_run_info()` | (Только в активаторах) Получить информацию о прикреплённом сценарии: `{script_id, script_name, script_exec_timeout}` |

**Пример import_script:**
```python
# Импорт сценария как модуля
utils = import_script('common_utils')
result = utils.process_data(data)
```

**Пример include_script:**
```python
# Включение кода сценария (выполняется в текущем контексте)
include_script('init_variables')
# Переменные из init_variables теперь доступны
print(initialized_var)
```

**Пример load_data_sources:**
```python
# Загрузить все источники данных типа "Prometheus"
prometheus_sources = load_data_sources(type_names_list=['Prometheus'])
for ds in prometheus_sources:
    result = ds.query(promql='up')
```

### Функции работы со сценариями

| Функция | Описание |
|---------|----------|
| `script_run2(is_result=False, exec_timeout=0, script_marker=None, is_async_run=True, is_result_exec_state=False, kwargs=None, no_data_source=False)` | Выполнить сценарий. Возвращает `task_id` (async) или `result` (sync) |
| `script_ready(task_id)` | Проверить статус выполнения: `True` — выполнен, `False` — выполняется |
| `script_get_res(task_id, timeout=None, is_return_ready_result=False)` | Получить результат (`return_result_`) с ожиданием |
| `script_get_res_with_while(task_id, timeout=None, delay=1)` | Получить результат с polling (цикл проверки) |
| `script_kill(task_id)` | Завершить задачу Celery: `True` — сигнал отправлен |
| `script_run_chain(scripts_chain_json)` | Выполнить цепочку сценариев |
| `get_queued_tasks()` | Получить количество задач в очереди |

**Важно:** В сценариях использование `script_run2` с `is_async_run=True` может вызвать DeadLock. Безопасное использование: `is_async_run=False` с получением результата.

**Пример асинхронного запуска (в активаторе):**
```python
# Запустить сценарий асинхронно
task_id = script_run2(script_marker='process_data', kwargs={'batch_id': 123})

# Дождаться результата
result = script_get_res_with_while(task_id, timeout=300, delay=5)
print(f'Результат: {result}')
```

**Пример синхронного запуска:**
```python
# Запустить и сразу получить результат
result = script_run2(
    script_marker='calculate_metrics',
    is_result=True,
    is_async_run=False,
    exec_timeout=60,
    kwargs={'metric_type': 'cpu'}
)
```

### Функции кэширования

| Функция | Описание |
|---------|----------|
| `set_cache(key, value, timeout=None)` | Сохранить значение в локальном кэше. `timeout` — время жизни в секундах |
| `get_cache(key, default=None)` | Получить значение из кэша. `default` — значение по умолчанию |
| `delete_cache(key)` | Удалить ключ из кэша |

**Пример:**
```python
# Кэширование результата тяжёлого запроса
cached_data = get_cache('heavy_query_result')
if cached_data is None:
    cached_data = perform_heavy_query()
    set_cache('heavy_query_result', cached_data, timeout=300)  # 5 минут
```

### Исключения GIMS

При работе со встроенными функциями могут возникать следующие исключения:

| Исключение | Когда возникает |
|------------|-----------------|
| `ScriptRunError` | Ошибка запуска сценария через `script_run2` |
| `ScriptReadyError` | Ошибка проверки статуса через `script_ready` |
| `ScriptGetResultError` | Ошибка получения результата |
| `ScriptGetResultTimeout` | Таймаут ожидания результата |
| `ScriptKillError` | Ошибка завершения задачи |
| `ScriptRunChainError` | Ошибка выполнения цепочки сценариев |
| `ImportScriptError` | Ошибка импорта сценария через `import_script` |
| `IncludeScriptError` | Ошибка включения сценария через `include_script` |
| `LoadDataSourcesError` | Ошибка загрузки источников данных |

**Пример обработки:**
```python
try:
    task_id = script_run2(script_marker='risky_script', is_async_run=True)
    result = script_get_res(task_id, timeout=60)
except ScriptGetResultTimeout:
    print_err('Сценарий не успел выполниться за 60 секунд')
    script_kill(task_id)
except ScriptRunError as e:
    print_err(f'Ошибка запуска: {e}')
```

---

## Development Recommendations

**ВАЖНО ДЛЯ LLM**: Следуйте этим рекомендациям при разработке компонентов GIMS для обеспечения качества и эффективности.

### Разбиение большого кода

Если код сценария слишком большой (высокий расход контекста LLM при загрузке), рекомендуется разбить его:

1. **На части через `include_script`** — код включается в текущий контекст:
   ```python
   include_script('config_loader')      # загружает конфигурацию
   include_script('data_processor')     # обрабатывает данные
   # Переменные из обоих сценариев доступны здесь
   ```

2. **На модули через `import_script`** — код импортируется как Python-модуль:
   ```python
   utils = import_script('string_utils')
   validators = import_script('data_validators')

   clean_data = utils.normalize(raw_data)
   if validators.is_valid(clean_data):
       process(clean_data)
   ```

### Параллельное выполнение

Активатор может запускать сценарии как отдельные Celery tasks через `script_run2`:

```python
# Запуск нескольких сценариев параллельно
task_ids = []
for batch in data_batches:
    task_id = script_run2(
        script_marker='process_batch',
        is_async_run=True,
        kwargs={'batch': batch}
    )
    task_ids.append(task_id)

# Сбор результатов
results = []
for task_id in task_ids:
    result = script_get_res_with_while(task_id, timeout=300)
    results.append(result)
```

### Диагностика и отладка

Используй функции логирования для диагностики:

```python
set_level_log('DEBUG')  # Включить debug-вывод

print_dbg(f'Входные параметры: {params}')
print(f'Обработано {count} записей')
print_wrn('Обнаружены дубликаты, пропускаем')
print_err(f'Критическая ошибка: {error}')
```

### Проверка библиотек

Если код использует `import`, проверь наличие библиотек в `installed-requirements.txt`. Для установки недостающих:

```bash
uv pip install --no-cache <package_name>
```

### Планирование больших задач

Для больших задач всегда:
1. Выполни анализ задачи
2. Спланируй и спроектируй решение
3. Предложи пользователю план реализации
4. После подтверждения и уточнения дискуссионных моментов — разработай код

### Доступ к системным функциям из методов источников данных

В коде методов источников данных доступны системные функции того окружения, откуда вызываются методы (из кода активатора или сценария). Это означает, что методы могут использовать `print`, `print_err`, `set_cache` и другие функции.

---

## Best Practices

**ВАЖНО ДЛЯ LLM**: Применяйте эти best practices во всех задачах разработки GIMS.

1. **Всегда изучай сначала** — используй `list` и `get` команды перед внесением изменений
2. **Ищи перед созданием** — используй `search` для поиска существующего кода для повторного использования
3. **Получай справочники** — всегда вызывай `python scripts/gims_references.py value-types` и `python scripts/gims_references.py sections` перед созданием свойств
4. **Используй осмысленные имена** — `label` это code identifier (English, snake_case), `name` это display name (может быть локализовано)
5. **Тестируй инкрементально** — сначала создай минимальный код, затем расширяй
6. **Используй папки** — организуй скрипты/типы в логическую иерархию папок

---

## Common Patterns

**ВАЖНО ДЛЯ LLM**: Используйте эти шаблоны как примеры правильной работы с GIMS через CLI.

### Найти и изменить скрипт

```bash
# 1. Поиск скрипта
python scripts/gims_scripts.py search --query "health_check"

# 2. Получить метаданные (без кода)
python scripts/gims_scripts.py get <found_id>

# 3. Получить код для анализа
python scripts/gims_scripts.py get-code <found_id>

# 4. Обновить код
python scripts/gims_scripts.py update <found_id> --code "<new_code>"
```

### Создать полноценный тип источника данных (пример Prometheus)

```bash
# 1. Получить справочники
python scripts/gims_references.py value-types
# Обрати внимание: str=4, int=2, bool=3, object=6 (используй object вместо list/dict!)

python scripts/gims_references.py sections
# Обрати внимание: Основные=1, Подключение=2

# 2. Создать тип
python scripts/gims_datasource_types.py create \
  --name "Prometheus" \
  --description "Prometheus monitoring"
# Получаем type_id из вывода

# 3. Создать свойства (доступ через self.label в коде метода)
python scripts/gims_datasource_types.py create-property \
  --type-id <type_id> \
  --name "URL" \
  --label "url" \
  --value-type-id 4 \
  --section-id 2 \
  --required \
  --description "URL Prometheus сервера"

python scripts/gims_datasource_types.py create-property \
  --type-id <type_id> \
  --name "Timeout" \
  --label "timeout" \
  --value-type-id 2 \
  --section-id 2 \
  --default-value "30" \
  --description "Таймаут запросов в секундах"

# 4. Создать метод с правильной структурой кода
# Код метода - БЕЗ оператора return, присваивание выходному параметру
cat > /tmp/query_method.py << 'EOF'
import requests

response = requests.get(
    f"{self.url}/api/v1/query",
    params={"query": promql},
    timeout=self.timeout
)
response.raise_for_status()

# Присваивание выходного параметра (возвращается как {"result": ...})
result = response.json()["data"]["result"]
EOF

python scripts/gims_datasource_types.py create-method \
  --type-id <type_id> \
  --name "Query" \
  --label "query" \
  --code-file /tmp/query_method.py \
  --description "Выполнить PromQL запрос"
# Получаем method_id из вывода

# 5. Создать параметры метода
# Входной параметр - передаётся при вызове метода
python scripts/gims_datasource_types.py create-param \
  --method-id <method_id> \
  --label "promql" \
  --value-type-id 4 \
  --input-type \
  --description "PromQL запрос"

# Выходной параметр - возвращается из метода как ключ dict
python scripts/gims_datasource_types.py create-param \
  --method-id <method_id> \
  --label "result" \
  --value-type-id 6 \
  --description "Результат запроса"
```

### Создать тип активатора

```bash
# Свойства активатора доступны напрямую по label (НЕ через self)
cat > /tmp/activator_code.py << 'EOF'
# Свойства: check_interval, target_url доступны как переменные

import requests

if check_interval > 0:
    try:
        response = requests.get(target_url, timeout=30)
        if response.status_code == 200:
            log.info("Health check passed")
        else:
            log.warning(f"Health check failed: {response.status_code}")
    except Exception as e:
        log.error(f"Health check error: {e}")
EOF

# 1. Создать тип активатора
python scripts/gims_activator_types.py create \
  --name "HealthCheck" \
  --code-file /tmp/activator_code.py \
  --description "Периодическая проверка здоровья"
# Получаем activator_type_id из вывода

# 2. Создать свойства - доступны напрямую по имени label в коде
python scripts/gims_activator_types.py create-property \
  --type-id <activator_type_id> \
  --name "Интервал проверки" \
  --label "check_interval" \
  --value-type-id 2 \
  --section-id 1 \
  --default-value "60"

python scripts/gims_activator_types.py create-property \
  --type-id <activator_type_id> \
  --name "URL для проверки" \
  --label "target_url" \
  --value-type-id 4 \
  --section-id 1 \
  --required
```

### Поиск и анализ кода

```bash
# Найти методы, использующие execute
python scripts/gims_datasource_types.py search \
  --query "execute" \
  --search-in code

# Найти активаторы с планированием
python scripts/gims_activator_types.py search \
  --query "schedule" \
  --search-in code

# Найти скрипты, связанные с prometheus
python scripts/gims_scripts.py search \
  --query "prometheus" \
  --search-in both
```

---

## Error Handling

**ВАЖНО ДЛЯ LLM**: При возникновении ошибок следуйте этим рекомендациям.

### Типичные ошибки API

- **401 с "токен обновления недействителен"**: Refresh token недействителен — попроси пользователя проверить активность учётной записи и получить новые токены из браузера (Developer Tools → Application → Cookies → `access_token` и `refresh_token`)
- **401**: Access token истёк — автоматическое обновление через refresh token (обрабатывается CLI-скриптами)
- **403**: Доступ запрещён — у пользователя нет необходимых прав
- **404**: Сущность не найдена — проверь существование ID
- **400**: Ошибка валидации — проверь обязательные поля и типы данных

### Обработка ошибок в коде GIMS

```python
# В скриптах и активаторах всегда используй обработку исключений
try:
    result = ds.my_datasource.fetch_data(param=value)
    if result:
        process_result(result)
    else:
        print_wrn('Получен пустой результат')
except Exception as e:
    print_err(f'Ошибка получения данных: {e}')
    # Можно использовать кэш как fallback
    result = get_cache('last_known_good_data')
```

### Проверка доступности библиотек

```python
# В начале скрипта/метода проверь импорты
try:
    import requests
    import pandas as pd
except ImportError as e:
    print_err(f'Недостающая библиотека: {e}')
    print_err('Установите библиотеку через: uv pip install --no-cache <package_name>')
    raise
```
