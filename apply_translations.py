#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json

def apply_translation_to_module(module_path: str, translations: dict):
    """Применяет переводы к модулю"""
    
    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = content
    applied_count = 0
    
    # Находим все пары old/new и заменяем
    def replace_translation(match):
        nonlocal applied_count
        comment = match.group(1)
        old_text = match.group(2)
        current_new = match.group(3)
        
        # Если есть перевод для этой строки
        if old_text in translations and translations[old_text].strip():
            applied_count += 1
            return f'    # {comment}\n    old "{old_text}"\n    new "{translations[old_text]}"'
        else:
            return match.group(0)
    
    pattern = r'    # ([^\n]+)\n    old "([^"]+)"\n    new "([^"]*)"'
    updated_content = re.sub(pattern, replace_translation, updated_content)
    
    # Сохраняем обновленный файл
    with open(module_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    return applied_count

def create_translation_template():
    """Создает шаблон для быстрого перевода популярных фраз"""
    
    common_translations = {
        # Интерфейс
        "Android": "Android",
        "Demo": "Демо",
        "Patreon": "Patreon", 
        "Public": "Публичная",
        "Test": "Тест",
        
        # Общие игровые фразы
        "Yes": "Да",
        "No": "Нет",
        "Continue": "Продолжить",
        "Back": "Назад",
        "Next": "Далее",
        "Save": "Сохранить",
        "Load": "Загрузить",
        "Settings": "Настройки",
        "Options": "Опции",
        "Gallery": "Галерея",
        "Credits": "Титры",
        "Quit": "Выход",
        
        # Часто встречающиеся слова
        "Dragon": "Дракон",
        "Princess": "Принцесса",
        "King": "Король",
        "Queen": "Королева",
        "Knight": "Рыцарь",
        "Castle": "Замок",
        "Village": "Деревня",
        "Forest": "Лес",
        "Mountain": "Гора",
        "Cave": "Пещера",
        
        # Эмоции и действия
        "Happy": "Счастливый",
        "Sad": "Грустный",
        "Angry": "Злой",
        "Surprised": "Удивленный",
        "Attack": "Атаковать",
        "Defend": "Защищаться",
        "Run": "Бежать",
        "Hide": "Прятаться",
        "Talk": "Говорить",
        "Listen": "Слушать"
    }
    
    template_file = "common_translations.json"
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(common_translations, f, ensure_ascii=False, indent=2)
    
    print(f"Создан шаблон переводов: {template_file}")
    return template_file

def quick_translate_simple_modules():
    """Быстро переводит простые модули с базовыми фразами"""
    
    # Загружаем общие переводы
    template_file = "common_translations.json"
    if not os.path.exists(template_file):
        create_translation_template()
    
    with open(template_file, 'r', encoding='utf-8') as f:
        common_translations = json.load(f)
    
    modules_dir = "translation_modules"
    simple_modules = ["options_ru.rpy", "screens_ru.rpy"]
    
    total_applied = 0
    
    for module_name in simple_modules:
        module_path = os.path.join(modules_dir, module_name)
        if os.path.exists(module_path):
            print(f"Применяю переводы к {module_name}...")
            applied = apply_translation_to_module(module_path, common_translations)
            total_applied += applied
            print(f"  Применено переводов: {applied}")
    
    print(f"\nВсего применено переводов: {total_applied}")

def create_translation_workflow():
    """Создает рабочий процесс для переводчиков"""
    
    workflow_file = "TRANSLATION_WORKFLOW.md"
    with open(workflow_file, 'w', encoding='utf-8') as f:
        f.write("""# Рабочий процесс перевода Ravager

## 🚀 Быстрый старт

### 1. Структура проекта
```
translation_modules/          # Модули для перевода
├── c1_ru.rpy                # Глава 1 (236 строк)
├── options_ru.rpy           # Настройки (6 строк) ⭐ НАЧАТЬ ЗДЕСЬ
├── screens_ru.rpy           # Интерфейс (99 строк)
└── ...
```

### 2. Формат перевода
```renpy
translate ru strings:

    # c1.rpy:123
    old "Hello, world!"
    new "Привет, мир!"        # ← ВАША ЗАДАЧА: заполнить это поле
```

## 📋 Пошаговый процесс

### Шаг 1: Выберите модуль
Рекомендуемый порядок:
1. `options_ru.rpy` (6 строк) - настройки
2. `screens_ru.rpy` (99 строк) - интерфейс  
3. `c1_ru.rpy` (236 строк) - первая глава
4. `c2_*_ru.rpy` - вторая глава
5. И так далее...

### Шаг 2: Откройте модуль в текстовом редакторе
```bash
# Пример для первого модуля
nano translation_modules/options_ru.rpy
```

### Шаг 3: Переведите строки
- Найдите строку `new ""`
- Вставьте перевод между кавычками: `new "Ваш перевод"`
- Сохраните файл

### Шаг 4: Проверьте перевод в игре
- Скопируйте переведенный файл в `_translations/tl/ru/`
- Запустите игру и проверьте результат

## 🎯 Советы по переводу

### ✅ Хорошие практики:
- **Сохраняйте стиль**: фэнтези, средневековье
- **Консистентность**: одинаковые термины переводите одинаково
- **Контекст**: читайте комментарии с номерами строк
- **Тестирование**: проверяйте перевод в игре

### ❌ Чего избегать:
- Не переводите имена персонажей без необходимости
- Не переводите технические теги `{color}`, `{b}`, `{i}`
- Не нарушайте форматирование кавычек
- Не делайте строки слишком длинными для интерфейса

## 🛠️ Полезные команды

### Проверить прогресс:
```bash
python3 translation_helper.py
```

### Применить готовые переводы:
```bash
python3 apply_translations.py
```

### Создать образец для работы:
```bash
# Создает sample_[module].txt с первыми 10 строками
python3 translation_helper.py
```

## 📊 Отслеживание прогресса

Ведите учет в файле `translation_progress.json`:
```json
{
  "options_ru.rpy": {
    "completed": true,
    "translator": "Ваше имя",
    "date": "2024-10-08"
  }
}
```

## 🎮 Тестирование

1. Скопируйте переведенный модуль в `_translations/tl/ru/`
2. Запустите игру
3. Включите русский язык в настройках
4. Проверьте переведенные строки

## 📞 Поддержка

При возникновении проблем:
1. Проверьте синтаксис Ren'Py
2. Убедитесь в правильности кодировки UTF-8
3. Проверьте, что кавычки экранированы правильно

---
**Удачи в переводе! 🎯**
""")
    
    print(f"Создано руководство: {workflow_file}")

def main():
    print("🎯 Настройка рабочего процесса перевода...")
    
    # Создаем шаблон переводов
    create_translation_template()
    
    # Создаем рабочий процесс
    create_translation_workflow()
    
    # Применяем базовые переводы
    print("\n🚀 Применение базовых переводов...")
    quick_translate_simple_modules()
    
    print("\n✅ Готово! Проверьте файлы:")
    print("  - translation_work_plan.md - план работы")
    print("  - TRANSLATION_WORKFLOW.md - инструкция для переводчиков")
    print("  - common_translations.json - шаблон переводов")
    print("  - translation_modules/ - модули для перевода")

if __name__ == "__main__":
    main()
