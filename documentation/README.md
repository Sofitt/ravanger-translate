# 🎯 Перевод игры Ravager на русский язык

## 🚀 Быстрый старт

### Команды для выполнения задач:

```bash
# 1. Получить ключи для переводов
cd tools && python3 extract_dialogue_only.py

# 2. Разбить на модули для перевода  
python3 split_translation.py

# 3. Упаковать переводы в игру
python3 smart_pack_translations.py

# 4. Запустить игру для тестирования
cd .. && ./Ravager.sh
```

## 📁 Структура проекта

- `translation_modules/` - модули для перевода (35 файлов, 27,969 строк)
- `tools/` - инструменты для работы
- `game/tl/ru/` - финальные файлы перевода

## 🛠️ Основные инструменты

- `extract_dialogue_only.py` - извлечение диалогов ⭐
- `split_translation.py` - разбивка на модули
- `smart_pack_translations.py` - упаковка в игру ⭐
- `translation_helper.py` - анализ прогресса

## 📖 Подробная документация

- `WORKFLOW.md` - пошаговое руководство для переводчиков
- `translation_work_plan.md` - план работы по приоритетам
