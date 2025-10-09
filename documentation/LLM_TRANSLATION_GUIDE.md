# 🤖 Руководство по LLM-переводу Ravager

## 📋 Обзор

Автоматизированный перевод игры с использованием локальной fine-tuned модели **Saiga** через Ollama.

**Ключевые особенности:**
- ✅ Правила перевода встроены в модель (fine-tuning)
- ✅ Простой формат запроса: `[INST]Переведи: "Text"[/INST]`
- ✅ Автоматическая валидация переменных, тегов и спецсимволов
- ✅ Настройки: `temperature=0.1`, `top_p=0.7`

---

## 🔧 Конфигурация

## 🔄 Пайплайн обработки

### 🚀 Автоматический перевод (рекомендуется)

Запуск полного пайплайна всех модулей:

```bash
cd tools
./llm_batch_translate.sh
```

**Что делает скрипт:**
1. Подготовка JSON из `.rpy` файлов (`translation_modules/`)
2. Перевод через Ollama API (модель Saiga)
3. Применение переводов обратно в `.rpy`
4. Упаковка в `game/tl/ru/`

### 🔧 Ручной перевод отдельного модуля

**Шаг 1: Подготовка**
```bash
cd tools
python3 llm_translate_prepare.py --module ../translation_modules/c1_ru.rpy
```
→ Создает `temp_files/llm_json/c1_ru.json`

**Шаг 2: Перевод**
```bash
python3 llm_translate.py \
  --input ../temp_files/llm_json/c1_ru.json \
  --output ../temp_files/llm_json/c1_ru_translated.json \
  --backend ollama \
  --api-url http://127.0.0.1:11434/api/chat \
  --model saiga \
  --temperature 0.1 \
  --top-p 0.7
```

**Шаг 3: Применение**
```bash
python3 llm_translate_apply.py \
  --input ../temp_files/llm_json/c1_ru_translated.json \
  --module ../translation_modules/c1_ru.rpy
```

**Шаг 4: Упаковка**
```bash
python3 smart_pack_translations.py
```

**Шаг 5: Тестирование**
```bash
cd .. && ./Ravager.sh
```

---

## 📊 Анализ прогресса перевода

### Проверка статистики

```bash
cd tools
python3 translation_helper.py --status
```

**Вывод:**
- Общее количество модулей
- Процент выполнения
- Топ модулей для работы (отсортированы по размеру)
- Создание файла `translation_work_plan.md`

### Создание образца для перевода

```bash
python3 translation_helper.py --create-sample <module_name>
```

Создает файл `sample_<module>_ru.txt` с примером первых 10 строк.

---

## 📊 Валидация переводов

### Автоматические проверки

```python
def validate_translation(original: str, translation: str) -> List[str]:
    errors = []
    
    # 1. Переменные
    orig_vars_curly = set(re.findall(r'\{(\w+)\}', original))
    trans_vars_curly = set(re.findall(r'\{(\w+)\}', translation))
    if orig_vars_curly != trans_vars_curly:
        errors.append(f"Несоответствие переменных {{}}: {orig_vars_curly} != {trans_vars_curly}")
    
    orig_vars_square = set(re.findall(r'\[(\w+)\]', original))
    trans_vars_square = set(re.findall(r'\[(\w+)\]', translation))
    if orig_vars_square != trans_vars_square:
        errors.append(f"Несоответствие переменных []: {orig_vars_square} != {trans_vars_square}")
    
    # 2. Теги
    orig_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', original)
    trans_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', translation)
    if orig_tags != trans_tags:
        errors.append(f"Несоответствие тегов: {orig_tags} != {trans_tags}")
    
    # 3. Спецсимволы
    if original.count('\\n') != translation.count('\\n'):
        errors.append(f"Несоответствие \\n: {original.count('\\n')} != {translation.count('\\n')}")
    
    # 4. Кавычки
    if '"' in translation and '\\"' not in original:
        errors.append("Кавычки должны быть экранированы: \\\"")
    
    return errors
```

