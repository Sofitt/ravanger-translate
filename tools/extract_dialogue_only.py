#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob

def is_dialogue_string(text):
    """Проверяет, является ли строка диалогом или интерфейсным текстом"""
    text = text.strip()
    
    # Исключаем пустые строки и очень короткие
    if not text or len(text) < 2:
        return False
    
    # Исключаем строки только из символов/чисел
    if not any(c.isalpha() for c in text):
        return False
    
    # Исключаем технические строки
    if any(pattern in text.lower() for pattern in [
        'renpy', 'config.', 'persistent.', 'gui.', '.rpy', '.rpyc',
        'what_suffix', 'who_suffix', 'what_prefix', 'who_prefix',
        'nvl_', 'adv_', 'ctc_', 'cps_', 'cpspt'
    ]):
        return False
    
    # Исключаем строки, которые выглядят как код
    if re.match(r'^[a-z_]+\s*[=<>!]+', text):
        return False
    
    # Разрешаем короткие строки если они в _() функции
    # Константы типа "FFFFFF" - исключаем
    if re.match(r'^[A-F0-9]+$', text):
        return False
    
    # Исключаем условные выражения
    if re.match(r'^(if|elif|else|and|or|not)\s+', text):
        return False
    
    # Исключаем строки с большим количеством символов подчеркивания (переменные)
    if text.count('_') > len(text) * 0.3:
        return False
    
    return True

def extract_dialogue_from_file(file_path):
    """Извлекает диалоги и переводимые строки из .rpy файла"""
    dialogues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        return dialogues
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        original_line = line
        line = line.strip()
        
        # Пропускаем комментарии и пустые строки
        if not line or line.startswith('#'):
            continue
        
        quote_matches = []
        
        # 1. Ищем строки в функции _() - это переводимые строки Ren'Py
        # Примеры: _("Gore"), _("Rape"), _("Some text")
        for match in re.finditer(r'_\("([^"\\]*(?:\\.[^"\\]*)*)"\)', line):
            text = match.group(1)
            quote_matches.append((text, 'translate_function'))
        
        for match in re.finditer(r"_\('([^'\\]*(?:\\.[^'\\]*)*)'\)", line):
            text = match.group(1)
            quote_matches.append((text, 'translate_function'))
        
        # 2. Ищем обычные строки в кавычках
        # Двойные кавычки
        for match in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line):
            text = match.group(1)
            if not line.startswith('_'):  # Не дублируем _() строки
                quote_matches.append((text, 'regular'))
        
        # Одинарные кавычки
        for match in re.finditer(r"'([^'\\]*(?:\\.[^'\\]*)*)'", line):
            text = match.group(1)
            if not line.startswith('_'):
                quote_matches.append((text, 'regular'))
        
        for text, source_type in quote_matches:
            if is_dialogue_string(text):
                context_line = original_line.strip()
                
                # Для _() функций всегда добавляем (это интерфейсные переводы)
                if source_type == 'translate_function':
                    context = f"{os.path.basename(file_path)}:{i+1}"
                    dialogues.append((text.strip(), context))
                    continue
                
                # Для обычных строк проверяем контекст
                is_character_dialogue = (
                    # Прямой диалог персонажа
                    re.match(r'^\s*\w+\s+"', context_line) or
                    # Диалог нарратора
                    re.match(r'^\s*"', context_line) or
                    # Центрированный текст
                    'centered' in context_line or
                    # Меню выборов
                    context_line.strip().startswith('"') and len(context_line.strip()) > 10
                )
                
                if is_character_dialogue:
                    context = f"{os.path.basename(file_path)}:{i+1}"
                    dialogues.append((text.strip(), context))
    
    return dialogues

def extract_all_dialogue():
    """Извлекает все диалоги из всех .rpy файлов"""
    print("🔍 Извлечение диалогов и переводимых строк...")
    
    all_dialogues = {}
    
    # Ищем все .rpy файлы в extracted_scripts
    script_files = glob.glob('extracted_scripts/*.rpy')
    
    total_files = len(script_files)
    for idx, file_path in enumerate(script_files, 1):
        print(f"  [{idx}/{total_files}] {os.path.basename(file_path)}", end='\r')
        
        dialogues = extract_dialogue_from_file(file_path)
        
        for text, context in dialogues:
            if text not in all_dialogues:
                all_dialogues[text] = []
            all_dialogues[text].append(context)
    
    print(f"\n✅ Обработано файлов: {total_files}")
    print(f"✅ Уникальных строк: {len(all_dialogues)}")
    
    return all_dialogues

def save_dialogue_keys(dialogues, output_file):
    """Сохраняет ключи переводов в файл"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Диалоги и интерфейсные строки игры Ravager для перевода\n")
        f.write(f"# Всего уникальных строк: {len(dialogues)}\n")
        f.write("# Формат: Ren'Py translation format\n\n")
        f.write("translate ru strings:\n\n")
        
        for text in sorted(dialogues.keys()):
            contexts = dialogues[text]
            # Ограничиваем количество контекстов для читабельности
            context_list = ', '.join(contexts[:5])
            if len(contexts) > 5:
                context_list += f" (+{len(contexts)-5} more)"
            
            f.write(f"    # {context_list}\n")
            f.write(f'    old "{text}"\n')
            f.write(f'    new ""\n\n')
    
    print(f"💾 Сохранено в: {output_file}")

if __name__ == "__main__":
    # Извлекаем диалоги
    dialogues = extract_all_dialogue()
    
    # Сохраняем в файл
    save_dialogue_keys(dialogues, "temp_files/dialogue_keys_new.txt")
    
    print("\n🎉 Готово!")
