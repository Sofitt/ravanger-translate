#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re

def split_translation_file():
    """Разделяет большой файл переводов на модули по исходным файлам"""
    
    input_file = "../temp_files/dialogue_keys.txt"
    output_dir = "../translation_modules"
    
    # Создаем папку для модулей
    os.makedirs(output_dir, exist_ok=True)
    
    # Словарь для группировки по файлам
    file_groups = {}
    current_entry = None
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ищем комментарий с именем файла
        if line.startswith('# ') and '.rpy:' in line:
            # Извлекаем имя файла
            file_match = re.search(r'(\w+\.rpy):', line)
            if file_match:
                source_file = file_match.group(1)
                
                # Читаем old строку
                if i + 1 < len(lines) and lines[i + 1].strip().startswith('old '):
                    old_line = lines[i + 1].strip()
                    
                    # Читаем new строку
                    if i + 2 < len(lines) and lines[i + 2].strip().startswith('new '):
                        new_line = lines[i + 2].strip()
                        
                        # Группируем по файлам
                        if source_file not in file_groups:
                            file_groups[source_file] = []
                        
                        file_groups[source_file].append({
                            'comment': line,
                            'old': old_line,
                            'new': new_line
                        })
                        
                        i += 3
                        continue
        
        i += 1
    
    # Создаем файлы для каждой группы
    for source_file, entries in file_groups.items():
        module_name = source_file.replace('.rpy', '_ru.rpy')
        output_path = os.path.join(output_dir, module_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Перевод файла {source_file}\n")
            f.write(f"# Всего строк: {len(entries)}\n\n")
            f.write("translate ru strings:\n\n")
            
            for entry in entries:
                f.write(f"    {entry['comment']}\n")
                f.write(f"    {entry['old']}\n")
                f.write(f"    {entry['new']}\n\n")
        
        print(f"Создан модуль {module_name}: {len(entries)} строк")
    
    # Создаем файл со статистикой
    with open(os.path.join(output_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write("# Модули перевода Ravager\n\n")
        f.write("## Приоритет перевода:\n\n")
        
        # Сортируем по приоритету
        priority_order = [
            'c1.rpy', 'c2_highlands.rpy', 'c2_lowlands.rpy', 'c2_mountains.rpy', 'c2_world.rpy',
            'c3_captives.rpy', 'c3_captures.rpy', 'c3_dreams.rpy', 'c3_hordes.rpy', 'c3_lair.rpy',
            'c4.rpy', 'c4_abbey.rpy', 'c4_capital.rpy', 'c4_cove.rpy', 'c4_farms.rpy', 'c4_fort.rpy',
            'c4_swamp.rpy', 'c4_town.rpy', 'c4_waifu.rpy', 'c4_wildlands.rpy',
            'c5.rpy', 'c5_court.rpy', 'c5_dream.rpy', 'c5_forces.rpy', 'c5_harem.rpy', 'c5_herald.rpy',
            'c6.rpy', 'c6_court.rpy', 'c6_forces.rpy', 'c6_harem.rpy', 'c6_herald.rpy',
            'screens.rpy', 'options.rpy', 'gallery.rpy'
        ]
        
        f.write("### 🎯 Основной сюжет (высокий приоритет):\n")
        for file_name in priority_order[:15]:  # Первые 15 файлов
            if file_name in file_groups:
                count = len(file_groups[file_name])
                f.write(f"- `{file_name.replace('.rpy', '_ru.rpy')}` - {count} строк\n")
        
        f.write("\n### 🎮 Интерфейс и дополнительно:\n")
        for file_name in priority_order[15:]:  # Остальные файлы
            if file_name in file_groups:
                count = len(file_groups[file_name])
                f.write(f"- `{file_name.replace('.rpy', '_ru.rpy')}` - {count} строк\n")
        
        f.write(f"\n**Всего модулей:** {len(file_groups)}\n")
        f.write(f"**Всего строк:** {sum(len(entries) for entries in file_groups.values())}\n")
    
    print(f"\nГотово! Создано {len(file_groups)} модулей в папке '{output_dir}'")
    return output_dir

if __name__ == "__main__":
    split_translation_file()
