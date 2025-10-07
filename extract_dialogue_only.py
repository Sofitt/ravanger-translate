#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob

def is_dialogue_string(text):
    """Проверяет, является ли строка диалогом или интерфейсным текстом"""
    text = text.strip()
    
    # Исключаем пустые строки и очень короткие
    if not text or len(text) < 3:
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
    
    if re.match(r'^[A-Z_]+$', text) and len(text) < 20:  # константы
        return False
    
    if re.match(r'^\w+\s*\(.*\)$', text):  # вызовы функций
        return False
    
    # Исключаем условные выражения
    if re.match(r'^(if|elif|else|and|or|not)\s+', text):
        return False
    
    # Исключаем строки с большим количеством символов подчеркивания (переменные)
    if text.count('_') > len(text) * 0.3:
        return False
    
    return True

def extract_dialogue_from_file(file_path):
    """Извлекает только диалоги из .rpy файла"""
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
        
        # Ищем строки в кавычках
        quote_matches = []
        
        # Двойные кавычки
        for match in re.finditer(r'"([^"\\]*(?:\\.[^"\\]*)*)"', line):
            quote_matches.append(match.group(1))
        
        # Одинарные кавычки
        for match in re.finditer(r"'([^'\\]*(?:\\.[^'\\]*)*)'", line):
            quote_matches.append(match.group(1))
        
        for text in quote_matches:
            if is_dialogue_string(text):
                # Проверяем контекст - это диалог персонажа?
                context_line = original_line.strip()
                
                # Диалоги персонажей обычно имеют формат: character "text"
                # или просто "text" для нарратора
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

def main():
    script_dir = "extracted_scripts"
    output_file = "dialogue_keys.txt"
    
    all_dialogues = []
    file_stats = {}
    
    # Обрабатываем основные файлы сюжета (исключаем технические)
    story_files = [
        'c0_reference.rpy', 'c1.rpy', 
        'c2_highlands.rpy', 'c2_lowlands.rpy', 'c2_mountains.rpy', 'c2_world.rpy',
        'c3_captives.rpy', 'c3_captures.rpy', 'c3_dreams.rpy', 'c3_hordes.rpy', 'c3_lair.rpy',
        'c4.rpy', 'c4_abbey.rpy', 'c4_capital.rpy', 'c4_cove.rpy', 'c4_farms.rpy', 
        'c4_fort.rpy', 'c4_swamp.rpy', 'c4_town.rpy', 'c4_waifu.rpy', 'c4_wildlands.rpy',
        'c5.rpy', 'c5_court.rpy', 'c5_dream.rpy', 'c5_forces.rpy', 'c5_harem.rpy', 'c5_herald.rpy',
        'c6.rpy', 'c6_court.rpy', 'c6_forces.rpy', 'c6_harem.rpy', 'c6_herald.rpy',
        'screens.rpy', 'options.rpy', 'gallery.rpy'
    ]
    
    for filename in story_files:
        file_path = os.path.join(script_dir, filename)
        if os.path.exists(file_path):
            print(f"Обрабатываю {filename}...")
            dialogues = extract_dialogue_from_file(file_path)
            all_dialogues.extend(dialogues)
            file_stats[filename] = len(dialogues)
            print(f"  Найдено диалогов: {len(dialogues)}")
    
    # Убираем дубликаты
    unique_dialogues = {}
    for text, context in all_dialogues:
        if text not in unique_dialogues:
            unique_dialogues[text] = []
        unique_dialogues[text].append(context)
    
    # Сортируем по алфавиту
    sorted_dialogues = sorted(unique_dialogues.items())
    
    # Записываем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Диалоги и интерфейсные строки игры Ravager для перевода\n")
        f.write(f"# Всего уникальных строк: {len(sorted_dialogues)}\n")
        f.write("# Формат: Ren'Py translation format\n\n")
        f.write("translate ru strings:\n\n")
        
        for i, (text, contexts) in enumerate(sorted_dialogues, 1):
            # Записываем контекст как комментарий
            f.write(f"    # {', '.join(contexts[:2])}")  # показываем первые 2 контекста
            if len(contexts) > 2:
                f.write(f" (+{len(contexts)-2} more)")
            f.write("\n")
            
            # Экранируем кавычки в строке
            escaped_text = text.replace('"', '\\"')
            f.write(f'    old "{escaped_text}"\n')
            f.write(f'    new ""\n\n')
    
    # Статистика
    print(f"\nСтатистика по файлам:")
    for filename, count in file_stats.items():
        print(f"  {filename}: {count} диалогов")
    
    print(f"\nГотово! Найдено {len(sorted_dialogues)} уникальных диалогов для перевода.")
    print(f"Результат сохранен в файл: {output_file}")
    print(f"Этот файл содержит только диалоги персонажей и интерфейсные строки.")

if __name__ == "__main__":
    main()
