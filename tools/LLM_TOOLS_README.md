# 🤖 Инструменты для LLM-перевода

## 📋 Обзор

Набор инструментов для автоматизированного перевода с использованием локальных LLM моделей.

---

## 🛠️ Инструменты

### 1. `llm_translate_prepare.py`
Подготовка файлов перевода для обработки через LLM

**Функции:**
- Парсинг `.rpy` файлов
- Извлечение структуры переводов
- Анализ переменных, тегов, спецсимволов
- Экспорт в JSON формат

**Использование:**

```bash
# Подготовить один модуль
python3 llm_translate_prepare.py --module ../translation_modules/c1_ru.rpy \
                                   --output ../temp_files/llm_json/c1_ru.json

# Подготовить все модули (пакетный режим)
python3 llm_translate_prepare.py --batch ../translation_modules \
                                   --batch-output ../temp_files/llm_json

# Режим по умолчанию (обработать все модули)
python3 llm_translate_prepare.py
```

**Выходной формат JSON:**

```json
{
  "metadata": {
    "module": "c1_ru.rpy",
    "total_strings": 236,
    "translated": 0,
    "untranslated": 236
  },
  "strings": [
    {
      "id": 0,
      "comment": "c1.rpy:123",
      "original": "Hello, {name}!",
      "translation": "",
      "context": "dialogue",
      "tags": [],
      "variables_curly": ["name"],
      "variables_square": [],
      "special_chars": {
        "newlines": 0,
        "tabs": 0,
        "escaped_quotes": 0
      }
    }
  ]
}
```

---

### 2. `llm_translate.py`
Основной скрипт для перевода через LLM

**Поддерживаемые backends:**
- OpenAI-compatible API (llama.cpp, text-generation-webui, vLLM)
- Ollama

**Функции:**
- Перевод текста через API
- Автоматическая валидация переводов
- Проверка сохранности переменных и тегов
- Обработка ошибок и повторные попытки

**Использование:**

```bash
# Базовый вариант (llama.cpp server)
python3 llm_translate.py --input ../temp_files/llm_json/c1_ru.json \
                          --output ../temp_files/llm_json/c1_ru_translated.json \
                          --api-url http://localhost:8080/v1/chat/completions \
                          --model local-model

# Ollama
python3 llm_translate.py --input ../temp_files/llm_json/c1_ru.json \
                          --output ../temp_files/llm_json/c1_ru_translated.json \
                          --backend ollama \
                          --api-url http://localhost:11434/api/chat \
                          --model llama3

# С настройкой температуры
python3 llm_translate.py --input ../temp_files/llm_json/c1_ru.json \
                          --output ../temp_files/llm_json/c1_ru_translated.json \
                          --temperature 0.3 \
                          --max-tokens 2000
```

**Параметры:**

- `--input` - входной JSON файл
- `--output` - выходной JSON файл
- `--backend` - backend: `openai` или `ollama` (по умолчанию `openai`)
- `--api-url` - URL API сервера
- `--api-key` - API ключ (если требуется)
- `--model` - название модели
- `--temperature` - temperature (0.0-1.0, по умолчанию 0.3)
- `--max-tokens` - максимум токенов в ответе

**Валидация:**

Автоматически проверяет:
- ✅ Сохранность переменных `{var}` и `[var]`
- ✅ Сохранность тегов `{color}`, `{b}`, и т.д.
- ✅ Количество переносов строк `\n`
- ✅ Экранирование кавычек `\"`

---

### 3. `llm_translate_apply.py`
Применение переводов из JSON обратно в .rpy файлы

**Функции:**
- Чтение переводов из JSON
- Обновление `.rpy` файлов
- Статистика применения
- Пакетная обработка

**Использование:**

```bash
# Применить один модуль
python3 llm_translate_apply.py --input ../temp_files/llm_json/c1_ru_translated.json \
                                --module ../translation_modules/c1_ru.rpy

# Применить с сохранением в новый файл
python3 llm_translate_apply.py --input ../temp_files/llm_json/c1_ru_translated.json \
                                --module ../translation_modules/c1_ru.rpy \
                                --output ../translation_modules/c1_ru_new.rpy

# Пакетный режим
python3 llm_translate_apply.py --batch-json ../temp_files/llm_json \
                                --batch-rpy ../translation_modules

# Режим по умолчанию (применить все переводы)
python3 llm_translate_apply.py
```

