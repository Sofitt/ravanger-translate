#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import glob
import argparse
from typing import Dict, List, Tuple, Optional
from create_ru_ui_fix import create_ui_fix

class SmartTranslationPacker:
    def __init__(self, quiet=False):
        self.existing_translations = {}  # {key: (value, source_file, line_num)}
        self.new_translations = {}       # {key: (value, source_file, comment)}
        self.quiet = quiet
    
    def log(self, message):
        """Выводит сообщение если не в тихом режиме"""
        if not self.quiet:
            print(message)
    
    def log_error(self, message):
        """Всегда выводит ошибки"""
        print(message)

    def parse_translation_file(self, file_path: str) -> Dict[str, Tuple[str, str, str]]:
        """Парсит файл перевода и возвращает словарь переводов"""
        translations = {}

        if not os.path.exists(file_path):
            return translations

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Находим все блоки переводов
        pattern = r'    # ([^\n]+)\n    old "([^"]+)"\n    new "([^"]*)"'
        matches = re.findall(pattern, content)

        for comment, old_text, new_text in matches:
            # Нормализуем ключ для сравнения (убираем кавычки для проверки дубликатов)
            normalized_key = old_text.strip().strip("'\"")

            # Если ключ уже есть, пропускаем дубликат
            if normalized_key in translations:
                self.log(f"  ⚠️  Пропущен дубликат: {old_text}")
                continue

            translations[normalized_key] = (new_text, file_path, comment, old_text)

        return translations

    def load_existing_translations(self, translations_dir: str):
        """Загружает существующие переводы из всех файлов"""
        self.log("🔍 Загружаю существующие переводы...")

        if not os.path.exists(translations_dir):
            self.log_error(f"Папка {translations_dir} не найдена")
            return

        for filename in os.listdir(translations_dir):
            if filename.endswith('.rpy'):
                file_path = os.path.join(translations_dir, filename)
                file_translations = self.parse_translation_file(file_path)

                for key, (value, source, comment, original_key) in file_translations.items():
                    if key in self.existing_translations:
                        self.log(f"⚠️  Дубликат найден: {key} в {filename}")
                    else:
                        self.existing_translations[key] = (value, filename, comment, original_key)

                self.log(f"  📄 {filename}: {len(file_translations)} переводов")

        self.log(f"✅ Загружено {len(self.existing_translations)} существующих переводов")

    def load_new_translations(self, modules_dir: str):
        """Загружает новые переводы из модулей"""
        self.log("🆕 Загружаю новые переводы...")

        if not os.path.exists(modules_dir):
            self.log_error(f"Папка {modules_dir} не найдена")
            return

        for filename in os.listdir(modules_dir):
            if filename.endswith('_ru.rpy'):
                file_path = os.path.join(modules_dir, filename)
                file_translations = self.parse_translation_file(file_path)

                for key, (value, source, comment, original_key) in file_translations.items():
                    self.new_translations[key] = (value, filename, comment, original_key)

                self.log(f"  📄 {filename}: {len(file_translations)} переводов")

        self.log(f"✅ Загружено {len(self.new_translations)} новых переводов")

    def merge_translations(self) -> Dict[str, Tuple[str, str, str]]:
        """Объединяет переводы по правилам:
        - Если новый перевод пустой, оставляем старый
        - Если новый перевод не пустой, заменяем старый
        - Если ключа не было, добавляем новый
        - Если итоговый перевод пустой, заполняем оригинальным текстом
        """
        self.log("🔄 Объединяю переводы...")

        merged = {}
        stats = {
            'kept_old': 0,          # Оставили старый перевод
            'updated': 0,           # Обновили перевод
            'added_new': 0,         # Добавили новый
            'duplicates': 0,        # Найдено дубликатов
            'filled_original': 0    # Заполнено оригиналом
        }

        # Начинаем с существующих переводов
        for key, (value, source, comment, original_key) in self.existing_translations.items():
            merged[key] = (value, source, comment, original_key)

        # Обрабатываем новые переводы
        for key, (new_value, new_source, new_comment, new_original_key) in self.new_translations.items():
            if key in merged:
                old_value, old_source, old_comment, old_original_key = merged[key]
                stats['duplicates'] += 1

                if new_value.strip():  # Новый перевод не пустой
                    merged[key] = (new_value, new_source, new_comment, new_original_key)
                    stats['updated'] += 1
                    self.log(f"  🔄 Обновлен: {key[:50]}... -> {new_value[:30]}...")
                else:  # Новый перевод пустой, оставляем старый
                    stats['kept_old'] += 1
                    self.log(f"  ⏸️  Оставлен: {key[:50]}... = {old_value[:30]}...")
            else:
                # Новый ключ
                merged[key] = (new_value, new_source, new_comment, new_original_key)
                stats['added_new'] += 1

        # Заполняем пустые переводы оригинальным текстом
        for key, (value, source, comment, original_key) in list(merged.items()):
            if not value.strip():  # Перевод пустой
                merged[key] = (key, source, comment, original_key)
                stats['filled_original'] += 1

        self.log(f"\n📊 Статистика объединения:")
        self.log(f"  🆕 Добавлено новых: {stats['added_new']}")
        self.log(f"  🔄 Обновлено: {stats['updated']}")
        self.log(f"  ⏸️  Оставлено старых: {stats['kept_old']}")
        self.log(f"  🔍 Найдено дубликатов: {stats['duplicates']}")
        self.log(f"  📝 Заполнено оригиналом: {stats['filled_original']}")
        self.log(f"  📊 Итого переводов: {len(merged)}")

        return merged

    def group_by_source_file(self, translations: Dict[str, Tuple[str, str, str]]) -> Dict[str, List]:
        """Группирует переводы по исходным файлам"""
        grouped = {}

        for key, (value, source, comment, original_key) in translations.items():
            # Определяем целевой файл на основе источника
            if source.endswith('_ru.rpy'):
                target_file = source.replace('_ru.rpy', '.rpy')
            else:
                target_file = source

            if target_file not in grouped:
                grouped[target_file] = []

            # Используем оригинальный ключ для записи
            grouped[target_file].append((original_key, value, comment))

        return grouped

    def write_translation_file(self, file_path: str, translations: List[Tuple[str, str, str]]):
        """Записывает файл перевода"""
        base_name = os.path.basename(file_path).replace('.rpy', '')

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Перевод файла {base_name}.rpy\n")
            f.write(f"# Всего строк: {len(translations)}\n\n")
            f.write("translate ru strings:\n\n")

            for key, value, comment in sorted(translations):
                f.write(f"    # {comment}\n")
                f.write(f'    old "{key}"\n')
                f.write(f'    new "{value}"\n\n')

    def convert_json_to_rpy(self, json_dir: str, output_dir: str):
        """Конвертирует *_translated.json в *.rpy файлы для translation_modules"""
        self.log(f"🔄 Конвертирую JSON -> RPY...")
        self.log(f"   Источник: {json_dir}")
        self.log(f"   Назначение: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Находим все *_translated.json файлы
        json_files = glob.glob(os.path.join(json_dir, "*_translated.json"))
        
        if not json_files:
            self.log_error(f"⚠️  Не найдено файлов *_translated.json в {json_dir}")
            return 0
        
        converted_count = 0
        
        for json_file in json_files:
            basename = os.path.basename(json_file)
            module_name = basename.replace('_translated.json', '')
            output_file = os.path.join(output_dir, f"{module_name}_ru.rpy")
            
            try:
                # Загружаем JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get("metadata", {})
                strings = data.get("strings", [])
                
                # Фильтруем только переведенные строки
                translated_strings = [
                    s for s in strings 
                    if s.get("translation", "").strip()
                ]
                
                if not translated_strings:
                    self.log(f"  ⚠️  {module_name}: нет переведенных строк, пропускаю")
                    continue
                
                # Создаем .rpy файл
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Перевод файла {module_name}.rpy\n")
                    f.write(f"# Всего строк: {len(translated_strings)}\n")
                    f.write(f"# Источник: {basename}\n\n")
                    f.write("translate ru strings:\n\n")
                    
                    for s in translated_strings:
                        original = s["original"]
                        translation = s["translation"]
                        speaker = s.get("speaker", "")
                        context = s.get("context", "")
                        
                        # Формируем комментарий
                        comment_parts = []
                        if speaker and speaker != "narrator":
                            comment_parts.append(speaker)
                        if context:
                            comment_parts.append(context)
                        
                        comment = " - ".join(comment_parts) if comment_parts else module_name
                        
                        f.write(f"    # {comment}\n")
                        f.write(f'    old "{original}"\n')
                        f.write(f'    new "{translation}"\n\n')
                
                converted_count += 1
                self.log(f"  ✅ {module_name}_ru.rpy: {len(translated_strings)} переводов")
                
            except Exception as e:
                self.log_error(f"  ❌ Ошибка при конвертации {basename}: {e}")
        
        self.log(f"\n✅ Конвертировано файлов: {converted_count}")
        return converted_count

    def pack_to_game(self, output_dir: str):
        """Упаковывает переводы в игру"""
        self.log(f"📦 Упаковка переводов в {output_dir}...")

        # Создаем выходную папку
        os.makedirs(output_dir, exist_ok=True)

        # Объединяем переводы
        merged_translations = self.merge_translations()

        # Группируем по файлам
        grouped = self.group_by_source_file(merged_translations)

        # Записываем файлы
        for target_file, translations in grouped.items():
            output_path = os.path.join(output_dir, target_file)
            self.write_translation_file(output_path, translations)
            self.log(f"  ✅ {target_file}: {len(translations)} переводов")

        self.log(f"🎉 Упаковка завершена! Создано {len(grouped)} файлов")

        return len(grouped), len(merged_translations)

def main():
    parser = argparse.ArgumentParser(description="Умная упаковка переводов в игру")
    parser.add_argument('--quiet', '-q', action='store_true', 
                       help='Тихий режим (выводить только ошибки)')
    args = parser.parse_args()
    
    packer = SmartTranslationPacker(quiet=args.quiet)

    # Шаг 1: Конвертируем JSON переводы в RPY файлы
    packer.log("="*70)
    packer.log("ШАГ 1: КОНВЕРТАЦИЯ JSON -> RPY")
    packer.log("="*70)
    json_dir = "../temp_files/llm_json_v2"
    modules_dir = "../translation_modules"
    
    converted = packer.convert_json_to_rpy(json_dir, modules_dir)
    
    if converted == 0:
        packer.log_error(f"\n⚠️  Нет переведенных файлов для упаковки")
        packer.log_error(f"   Запустите сначала перевод: ./llm_batch_translate.sh --translate-only")
        return

    # Шаг 2: Отключаем оригинальные архивы переводов
    packer.log("\n" + "="*70)
    packer.log("ШАГ 2: ОТКЛЮЧЕНИЕ ОРИГИНАЛЬНЫХ АРХИВОВ")
    packer.log("="*70)
    translation_archives = ["../game/Translations.rpa", "../game/translations.rpa"]
    for archive in translation_archives:
        if os.path.exists(archive):
            disabled_name = archive + ".disabled"
            if not os.path.exists(disabled_name):
                os.rename(archive, disabled_name)
                packer.log(f"  ✅ Отключен: {archive} -> {disabled_name}")

    # Шаг 3: Загружаем существующие переводы из game/tl/ru
    packer.log("\n" + "="*70)
    packer.log("ШАГ 3: ЗАГРУЗКА СУЩЕСТВУЮЩИХ ПЕРЕВОДОВ")
    packer.log("="*70)
    packer.load_existing_translations("../game/tl/ru")

    # Шаг 4: Загружаем новые переводы из модулей
    packer.log("\n" + "="*70)
    packer.log("ШАГ 4: ЗАГРУЗКА НОВЫХ ПЕРЕВОДОВ")
    packer.log("="*70)
    packer.load_new_translations("../translation_modules")

    # Шаг 5: Упаковываем в игру
    packer.log("\n" + "="*70)
    packer.log("ШАГ 5: УПАКОВКА В ИГРУ")
    packer.log("="*70)
    files_count, translations_count = packer.pack_to_game("../game/tl/ru")

    # Шаг 6: Создаем настройки интерфейса для русского языка
    packer.log("\n" + "="*70)
    packer.log("ШАГ 6: НАСТРОЙКА ИНТЕРФЕЙСА")
    packer.log("="*70)
    create_ui_fix()

    packer.log(f"\n🎯 Готово к тестированию!")
    packer.log(f"   Файлов: {files_count}")
    packer.log(f"   Переводов: {translations_count}")
    packer.log(f"   Оригинальные архивы отключены для избежания конфликтов")
    packer.log(f"   Запустите игру и выберите русский язык")
    packer.log(f"\n💡 Для восстановления оригинальных переводов:")
    packer.log(f"   mv __test__/Translations.rpa.disabled game/Translations.rpa")

if __name__ == "__main__":
    main()
