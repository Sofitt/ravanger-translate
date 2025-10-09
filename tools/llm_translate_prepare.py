#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Подготовка файлов перевода для обработки через LLM
Преобразует .rpy файлы в JSON формат
"""

import os
import re
import json
import argparse
from typing import List, Dict, Tuple


class TranslationPreparer:
    def __init__(self):
        self.strings = []
    
    def parse_rpy_file(self, file_path: str) -> List[Dict]:
        """Парсит .rpy файл и извлекает структуры для перевода"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Паттерн для поиска блоков перевода
        # Используем (?:[^"\\]|\\.)* для корректной обработки экранированных кавычек
        pattern = r'    # ([^\n]+)\n    old "((?:[^"\\\\]|\\\\.)*)"\n    new "((?:[^"\\\\]|\\\\.)*)"'
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        strings = []
        for idx, (comment, old_text, new_text) in enumerate(matches):
            # Анализируем текст
            analysis = self._analyze_text(old_text)
            
            strings.append({
                "id": idx,
                "comment": comment.strip(),
                "original": old_text,
                "translation": new_text,
                "context": self._detect_context(old_text, comment),
                "tags": analysis["tags"],
                "variables_curly": analysis["variables_curly"],
                "variables_square": analysis["variables_square"],
                "special_chars": analysis["special_chars"]
            })
        
        return strings
    
    def _analyze_text(self, text: str) -> Dict:
        """Анализирует текст и извлекает теги, переменные, спецсимволы"""
        
        # Переменные в фигурных скобках
        variables_curly = re.findall(r'\{(\w+)\}', text)
        
        # Переменные в квадратных скобках
        variables_square = re.findall(r'\[(\w+)\]', text)
        
        # Теги форматирования
        tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', text)
        
        # Спецсимволы
        special_chars = {
            "newlines": text.count('\\n'),
            "tabs": text.count('\\t'),
            "escaped_quotes": text.count('\\"')
        }
        
        return {
            "variables_curly": variables_curly,
            "variables_square": variables_square,
            "tags": tags,
            "special_chars": special_chars
        }
    
    def _detect_context(self, text: str, comment: str) -> str:
        """Определяет контекст строки (диалог, интерфейс, и т.д.)"""
        
        # Интерфейсные строки обычно короткие
        if len(text) < 20 and not any(c in text for c in '.!?'):
            return "ui"
        
        # Названия файлов screen.rpy, options.rpy, gallery.rpy
        if any(name in comment.lower() for name in ['screen', 'option', 'gallery']):
            return "ui"
        
        # Диалоги обычно содержат знаки препинания
        if any(c in text for c in '.!?'):
            return "dialogue"
        
        # Остальное - общий текст
        return "text"
    
    def prepare_module(self, module_file: str, output_file: str):
        """Подготавливает модуль для перевода"""
        
        print(f"📄 Обрабатываю модуль: {module_file}")
        
        strings = self.parse_rpy_file(module_file)
        
        # Подсчет статистики
        total = len(strings)
        translated = sum(1 for s in strings if s["translation"].strip())
        empty = total - translated
        
        metadata = {
            "module": os.path.basename(module_file),
            "module_path": module_file,
            "total_strings": total,
            "translated": translated,
            "untranslated": empty,
            "source_language": "en",
            "target_language": "ru"
        }
        
        output = {
            "metadata": metadata,
            "strings": strings
        }
        
        # Сохраняем JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Подготовлено: {total} строк ({translated} переведено, {empty} пусто)")
        print(f"💾 Сохранено в: {output_file}")
        
        return output
    
    def prepare_batch(self, modules_dir: str, output_dir: str, pattern: str = "*_ru.rpy"):
        """Подготавливает пакет модулей"""
        
        import glob
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        module_files = glob.glob(os.path.join(modules_dir, pattern))
        
        print(f"🔍 Найдено модулей: {len(module_files)}")
        
        for module_file in module_files:
            basename = os.path.basename(module_file).replace('.rpy', '.json')
            output_file = os.path.join(output_dir, basename)
            
            try:
                self.prepare_module(module_file, output_file)
            except Exception as e:
                print(f"❌ Ошибка при обработке {module_file}: {e}")
        
        print(f"\n🎉 Готово! Обработано модулей: {len(module_files)}")


def main():
    parser = argparse.ArgumentParser(description="Подготовка переводов для LLM")
    parser.add_argument("--module", help="Путь к модулю перевода (.rpy)")
    parser.add_argument("--output", help="Путь к выходному JSON файлу")
    parser.add_argument("--batch", help="Обработать все модули в директории")
    parser.add_argument("--batch-output", default="../temp_files/llm_json", 
                       help="Директория для выходных JSON (при --batch)")
    parser.add_argument("--pattern", default="*_ru.rpy",
                       help="Паттерн для поиска файлов (при --batch)")
    
    args = parser.parse_args()
    
    preparer = TranslationPreparer()
    
    if args.batch:
        preparer.prepare_batch(args.batch, args.batch_output, args.pattern)
    elif args.module and args.output:
        preparer.prepare_module(args.module, args.output)
    else:
        # Режим по умолчанию: подготовить все модули
        modules_dir = "../translation_modules"
        output_dir = "../temp_files/llm_json"
        
        print("🚀 Режим пакетной обработки")
        print(f"📁 Входная директория: {modules_dir}")
        print(f"📁 Выходная директория: {output_dir}")
        print()
        
        preparer.prepare_batch(modules_dir, output_dir)


if __name__ == "__main__":
    main()
