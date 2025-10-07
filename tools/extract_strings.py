#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob

def extract_translatable_strings(file_path):
    """Извлекает переводимые строки из .rpy файла"""
    strings = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Регулярные выражения для поиска переводимых строк
    patterns = [
        # Диалоги персонажей: "Текст"
        r'"([^"\\]*(\\.[^"\\]*)*)"',
        # Строки в одинарных кавычках: 'Текст'
        r"'([^'\\]*(\\.[^'\\]*)*)'",
        # Функция _(): _("Текст")
        r'_\("([^"\\]*(\\.[^"\\]*)*)"\)',
        r"_\('([^'\\]*(\\.[^'\\]*)*)'\)",
        # Меню и выборы
        r'menu:\s*\n\s*"([^"\\]*(\\.[^"\\]*)*)"',
        # centered "Текст"
        r'centered\s+"([^"\\]*(\\.[^"\\]*)*)"',
        # show/hide text
        r'show\s+text\s+"([^"\\]*(\\.[^"\\]*)*)"',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            if isinstance(match, tuple):
                text = match[0]
            else:
                text = match
            
            # Фильтруем строки
            if text and len(text.strip()) > 0:
                # Исключаем технические строки
                if not any(skip in text.lower() for skip in [
                    'renpy', 'config.', 'persistent.', 'gui.', 'define',
                    'label ', 'jump ', 'call ', 'return', 'if ', 'else:',
                    'menu:', 'scene ', 'show ', 'hide ', 'play ', 'stop ',
                    'pause ', 'with ', '$', '{', '}', 'nvl', 'window'
                ]):
                    # Исключаем очень короткие строки и числа
                    if len(text.strip()) > 2 and not text.strip().isdigit():
                        strings.append(text.strip())
    
    return list(set(strings))  # Убираем дубликаты

def main():
    script_dir = "extracted_scripts"
    output_file = "translation_keys.txt"
    
    all_strings = []
    
    # Обрабатываем все .rpy файлы
    for rpy_file in glob.glob(os.path.join(script_dir, "*.rpy")):
        print(f"Обрабатываю {rpy_file}...")
        strings = extract_translatable_strings(rpy_file)
        all_strings.extend(strings)
        print(f"  Найдено строк: {len(strings)}")
    
    # Убираем дубликаты
    unique_strings = list(set(all_strings))
    unique_strings.sort()
    
    # Записываем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Ключи для перевода игры Ravager\n")
        f.write(f"# Всего строк: {len(unique_strings)}\n\n")
        
        for i, string in enumerate(unique_strings, 1):
            f.write(f"# {i:04d}\n")
            f.write(f'old "{string}"\n')
            f.write(f'new ""\n\n')
    
    print(f"\nГотово! Найдено {len(unique_strings)} уникальных строк для перевода.")
    print(f"Результат сохранен в файл: {output_file}")

if __name__ == "__main__":
    main()
