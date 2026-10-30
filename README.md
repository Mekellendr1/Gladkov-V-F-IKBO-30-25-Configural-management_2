# depgraph — визуализация графа зависимостей пакетов NuGet

Инструмент анализирует и визуализирует граф зависимостей пакетов
формата .NET (NuGet) без использования готовых менеджеров пакетов
и сторонних библиотек для получения зависимостей.

## Текущий статус

Готов этап 2: получение прямых зависимостей заданной версии пакета
из NuGet-репозитория (v3 API, .nuspec пакета) или из локального
файла тестового графа.

## Структура репозитория

- `run.sh` — скрипт запуска приложения;
- `src/config.py` — разбор и валидация параметров командной строки;
- `src/nuget.py` — клиент NuGet v3: service index, .nuspec, парсинг XML;
- `src/main.py` — точка входа приложения;
- `tests/run_tests.sh` — запуск всех bash-тестов;
- `tests/test_stage1.sh` — тесты валидации параметров (этап 1);
- `tests/test_stage2.sh` — тесты получения зависимостей (этап 2).

## Параметры командной строки

| Параметр | Описание |
| --- | --- |
| `--package` | имя анализируемого пакета (обязательный) |
| `--source` | URL репозитория или путь к файлу тестового репозитория (обязательный) |
| `--test-mode` | режим тестового репозитория (файл графа) |
| `--version` | версия пакета, по умолчанию `1.0.0` |
| `--ascii-tree` | режим вывода зависимостей в формате ASCII-дерева |
| `--max-depth` | максимальная глубина анализа, по умолчанию `5` |

## Формат тестового графа (--test-mode)

JSON-файл: имя пакета -> версия -> список прямых зависимостей.

    {
      "A": {
        "1.0.0": [{"id": "B", "version": "1.0.0"}],
        "2.0.0": []
      }
    }

## Функции

| Функция | Описание |
| --- | --- |
| `config.build_parser` | создаёт парсер опций командной строки |
| `config.validate_package` | проверяет имя пакета |
| `config.validate_source` | проверяет URL или путь к тестовому файлу |
| `config.validate_version` | проверяет формат версии X.Y.Z |
| `config.validate_max_depth` | проверяет диапазон глубины анализа |
| `config.parse_args` | разбирает аргументы и возвращает конфигурацию |
| `config.format_config` | форматирует конфигурацию как ключ-значение |
| `nuget.fetch_json` | скачивает JSON-документ по URL |
| `nuget.find_package_base_url` | находит PackageBaseAddress/3.0.0 в service index |
| `nuget.nuspec_url` | строит URL .nuspec пакета заданной версии |
| `nuget.fetch_nuspec` | скачивает .nuspec пакета |
| `nuget.parse_dependencies` | извлекает прямые зависимости из XML .nuspec |
| `main.normalize_deps` | проверяет записи зависимостей тестового графа |
| `main.fetch_nuget_dependencies` | прямые зависимости из живого репозитория |
| `main.fetch_test_dependencies` | прямые зависимости из тестового графа |
| `main.print_dependencies` | выводит прямые зависимости на экран |
| `main.main` | точка входа: вывод зависимостей или ошибки |

## Сборка, запуск, тесты

Сборка не требуется (чистый Python 3, только стандартная библиотека).

Запуск приложения:

    ./run.sh --package Newtonsoft.Json \
        --source https://api.nuget.org/v3/index.json --version 13.0.3

Запуск тестов:

    bash tests/run_tests.sh

## Примеры использования

Прямые зависимости из живого NuGet:

    $ ./run.sh --package Newtonsoft.Json \
        --source https://api.nuget.org/v3/index.json --version 13.0.3
    Microsoft.CSharp 4.3.0
    NETStandard.Library 1.6.1

    $ ./run.sh --package Microsoft.Extensions.Logging \
        --source https://api.nuget.org/v3/index.json --version 8.0.0
    Microsoft.Extensions.DependencyInjection 8.0.0
    Microsoft.Extensions.Logging.Abstractions 8.0.0
    Microsoft.Extensions.Options 8.0.0

Тестовый граф:

    $ ./run.sh --package A --source graph.json --test-mode --version 1.0.0
    B 1.0.0
    C 2.0.0

Обработка ошибок:

    $ ./run.sh --package Z --source graph.json --test-mode --version 1.0.0
    ERROR: package Z 1.0.0 not found in test graph

    $ ./run.sh --package NoPkg --source https://api.nuget.org/v3/index.json \
        --version 99.99.99
    ERROR: package NoPkg 99.99.99 not found