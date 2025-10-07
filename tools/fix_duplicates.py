#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import os

def fix_translation_duplicates(file_path):
    """Исправляет дубликаты в файле перевода"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все пары old/new
    pattern = r'    # ([^\n]+)\n    old "([^"]+)"\n    new "([^"]*)"'
    matches = re.findall(pattern, content)
    
    # Группируем по old строкам
    seen_old = {}
    unique_translations = []
    
    for comment, old_text, new_text in matches:
        # Нормализуем old_text для сравнения (убираем кавычки и пробелы)
        normalized = old_text.strip("'\"").strip()
        
        if normalized not in seen_old:
            seen_old[normalized] = True
            unique_translations.append((comment, old_text, new_text))
        else:
            print(f"Удален дубликат: {old_text}")
    
    # Создаем новый файл
    new_content = "# Перевод файла c0_reference.rpy\n"
    new_content += f"# Всего строк: {len(unique_translations)}\n\n"
    new_content += "translate ru strings:\n\n"
    
    for comment, old_text, new_text in unique_translations:
        new_content += f"    # {comment}\n"
        new_content += f'    old "{old_text}"\n'
        new_content += f'    new "{new_text}"\n\n'
    
    # Сохраняем исправленный файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Исправлен файл: {file_path}")
    print(f"Уникальных переводов: {len(unique_translations)}")

if __name__ == "__main__":
    fix_translation_duplicates("game/tl/ru/c0_reference.rpy")
