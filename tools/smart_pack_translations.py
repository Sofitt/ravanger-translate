#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from typing import Dict, List, Tuple, Optional

class SmartTranslationPacker:
    def __init__(self):
        self.existing_translations = {}  # {key: (value, source_file, line_num)}
        self.new_translations = {}       # {key: (value, source_file, comment)}

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
                print(f"  ⚠️  Пропущен дубликат: {old_text}")
                continue

            translations[normalized_key] = (new_text, file_path, comment, old_text)

        return translations

    def load_existing_translations(self, translations_dir: str):
        """Загружает существующие переводы из всех файлов"""
        print("🔍 Загружаю существующие переводы...")

        if not os.path.exists(translations_dir):
            print(f"Папка {translations_dir} не найдена")
            return

        for filename in os.listdir(translations_dir):
            if filename.endswith('.rpy'):
                file_path = os.path.join(translations_dir, filename)
                file_translations = self.parse_translation_file(file_path)

                for key, (value, source, comment, original_key) in file_translations.items():
                    if key in self.existing_translations:
                        print(f"⚠️  Дубликат найден: {key} в {filename}")
                    else:
                        self.existing_translations[key] = (value, filename, comment, original_key)

                print(f"  📄 {filename}: {len(file_translations)} переводов")

        print(f"✅ Загружено {len(self.existing_translations)} существующих переводов")

    def load_new_translations(self, modules_dir: str):
        """Загружает новые переводы из модулей"""
        print("🆕 Загружаю новые переводы...")

        if not os.path.exists(modules_dir):
            print(f"Папка {modules_dir} не найдена")
            return

        for filename in os.listdir(modules_dir):
            if filename.endswith('_ru.rpy'):
                file_path = os.path.join(modules_dir, filename)
                file_translations = self.parse_translation_file(file_path)

                for key, (value, source, comment, original_key) in file_translations.items():
                    self.new_translations[key] = (value, filename, comment, original_key)

                print(f"  📄 {filename}: {len(file_translations)} переводов")

        print(f"✅ Загружено {len(self.new_translations)} новых переводов")

    def merge_translations(self) -> Dict[str, Tuple[str, str, str]]:
        """Объединяет переводы по правилам:
        - Если новый перевод пустой, оставляем старый
        - Если новый перевод не пустой, заменяем старый
        - Если ключа не было, добавляем новый
        - Если итоговый перевод пустой, заполняем оригинальным текстом
        """
        print("🔄 Объединяю переводы...")

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
                    print(f"  🔄 Обновлен: {key[:50]}... -> {new_value[:30]}...")
                else:  # Новый перевод пустой, оставляем старый
                    stats['kept_old'] += 1
                    print(f"  ⏸️  Оставлен: {key[:50]}... = {old_value[:30]}...")
            else:
                # Новый ключ
                merged[key] = (new_value, new_source, new_comment, new_original_key)
                stats['added_new'] += 1

        # Заполняем пустые переводы оригинальным текстом
        for key, (value, source, comment, original_key) in list(merged.items()):
            if not value.strip():  # Перевод пустой
                merged[key] = (key, source, comment, original_key)
                stats['filled_original'] += 1

        print(f"\n📊 Статистика объединения:")
        print(f"  🆕 Добавлено новых: {stats['added_new']}")
        print(f"  🔄 Обновлено: {stats['updated']}")
        print(f"  ⏸️  Оставлено старых: {stats['kept_old']}")
        print(f"  🔍 Найдено дубликатов: {stats['duplicates']}")
        print(f"  📝 Заполнено оригиналом: {stats['filled_original']}")
        print(f"  📊 Итого переводов: {len(merged)}")

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

    def pack_to_game(self, output_dir: str):
        """Упаковывает переводы в игру"""
        print(f"📦 Упаковка переводов в {output_dir}...")

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
            print(f"  ✅ {target_file}: {len(translations)} переводов")

        print(f"🎉 Упаковка завершена! Создано {len(grouped)} файлов")

        return len(grouped), len(merged_translations)

def main():
    packer = SmartTranslationPacker()

    # Отключаем оригинальные архивы переводов для избежания конфликтов
    print("🔧 Отключение оригинальных архивов переводов...")
    translation_archives = ["../game/Translations.rpa", "../game/translations.rpa"]
    for archive in translation_archives:
        if os.path.exists(archive):
            disabled_name = archive + ".disabled"
            if not os.path.exists(disabled_name):
                os.rename(archive, disabled_name)
                print(f"  ✅ Отключен: {archive} -> {disabled_name}")

    # Загружаем существующие переводы из _translations
    packer.load_existing_translations("../_translations/tl/ru")

    # Загружаем новые переводы из модулей
    packer.load_new_translations("../translation_modules")

    # Упаковываем в игру
    files_count, translations_count = packer.pack_to_game("../game/tl/ru")

    print(f"\n🎯 Готово к тестированию!")
    print(f"   Файлов: {files_count}")
    print(f"   Переводов: {translations_count}")
    print(f"   Оригинальные архивы отключены для избежания конфликтов")
    print(f"   Запустите игру и выберите русский язык")
    print(f"\n💡 Для восстановления оригинальных переводов:")
    print(f"   mv __test__/Translations.rpa.disabled game/Translations.rpa")

if __name__ == "__main__":
    main()