**Статистика:**
- Всего блоков обработано
- Применено новых переводов
- Пропущено (уже переведено)
- Пропущено (нет перевода)

---

## 🚀 Полный пайплайн

### Шаг 0: Установка зависимостей

```bash
pip install requests
```

### Шаг 1: Запуск LLM сервера

#### Вариант A: llama.cpp server

```bash
# Скачайте модель (например, Saiga или LLaMA)
# Запустите сервер
./llama-server -m model.gguf -c 4096 --port 8080
```

#### Вариант B: Ollama

```bash
# Установите Ollama: https://ollama.ai
ollama pull llama3
ollama serve
```

#### Вариант C: text-generation-webui

```bash
# Запустите с API режимом
python server.py --api --listen
```

### Шаг 2: Подготовка данных

```bash
cd tools

# Подготовить все модули для перевода
python3 llm_translate_prepare.py
```

**Результат:** JSON файлы в `../temp_files/llm_json/`

### Шаг 3: Перевод через LLM

```bash
# Перевести один модуль
python3 llm_translate.py \
    --input ../temp_files/llm_json/c1_ru.json \
    --output ../temp_files/llm_json/c1_ru_translated.json \
    --api-url http://localhost:8080/v1/chat/completions

# Или перевести все модули (скрипт-помощник)
for file in ../temp_files/llm_json/*.json; do
    basename=$(basename "$file" .json)
    if [[ ! "$basename" == *"_translated" ]]; then
        python3 llm_translate.py \
            --input "$file" \
            --output "../temp_files/llm_json/${basename}_translated.json" \
            --api-url http://localhost:8080/v1/chat/completions
    fi
done
```

### Шаг 4: Применение переводов

```bash
# Применить все переводы обратно в .rpy файлы
python3 llm_translate_apply.py
```

### Шаг 5: Упаковка в игру

```bash
# Упаковать переводы в игру
python3 smart_pack_translations.py
```

### Шаг 6: Тестирование

```bash
cd ..
./Ravager.sh
# В игре: Настройки → Язык → Русский
```

---

## 📊 Рекомендуемые настройки LLM

### Модели

**Рекомендуемые:**
- **Saiga 8B/13B** - специально для русского языка
- **LLaMA 3 8B/70B** - хорошее качество перевода
- **Qwen 7B/14B** - хорошо работает с русским

**Минимальные требования:**
- 8B параметров для приемлемого качества
- 13B+ для высокого качества

### Параметры генерации

```python
temperature = 0.3        # Низкая для точности
top_p = 0.9
top_k = 40
max_tokens = 2000
repeat_penalty = 1.1
```

### Промпт

См. `documentation/LLM_TRANSLATION_GUIDE.md` для полного промпта.

---

## ⚠️ Важные замечания

### 1. Проверка качества

**Всегда проверяйте переводы вручную:**
- Первые 10-20 строк каждого модуля
- Важные диалоги и сюжетные моменты
- Интерфейсные элементы

### 2. Ограничения LLM

**LLM может ошибаться в:**
- Сохранности переменных (проверяется автоматически)
- Контексте и тоне персонажей
- Специфических терминах фэнтези-сеттинга

**Решение:** Создайте глоссарий и включите его в промпт

### 3. Производительность

**Скорость перевода:**
- ~1-2 строки в секунду (зависит от модели и железа)
- ~100-200 строк за 2-5 минут
- Полный проект (27,969 строк) - несколько часов

**Оптимизация:**
- Используйте квантизованные модели (Q4_K_M, Q5_K_M)
- Включите GPU ускорение
- Переводите модули параллельно (на разных серверах)

### 4. Стоимость

**Локальная LLM:**
- ✅ Бесплатно
- ✅ Приватность данных
- ❌ Требует мощное железо

**Требования железа:**
- 8B модель: 8-16 GB RAM/VRAM
- 13B модель: 16-32 GB RAM/VRAM
- 70B модель: 64+ GB RAM или мощный GPU

