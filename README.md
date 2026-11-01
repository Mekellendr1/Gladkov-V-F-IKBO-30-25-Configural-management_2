# depgraph — визуализация графа зависимостей пакетов NuGet

Инструмент анализирует и визуализирует граф зависимостей пакетов
формата .NET (NuGet) без использования готовых менеджеров пакетов
и сторонних библиотек для получения зависимостей.

## Текущий статус

Готов этап 3: построение полного графа зависимостей алгоритмом DFS
с рекурсией, ограничение анализа максимальной глубиной, обработка
циклических зависимостей и расширенный тестовый режим.

## Структура репозитория

- `run.sh` — скрипт запуска приложения;
- `src/config.py` — разбор и валидация параметров командной строки;
- `src/nuget.py` — клиент NuGet v3: service index, .nuspec, парсинг XML;
- `src/graph.py` — построение графа: DFS, ограничение глубины, циклы;
- `src/main.py` — точка входа приложения;
- `tests/run_tests.sh` — запуск всех bash-тестов;
- `tests/test_stage1.sh` — тесты валидации параметров (этап 1);
- `tests/test_stage2.sh` — тесты получения прямых зависимостей (этап 2);
- `tests/test_stage3.sh` — тесты построения графа, циклов, глубины (этап 3).

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

JSON-файл: имя пакета (большие латинские буквы) -> список прямых
зависимостей. Одна и та же структура используется и для NuGet
(зависимости не фильтруются по версии и target framework).

    {
      "A": [{"id": "B"}, {"id": "C"}],
      "B": [{"id": "D"}],
      "C": [{"id": "D"}],
      "D": []
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
| `graph.build_graph` | строит граф зависимостей рекурсивным DFS |
| `graph._visit` | обходит одну вершину и рекурсивно её зависимости |
| `main.make_nuget_fetcher` | создаёт функцию получения зависимостей из NuGet |
| `main.make_test_fetcher` | создаёт функцию получения зависимостей из файла |
| `main.print_graph` | выводит граф в виде рёбер `узел -> потомок` |
| `main._graph_order` | порядок вершин в DFS-preorder от корня |
| `main.main` | точка входа: построение графа или ошибка |

## Сборка, запуск, тесты

Сборка не требуется (чистый Python 3, только стандартная библиотека).

Запуск приложения:

    ./run.sh --package Newtonsoft.Json \
        --source https://api.nuget.org/v3/index.json --version 13.0.3 \
        --max-depth 2

Запуск тестов:

    bash tests/run_tests.sh

## Примеры использования

Полный граф из тестового файла (пакеты — большие латинские буквы):

    $ ./run.sh --package A --source tree.json --test-mode --max-depth 5
    A -> B
    A -> C
    B -> D
    C -> D
    D -> (none)

Циклическая зависимость (A -> B -> C -> A):

    $ ./run.sh --package A --source cycle.json --test-mode --max-depth 5
    A -> B
    B -> C
    C -> (cycle)

Ограничение глубины (max-depth 1 обрезает граф):

    $ ./run.sh --package A --source deep.json --test-mode --max-depth 1
    A -> B
    B -> (depth limit)

Живой NuGet с ограничением глубины:

    $ ./run.sh --package Microsoft.Extensions.Logging \
        --source https://api.nuget.org/v3/index.json --version 8.0.0 \
        --max-depth 2
    Microsoft.Extensions.Logging -> Microsoft.Extensions.DependencyInjection
    Microsoft.Extensions.Logging -> Microsoft.Extensions.Logging.Abstractions
    ...