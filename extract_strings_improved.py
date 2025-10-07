#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import glob

def is_translatable_string(text):
    """Проверяет, является ли строка переводимой"""
    text = text.strip()
    
    # Исключаем пустые строки
    if not text or len(text) < 2:
        return False
    
    # Исключаем строки только из символов
    if not any(c.isalpha() for c in text):
        return False
    
    # Исключаем технические строки
    technical_patterns = [
        r'^[a-z_]+\s+[a-z_]+',  # команды типа "show character"
        r'^\$',  # переменные
        r'^#',   # комментарии
        r'^\{',  # теги
        r'^if\s+',  # условия
        r'^else',   # else
        r'^elif\s+', # elif
        r'^menu:',   # меню
        r'^label\s+', # метки
        r'^jump\s+',  # переходы
        r'^call\s+',  # вызовы
        r'^return',   # возвраты
        r'^scene\s+', # сцены
        r'^show\s+',  # показ
        r'^hide\s+',  # скрытие
        r'^play\s+',  # воспроизведение
        r'^stop\s+',  # остановка
        r'^pause\s+', # пауза
        r'^with\s+',  # переходы
        r'^window\s+', # окно
        r'^nvl\s+',   # nvl
        r'^\[',       # интерполяция
        r'^define\s+', # определения
        r'^default\s+', # значения по умолчанию
        r'^init\s+',   # инициализация
        r'^transform\s+', # трансформации
        r'^image\s+',     # изображения
        r'^layeredimage\s+', # слоистые изображения
        r'^\w+\s*=',      # присваивания
        r'config\.',      # конфигурация
        r'persistent\.',  # постоянные данные
        r'gui\.',         # GUI
        r'renpy\.',       # renpy функции
        r'\.rpy$',        # имена файлов
        r'\.rpyc$',       # скомпилированные файлы
        r'^\d+$',         # только числа
        r'^[A-Z_]+$',     # константы
        r'^[a-z_]+$',     # переменные
    ]
    
    for pattern in technical_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return False
    
    # Исключаем строки с техническими ключевыми словами
    technical_keywords = [
        'renpy', 'config', 'persistent', 'gui', 'define', 'default',
        'init', 'transform', 'image', 'layeredimage', 'screen',
        'style', 'translate', 'python', 'nvl', 'menu', 'label',
        'jump', 'call', 'return', 'if', 'else', 'elif', 'while',
        'for', 'pass', 'break', 'continue', 'try', 'except',
        'finally', 'with', 'as', 'import', 'from', 'class', 'def'
    ]
    
    text_lower = text.lower()
    for keyword in technical_keywords:
        if keyword in text_lower and len(text) < 50:  # короткие строки с техническими словами
            return False
    
    return True

def extract_dialogue_strings(file_path):
    """Извлекает диалоги и переводимые строки из .rpy файла"""
    strings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except:
        return strings
    
    in_menu = False
    menu_depth = 0
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Пропускаем комментарии и пустые строки
        if not line or line.startswith('#'):
            continue
        
        # Обработка меню
        if line.startswith('menu:'):
            in_menu = True
            menu_depth = 0
            continue
        
        if in_menu:
            if line and not line.startswith(' ') and not line.startswith('\t'):
                in_menu = False
                menu_depth = 0
        
        # Извлекаем строки в кавычках
        quote_patterns = [
            r'"([^"\\]*(?:\\.[^"\\]*)*)"',  # двойные кавычки
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",  # одинарные кавычки
        ]
        
        for pattern in quote_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if is_translatable_string(match):
                    # Добавляем контекст (имя файла и номер строки)
                    context = f"{os.path.basename(file_path)}:{i+1}"
                    strings.append((match.strip(), context))
    
    return strings

def main():
    script_dir = "extracted_scripts"
    output_file = "translation_keys_clean.txt"
    
    all_strings = []
    file_stats = {}
    
    # Обрабатываем все .rpy файлы
    rpy_files = sorted(glob.glob(os.path.join(script_dir, "*.rpy")))
    
    for rpy_file in rpy_files:
        print(f"Обрабатываю {rpy_file}...")
        strings = extract_dialogue_strings(rpy_file)
        all_strings.extend(strings)
        file_stats[rpy_file] = len(strings)
        print(f"  Найдено строк: {len(strings)}")
    
    # Убираем дубликаты, сохраняя контекст
    unique_strings = {}
    for text, context in all_strings:
        if text not in unique_strings:
            unique_strings[text] = []
        unique_strings[text].append(context)
    
    # Сортируем по алфавиту
    sorted_strings = sorted(unique_strings.items())
    
    # Записываем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Ключи для перевода игры Ravager\n")
        f.write(f"# Всего уникальных строк: {len(sorted_strings)}\n")
        f.write("# Формат: Ren'Py translation format\n\n")
        f.write("translate ru strings:\n\n")
        
        for i, (text, contexts) in enumerate(sorted_strings, 1):
            # Записываем контекст как комментарий
            f.write(f"    # {', '.join(contexts[:3])}")  # показываем первые 3 контекста
            if len(contexts) > 3:
                f.write(f" (+{len(contexts)-3} more)")
            f.write("\n")
            
            # Экранируем кавычки в строке
            escaped_text = text.replace('"', '\\"')
            f.write(f'    old "{escaped_text}"\n')
            f.write(f'    new ""\n\n')
    
    # Статистика
    print(f"\nСтатистика по файлам:")
    for file_path, count in file_stats.items():
        print(f"  {os.path.basename(file_path)}: {count} строк")
    
    print(f"\nГотово! Найдено {len(sorted_strings)} уникальных строк для перевода.")
    print(f"Результат сохранен в файл: {output_file}")
    print(f"Формат файла готов для использования в Ren'Py переводах.")

if __name__ == "__main__":
    main()