---

## 🐛 Устранение проблем

### Проблема: API не отвечает

**Решение:**
```bash
# Проверьте, запущен ли сервер
curl http://localhost:8080/v1/models

# Проверьте логи сервера
```

### Проблема: Переводы низкого качества

**Решение:**
- Используйте более крупную модель
- Уточните системный промпт
- Снизьте temperature до 0.1-0.2
- Добавьте примеры в промпт (few-shot learning)

### Проблема: Переменные теряются

**Решение:**
- Валидатор автоматически обнаруживает это
- Проверьте логи `llm_translate.py`
- Повторите перевод проблемных строк
- Уточните промпт с акцентом на сохранность переменных

### Проблема: Слишком медленно

**Решение:**
- Используйте квантизованную модель (Q4_K_M вместо F16)
- Увеличьте batch size (если API поддерживает)
- Переводите модули параллельно:

```bash
# Запустите несколько экземпляров llm_translate.py
python3 llm_translate.py --input c1_ru.json --output c1_ru_tr.json &
python3 llm_translate.py --input c2_ru.json --output c2_ru_tr.json &
python3 llm_translate.py --input c3_ru.json --output c3_ru_tr.json &
```

---

## 📚 Дополнительные ресурсы

- `documentation/LLM_TRANSLATION_GUIDE.md` - полное руководство по переводу
- `documentation/WORKFLOW.md` - общий рабочий процесс
- `tools/README.md` - основные инструменты проекта

---

## 🎯 Советы по эффективности

### 1. Порядок перевода

Переводите модули в таком порядке:
1. **Интерфейс** (`screens_ru.rpy`, `options_ru.rpy`) - проверите работу пайплайна
2. **Маленькие модули** - быстрый прогресс, мотивация
3. **Основной сюжет** - критически важно для качества
4. **Дополнительный контент** - можно отложить

### 2. Глоссарий

Создайте файл `glossary.json`:

```json
{
  "Dragon": "Дракон",
  "Kobold": "Кобольд",
  "Lair": "Логово",
  "Hoard": "Клад",
  "Ravager": "Разоритель"
}
```

Включите его в системный промпт:

```python
system_prompt += "\n\nГЛОССАРИЙ:\n"
for en, ru in glossary.items():
    system_prompt += f"{en} → {ru}\n"
```

### 3. Мониторинг

Создайте скрипт для мониторинга прогресса:

```bash
# Подсчитать переведенные модули
python3 translation_helper.py
```

---

## 📝 Примеры использования

### Пример 1: Быстрый перевод одного модуля

```bash
cd tools

# 1. Подготовить
python3 llm_translate_prepare.py \
    --module ../translation_modules/c1_ru.rpy \
    --output ../temp_files/c1_ru.json

# 2. Перевести
python3 llm_translate.py \
    --input ../temp_files/c1_ru.json \
    --output ../temp_files/c1_ru_translated.json

# 3. Применить
python3 llm_translate_apply.py \
    --input ../temp_files/c1_ru_translated.json \
    --module ../translation_modules/c1_ru.rpy

# 4. Упаковать и протестировать
python3 smart_pack_translations.py
cd .. && ./Ravager.sh
```

### Пример 2: Массовый перевод всех модулей

```bash
cd tools

# 1. Подготовить все модули
python3 llm_translate_prepare.py

# 2. Перевести все (цикл)
for file in ../temp_files/llm_json/*.json; do
    basename=$(basename "$file" .json)
    echo "Перевод: $basename"
    python3 llm_translate.py \
        --input "$file" \
        --output "../temp_files/llm_json/${basename}_translated.json"
done

# 3. Применить все
python3 llm_translate_apply.py

# 4. Упаковать
python3 smart_pack_translations.py
```

---

## ✅ Финальный чеклист

Перед завершением работы:

- [ ] Все модули переведены
- [ ] Валидация прошла успешно
- [ ] Переводы применены в `.rpy` файлы
- [ ] Упаковано через `smart_pack_translations.py`
- [ ] Протестировано в игре
- [ ] Проверены критические диалоги
- [ ] Интерфейс корректно отображается
- [ ] Нет синтаксических ошибок Ren'Py