---

## 📁 Структура выходных данных

### JSON для LLM (промежуточный формат)

```json
{
  "metadata": {
    "module": "c1_ru.rpy",
    "total_strings": 236,
    "source_language": "en",
    "target_language": "ru"
  },
  "strings": [
    {
      "id": 0,
      "comment": "c1.rpy:123",
      "original": "Hello, Dragon!",
      "translation": "",
      "context": "dialogue",
      "tags": [],
      "variables": []
    }
  ]
}
```

### После перевода

```json
{
  "strings": [
    {
      "id": 0,
      "comment": "c1.rpy:123",
      "original": "Hello, Dragon!",
      "translation": "Привет, Дракон!",
      "context": "dialogue",
      "tags": [],
      "variables": []
    }
  ]
}
```

---

## ✅ Чеклист качества

Перед финализацией перевода:

- [ ] Все переменные `{var}` и `[var]` сохранены
- [ ] Все теги форматирования сохранены
- [ ] Спецсимволы `\n`, `\t` на месте
- [ ] Кавычки экранированы `\"`
- [ ] Нет технических строк в переводе
- [ ] Стиль соответствует контексту (диалог/интерфейс)
- [ ] Терминология консистентна
- [ ] Перевод помещается в UI (длина текста)
- [ ] Нет грамматических ошибок

---

## 🔧 Устранение проблем

### Проблема: "invalid syntax" при загрузке в игру

**Причина:** Неэкранированные кавычки

**Решение:**
```renpy
# ❌ НЕПРАВИЛЬНО
new "Он сказал "Привет""

# ✅ ПРАВИЛЬНО
new "Он сказал \"Привет\""
```

### Проблема: Переменная отображается как текст

**Причина:** Переменная была переведена

**Решение:**
```renpy
# ❌ НЕПРАВИЛЬНО
new "У тебя {золото} золота"

# ✅ ПРАВИЛЬНО
new "У тебя {gold} золота"
```

### Проблема: Текст не помещается в кнопку

**Причина:** Перевод слишком длинный

**Решение:**
```renpy
# ❌ НЕПРАВИЛЬНО
old "Auto"
new "Автоматически"

# ✅ ПРАВИЛЬНО
old "Auto"
new "Авто"
```

---

## ⚠️ Важные замечания

### О промптах и правилах перевода

**Системный промпт НЕ используется** - все правила встроены в fine-tuned модель Saiga.

Формат запроса очень простой:
```
[INST]Переведи: "Your text here"[/INST]
```

Модель обучена:
- Не переводить переменные `{var}` и `[var]`
- Сохранять теги `{color=...}`, `{b}`, `{/b}` и т.д.
- Сохранять количество `\n` (переносов строк)
- Использовать неформальное "ты" в диалогах

### О качестве перевода

**Статистика теста (options_ru.json, 23 строки):**
- ✅ 100% успешно переведено (23/23)
- ✅ Все теги форматирования сохранены
- ✅ Все URL не изменены
- ✅ Переносы строк корректны
- ✅ Вложенные теги работают

### Про обработку ошибок

Валидатор Python проверяет:
1. Соответствие переменных `{var}` и `[var]`
2. Соответствие тегов форматирования
3. Количество `\n` и `\t`
4. Экранирование кавычек `\"`

Если есть предупреждения - проверьте результат вручную.

---

## 📚 Дополнительные ресурсы

- **`LLM_QUICKSTART.md`** - быстрый старт LLM-перевода
- **`WORKFLOW.md`** - общий процесс перевода
- **`tools/README.md`** - описание всех инструментов
- **`translation_work_plan.md`** - автоматически генерируемый план работы

---

## 🎯 Быстрый старт

```bash
# 1. Установка Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull saiga

# 2. Запуск перевода
cd tools
./llm_batch_translate.sh

# 3. Проверка результатов
python3 translation_helper.py --status

# 4. Упаковка и тест
python3 smart_pack_translations.py
cd .. && ./Ravager.sh
```
