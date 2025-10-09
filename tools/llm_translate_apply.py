#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Применение переводов из JSON обратно в .rpy файлы
"""

import os
import re
import json
import argparse
from typing import Dict, List, Tuple


class TranslationApplicator:
    """Применяет переводы из JSON в .rpy файлы"""
    
    def __init__(self):
        self.stats = {
            "total": 0,
            "applied": 0,
            "skipped_empty": 0,
            "skipped_exists": 0,
            "errors": 0
        }
    
    def load_json(self, json_file: str) -> Dict:
        """Загружает JSON с переводами"""
        
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_rpy(self, rpy_file: str) -> str:
        """Загружает содержимое .rpy файла"""
        
        with open(rpy_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    def save_rpy(self, rpy_file: str, content: str):
        """Сохраняет содержимое в .rpy файл"""
        
        with open(rpy_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def create_translations_map(self, strings: List[Dict]) -> Dict[str, str]:
        """Создает маппинг оригинал -> перевод"""
        
        translations_map = {}
        
        for string_obj in strings:
            original = string_obj["original"]
            translation = string_obj.get("translation", "").strip()
            
            if translation:
                translations_map[original] = translation
        
        return translations_map
    
    def apply_translations(self, rpy_content: str, translations_map: Dict[str, str]) -> str:
        """Применяет переводы к содержимому .rpy файла"""
        
        # Паттерн для поиска блоков перевода
        pattern = r'(    # [^\n]+\n    old "([^"]+)"\n    new ")([^"]*)(")'
        
        def replace_translation(match):
            full_match = match.group(0)
            prefix = match.group(1)
            old_text = match.group(2)
            current_translation = match.group(3)
            suffix = match.group(4)
            
            self.stats["total"] += 1
            
            # Проверяем, есть ли новый перевод
            if old_text in translations_map:
                new_translation = translations_map[old_text]
                
                # Если текущий перевод пустой - применяем новый
                if not current_translation.strip():
                    self.stats["applied"] += 1
                    return f'{prefix}{new_translation}{suffix}'
                else:
                    # Если уже есть перевод - пропускаем (или заменяем по желанию)
                    self.stats["skipped_exists"] += 1
                    return full_match
            else:
                # Нет нового перевода - оставляем как есть
                if not current_translation.strip():
                    self.stats["skipped_empty"] += 1
                return full_match
        
        # Применяем замены
        new_content = re.sub(pattern, replace_translation, rpy_content)
        
        return new_content
    
    def apply_json_to_rpy(self, json_file: str, rpy_file: str, output_file: str = None):
        """Применяет переводы из JSON в .rpy файл"""
        
        print(f"📄 Загружаю JSON: {json_file}")
        data = self.load_json(json_file)
        
        metadata = data.get("metadata", {})
        strings = data.get("strings", [])
        
        print(f"📊 Модуль: {metadata.get('module', 'unknown')}")
        print(f"📊 Всего строк в JSON: {len(strings)}")
        print(f"📊 Переведено в JSON: {metadata.get('translated', 0)}")
        print()
        
        # Создаем маппинг переводов
        translations_map = self.create_translations_map(strings)
        print(f"🔄 Переводов для применения: {len(translations_map)}")
        print()
        
        # Загружаем .rpy файл
        if not os.path.exists(rpy_file):
            print(f"❌ Файл не найден: {rpy_file}")
            return
        
        print(f"📄 Загружаю .rpy: {rpy_file}")
        rpy_content = self.load_rpy(rpy_file)
        
        # Применяем переводы
        print(f"🔄 Применяю переводы...")
        new_content = self.apply_translations(rpy_content, translations_map)
        
        # Сохраняем результат
        output = output_file or rpy_file
        print(f"💾 Сохраняю в: {output}")
        self.save_rpy(output, new_content)
        
        # Статистика
        print()
        print(f"📊 Статистика применения:")
        print(f"  📝 Всего блоков: {self.stats['total']}")
        print(f"  ✅ Применено: {self.stats['applied']}")
        print(f"  ⏭️  Пропущено (уже переведено): {self.stats['skipped_exists']}")
        print(f"  ⏸️  Пропущено (нет перевода): {self.stats['skipped_empty']}")
        
        if self.stats["errors"] > 0:
            print(f"  ❌ Ошибки: {self.stats['errors']}")
    
    def apply_batch(self, json_dir: str, rpy_dir: str, output_dir: str = None):
        """Применяет переводы из пакета JSON файлов"""
        
        import glob
        
        json_files = glob.glob(os.path.join(json_dir, "*.json"))
        
        print(f"🔍 Найдено JSON файлов: {len(json_files)}")
        print()
        
        for json_file in json_files:
            # Определяем соответствующий .rpy файл
            json_basename = os.path.basename(json_file)
            # Убираем _translated если есть
            json_basename = json_basename.replace('_translated.json', '.json')
            basename = json_basename.replace('.json', '.rpy')
            rpy_file = os.path.join(rpy_dir, basename)
            
            if not os.path.exists(rpy_file):
                print(f"⚠️  .rpy файл не найден для {basename}, пропускаю...")
                continue
            
            # Определяем выходной файл
            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_file = os.path.join(output_dir, basename)
            else:
                output_file = rpy_file  # Перезаписываем исходный
            
            print(f"{'='*60}")
            self.apply_json_to_rpy(json_file, rpy_file, output_file)
            print()
            
            # Сброс статистики для следующего файла
            self.stats = {
                "total": 0,
                "applied": 0,
                "skipped_empty": 0,
                "skipped_exists": 0,
                "errors": 0
            }


def main():
    parser = argparse.ArgumentParser(description="Применение переводов из JSON в .rpy")
    parser.add_argument("--input", help="Входной JSON файл")
    parser.add_argument("--module", help="Целевой .rpy файл модуля")
    parser.add_argument("--output", help="Выходной .rpy файл (опционально)")
    parser.add_argument("--batch-json", help="Директория с JSON файлами (пакетный режим)")
    parser.add_argument("--batch-rpy", help="Директория с .rpy файлами (пакетный режим)")
    parser.add_argument("--batch-output", help="Директория для выходных .rpy (пакетный режим)")
    
    args = parser.parse_args()
    
    applicator = TranslationApplicator()
    
    if args.batch_json and args.batch_rpy:
        # Пакетный режим
        print("🚀 Режим пакетной обработки")
        print(f"📁 JSON директория: {args.batch_json}")
        print(f"📁 .rpy директория: {args.batch_rpy}")
        if args.batch_output:
            print(f"📁 Выходная директория: {args.batch_output}")
        else:
            print(f"⚠️  Исходные файлы будут перезаписаны!")
        print()
        
        applicator.apply_batch(args.batch_json, args.batch_rpy, args.batch_output)
        
    elif args.input and args.module:
        # Одиночный режим
        applicator.apply_json_to_rpy(args.input, args.module, args.output)
        
    else:
        # Режим по умолчанию: применить все из temp_files/llm_json
        json_dir = "../temp_files/llm_json"
        rpy_dir = "../translation_modules"
        
        print("🚀 Режим по умолчанию: применение всех переводов")
        print(f"📁 JSON директория: {json_dir}")
        print(f"📁 .rpy директория: {rpy_dir}")
        print(f"⚠️  Исходные файлы будут перезаписаны!")
        print()
        
        applicator.apply_batch(json_dir, rpy_dir)
    
    print("\n🎉 Готово!")


if __name__ == "__main__":
    main()
