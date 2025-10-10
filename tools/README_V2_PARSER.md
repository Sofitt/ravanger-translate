# LLM Translation Prepare V2 - Парсер с поддержкой персонажей

## Описание

Новая версия парсера `llm_translate_prepare_v2.py` работает с **исходными** файлами из `extracted_scripts/` и извлекает информацию о персонажах для улучшения качества перевода.

## Основные отличия от V1

| Функция | V1 | V2 |
|---------|----|----|
| Источник | `translation_modules/*_ru.rpy` | `extracted_scripts/*.rpy` |
| Персонажи | ❌ Нет | ✅ Да |
| Пол персонажа | ❌ Нет | ✅ Да (через карту) |
| Show команды | ❌ Нет | ✅ Учитывает |
| Карта персонажей | ❌ Нет | ✅ Создается автоматически |

## Формат JSON

### Пример строки с персонажем

```json
{
  "id": 103,
  "line": 762,
  "file": "c1.rpy",
  "speaker": "maid",
  "speaker_prefix": "maid",
  "speaker_gender": "female",
  "original": "H-hello? [namepov!tc]?",
  "translation": "",
  "context": "dialogue",
  "tags": [],
  "variables_curly": [],
  "variables_square": ["namepov!tc"],
  "special_chars": {
    "newlines": 0,
    "tabs": 0,
    "escaped_quotes": 0,
    "has_formatting": false
  }
}
```

### Новые поля

- **`speaker`** - сущность персонажа (maid, princess, nmaid и т.д.)
- **`speaker_prefix`** - префикс (n = narrator, или имя персонажа)
- **`speaker_gender`** - пол персонажа (male/female/neutral/unknown)
- **`line`** - номер строки в исходном файле

## Карта персонажей

Парсер работает с двумя типами файлов:
- **`data/characters.json`** - основной файл с заполненными гендерами (редактируется вручную)
- **`data/characters_ДД.ММ.ГГГГ-ЧЧ:ММ:СС.json`** - файлы с новыми персонажами, которых нет в основном

### Логика работы

1. При запуске парсер загружает `data/characters.json`
2. Сравнивает найденных персонажей с существующими
3. Если есть новые - сохраняет их в файл с датой
4. Если новых нет - пропускает сохранение

### Пример основного файла

```json
{
  "maid": {
    "entities": ["maid", "nmaid"],
    "gender": "",
    "notes": ""
  },
  "princess": {
    "entities": ["princess", "nprincess"],
    "gender": "",
    "notes": ""
  }
}
```

**Задача переводчика:** заполнить поле `gender` значениями:
- `"male"` - мужской пол
- `"female"` - женский пол
- `"neutral"` - нейтральный/неизвестный
- `"unknown"` - точно неизвестно

## Использование

### 1. Обработка одного файла

```bash
python3 llm_translate_prepare_v2.py \
  --source ../extracted_scripts/c1.rpy \
  --output ../temp_files/c1_v2.json \
  --character-map ../data/characters.json
```

### 2. Пакетная обработка

```bash
python3 llm_translate_prepare_v2.py \
  --batch ../extracted_scripts \
  --batch-output ../temp_files/llm_json_v2 \
  --character-map ../data/characters.json
```

### 3. Использование существующей карты персонажей

После того как вы заполнили `gender` в файле `characters-11.10.2025.json`:

```bash
# Повторная обработка с учетом пола
python3 llm_translate_prepare_v2.py \
  --source ../extracted_scripts/c1.rpy \
  --output ../temp_files/c1_v2.json \
  --character-map ../data/characters-11.10.2025.json
```

Теперь поле `speaker_gender` будет заполнено в JSON.

## Примеры распознавания персонажей

### Прямая речь с указанием персонажа

```renpy
maid talk "H-hello? [namepov!tc]?"
princess "Come out, little one."
```

Парсится как:
- `speaker: "maid"`, `original: "H-hello? [namepov!tc]?"`
- `speaker: "princess"`, `original: "Come out, little one."`

### Контекст из show команды

```renpy
show princess normal at offscreenright

"You are in a vast, richly decorated chamber."
```

Парсится как:
- `speaker: "princess"`, `original: "You are in a vast..."`

### Повествование (narrator)

```renpy
nprincess "She smiles warmly at you."
```

Парсится как:
- `speaker: "nprincess"`, `speaker_prefix: "n"`, `context: "narration"`

## Workflow с картой персонажей

### Первичная настройка

1. **Создать начальную карту персонажей:**
   ```bash
   python3 llm_translate_prepare_v2.py --batch ../extracted_scripts --character-map ../data/characters.json
   ```
   Будет создан файл `data/characters_11.10.2025-01:25:24.json` со всеми персонажами

2. **Заполнить пол персонажей:**
   Скопируйте содержимое файла с датой в `data/characters.json` и заполните `gender`:
   ```json
   {
     "maid": {
       "entities": ["maid", "nmaid"],
       "gender": "female",
       "notes": "Служанка принцессы"
     },
     "princess": {
       "entities": ["princess", "nprincess"],
       "gender": "female",
       "notes": ""
     }
   }
   ```

3. **Использовать в переводе:**
   ```bash
   python3 llm_translate_prepare_v2.py --batch ../extracted_scripts --character-map ../data/characters.json
   ```
   Парсер загрузит гендеры из основного файла и добавит их в JSON для LLM

### При обновлении игры

Если вышла новая версия игры с новыми персонажами:

1. **Запустить парсер:**
   ```bash
   python3 llm_translate_prepare_v2.py --batch ../extracted_scripts --character-map ../data/characters.json
   ```

2. **Проверить вывод:**
   ```
   ✅ Загружена существующая карта: ../data/characters.json
   💾 Новые персонажи сохранены: ../data/characters_11.10.2025-14:30:15.json
      Новых персонажей: 3
   ```

3. **Заполнить гендеры новых персонажей:**
   Откройте файл с датой, проставьте `gender` и добавьте в основной `characters.json`

4. **Готово:**
   При следующем запуске новые персонажи будут учтены

## Преимущества для перевода

- ✅ **Корректный род** - LLM знает пол персонажа
- ✅ **Контекст** - видно, кто говорит
- ✅ **Повествование** - различаются диалоги и описания
- ✅ **Отслеживание** - можно видеть номер строки в исходнике

## Совместимость

V2 парсер **не заменяет** V1, а дополняет его:
- **V1** - для работы с готовыми модулями перевода
- **V2** - для создания нового перевода с учетом контекста персонажей

## Фильтрация служебных слов

Парсер автоматически исключает служебные слова RenPy:
- `if`, `else`, `menu`, `centered`, `extend`, `nvl`
- `show`, `hide`, `with`, `scene`, `play`, `stop`
- И другие технические команды

Если какое-то слово ошибочно распознается как персонаж, добавьте его в `RENPY_KEYWORDS` в коде парсера.
