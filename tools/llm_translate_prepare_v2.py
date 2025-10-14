#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Подготовка файлов перевода для обработки через LLM (версия 2)
С поддержкой извлечения информации о персонажах
Работает с исходными .rpy файлами из extracted_scripts/
"""

import os
import re
import json
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict


class TranslationPreparerV2:
    # Служебные слова RenPy, которые не являются персонажами
    RENPY_KEYWORDS = {
        'if', 'else', 'elif', 'while', 'for', 'pass', 'return', 'jump', 'call',
        'menu', 'centered', 'extend', 'nvl', 'scene', 'show', 'hide', 'with',
        'window', 'play', 'stop', 'pause', 'define', 'default', 'label', 'init',
        'python', 'transform', 'image', 'screen', 'style', 'translate', 'narrator',
        'pov', 'variant', 'textbutton', 'text_selected_color', 'text_hover_color',
        'text_font', 'text_color', 'text', 'style_suffix', 'layout',
        'mousewheel', 'scrollbars', 'size_group', 'style_group', 'style_prefix',
        'add', 'alt', 'auto','background', 'draggable', 'font', 'foreground',
        'hover_background', 'id', 'idle', 'key', 'thumb', 'fmw'
    }

    def __init__(self):
        self.strings = []
        self.character_entities = set()  # Все найденные сущности персонажей

    def parse_rpy_source(self, file_path: str) -> Tuple[List[Dict], Set[str]]:
        """Парсит исходный .rpy файл и извлекает переводимые строки с контекстом персонажей"""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        strings = []
        character_entities = set()
        current_speaker = None  # Текущий говорящий (из show или предыдущей реплики)
        seen_texts = set()  # Отслеживание дубликатов

        idx = 0
        for line_num, line in enumerate(lines, 1):
            # Пропускаем комментарии и пустые строки
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            # Команда show - определяем текущего персонажа
            show_match = re.match(r'\s+show\s+(\w+)', line)
            if show_match:
                current_speaker = show_match.group(1)
                continue

            # Скрываем персонажа
            hide_match = re.match(r'\s+hide\s+(\w+)', line)
            if hide_match:
                if current_speaker == hide_match.group(1):
                    current_speaker = None
                continue

            # Паттерн для textbutton (ДОЛЖЕН БЫТЬ ПЕРЕД dialog_match!)
            # Формат: textbutton "текст": или textbutton 'текст':
            textbutton_match = re.match(r'\s+textbutton\s+["\'](.+?)["\']\s*:', line)
            if textbutton_match:
                text = textbutton_match.group(1)
                
                # Сохраняем полную оригинальную строку для упаковки
                original_line = line.strip()
                
                # Проверка: если после текста идёт условие
                remaining_line = line[textbutton_match.end():]
                has_condition = ('==' in remaining_line or 'True' in remaining_line or 'False' in remaining_line)
                
                # Пропускаем пустые и очень короткие строки
                if not text.strip() or len(text.strip()) < 2:
                    continue
                
                # Пропускаем hex цвета
                if re.match(r'^#[0-9a-fA-F]+$', text.strip()):
                    continue
                
                analysis = self._analyze_text(text)
                
                string_obj = {
                    "id": idx,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                    "speaker": "ui",
                    "speaker_prefix": "ui",
                    "original": text,
                    "translation": "",
                    "context": "ui",
                    "tags": analysis["tags"],
                    "variables_curly": analysis["variables_curly"],
                    "variables_square": analysis["variables_square"],
                    "special_chars": analysis["special_chars"]
                }
                
                # Если есть условие - сохраняем полную строку для упаковки
                if has_condition:
                    string_obj["original_full"] = original_line
                
                strings.append(string_obj)
                
                idx += 1
                continue

            # Паттерн для menu items
            # Формат: "текст": или 'текст': (может быть с условием между кавычкой и двоеточием)
            # Ловим двойные и одинарные кавычки отдельно, чтобы не пересекались
            menu_match = re.match(r'\s+"([^"]+)".*:$|' + r'\s+\'([^\']+)\'.*:$', line)
            if menu_match:
                # group(1) для двойных кавычек, group(2) для одинарных
                text = menu_match.group(1) if menu_match.group(1) else menu_match.group(2)
                
                # Сохраняем полную оригинальную строку для упаковки
                original_line = line.strip()
                
                # Проверка: если в строке есть условие между кавычкой и двоеточием
                # Находим позицию закрывающей кавычки и двоеточия
                if text:
                    # Ищем что идёт после закрывающей кавычки до двоеточия
                    quote_char = '"' if menu_match.group(1) else "'"
                    after_quote_pos = line.find(quote_char + text + quote_char) + len(quote_char + text + quote_char)
                    between_quote_and_colon = line[after_quote_pos:]
                    has_condition = ('==' in between_quote_and_colon or 'True' in between_quote_and_colon or 'False' in between_quote_and_colon)
                else:
                    has_condition = False
                
                # Пропускаем пустые и очень короткие технические строки
                if not text.strip() or len(text.strip()) < 2:
                    continue
                
                # Пропускаем технические строки (hex цвета, числа)
                if re.match(r'^#[0-9a-fA-F]+$', text.strip()):
                    continue
                
                analysis = self._analyze_text(text)
                
                string_obj = {
                    "id": idx,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                    "speaker": "menu",
                    "speaker_prefix": "menu",
                    "original": text,
                    "translation": "",
                    "context": "menu",
                    "tags": analysis["tags"],
                    "variables_curly": analysis["variables_curly"],
                    "variables_square": analysis["variables_square"],
                    "special_chars": analysis["special_chars"]
                }
                
                # Если есть условие - сохраняем полную строку для упаковки
                if has_condition:
                    string_obj["original_full"] = original_line
                
                strings.append(string_obj)
                
                idx += 1
                continue

            # Паттерн для функций перевода _("текст")
            translate_func_match = re.search(r'_\("([^"]+)"\)', line)
            if translate_func_match:
                text = translate_func_match.group(1)
                
                # Пропускаем пустые и очень короткие строки
                if not text.strip() or len(text.strip()) < 2:
                    continue
                
                # Пропускаем hex цвета
                if re.match(r'^#[0-9a-fA-F]+$', text.strip()):
                    continue
                
                # Пропускаем дубликаты
                if text in seen_texts:
                    continue
                
                seen_texts.add(text)
                analysis = self._analyze_text(text)
                
                strings.append({
                    "id": idx,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                    "speaker": "system",
                    "speaker_prefix": "system",
                    "original": text,
                    "translation": "",
                    "context": "text",
                    "tags": analysis["tags"],
                    "variables_curly": analysis["variables_curly"],
                    "variables_square": analysis["variables_square"],
                    "special_chars": analysis["special_chars"]
                })
                
                idx += 1
                continue

            # Паттерн для text_color и других атрибутов (пропускаем)
            if re.match(r'\s+(text_color|text_hover_color|text_selected_color|text_font)\s+', line):
                continue

            # Паттерн для диалогов с явным указанием персонажа
            # Формат: персонаж [talk] "текст" или centered "текст" или extend "текст"
            dialog_match = re.match(r'\s+(\w+)\s+(?:talk\s+)?"([^"]*)"', line)
            if dialog_match:
                speaker = dialog_match.group(1)
                text = dialog_match.group(2)
                
                # Сохраняем полную оригинальную строку (включая условие) для корректной упаковки
                # Но для перевода используем только текст в кавычках
                original_line = line.strip()
                
                # Проверка: если в строке есть == или True/False после текста, это условие
                remaining_line = line[dialog_match.end():]
                has_condition = ('==' in remaining_line or 'True' in remaining_line or 'False' in remaining_line)
                
                # Если есть условие - сохраняем полную строку в metadata для упаковки
                # При упаковке будем искать по этой полной строке и заменять только текст в кавычках

                # Пропускаем пустые строки
                if not text.strip():
                    continue

                # Если это служебное слово RenPy, сохраняем текст но не персонажа
                if speaker in self.RENPY_KEYWORDS:
                    analysis = self._analyze_text(text)
                    
                    string_obj = {
                        "id": idx,
                        "line": line_num,
                        "file": os.path.basename(file_path),
                        "speaker": current_speaker if current_speaker else "narrator",
                        "speaker_prefix": self._get_speaker_prefix(current_speaker) if current_speaker else "narrator",
                        "original": text,
                        "translation": "",
                        "context": self._detect_context(text, current_speaker),
                        "tags": analysis["tags"],
                        "variables_curly": analysis["variables_curly"],
                        "variables_square": analysis["variables_square"],
                        "special_chars": analysis["special_chars"]
                    }
                    
                    # Если есть условие - сохраняем полную строку для упаковки
                    if has_condition:
                        string_obj["original_full"] = original_line
                    
                    strings.append(string_obj)
                    
                    idx += 1
                    continue

                character_entities.add(speaker)

                # Анализируем текст
                analysis = self._analyze_text(text)

                string_obj = {
                    "id": idx,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                    "speaker": speaker,
                    "speaker_prefix": self._get_speaker_prefix(speaker),
                    "original": text,
                    "translation": "",
                    "context": self._detect_context(text, speaker),
                    "tags": analysis["tags"],
                    "variables_curly": analysis["variables_curly"],
                    "variables_square": analysis["variables_square"],
                    "special_chars": analysis["special_chars"]
                }
                
                # Если есть условие - сохраняем полную строку для упаковки
                if has_condition:
                    string_obj["original_full"] = original_line
                
                strings.append(string_obj)

                idx += 1
                current_speaker = speaker
                continue

            # Паттерн для анонимных диалогов (повествование)
            # Формат: "текст" (НЕ заканчивается на :, иначе это menu item)
            anon_match = re.match(r'\s+"([^"]*)"', line)
            if anon_match:
                # Проверяем что это НЕ menu item (не заканчивается на :)
                if line.strip().endswith(':'):
                    # Это menu item, пропускаем - он уже обработан выше
                    continue
                
                text = anon_match.group(1)
                
                # Сохраняем полную оригинальную строку для упаковки
                original_line = line.strip()
                
                # Проверка: если после текста идёт условие
                remaining_line = line[anon_match.end():]
                has_condition = ('==' in remaining_line or 'True' in remaining_line or 'False' in remaining_line)

                # Пропускаем пустые строки и короткие технические строки
                if not text.strip() or len(text.strip()) < 3:
                    continue
                
                # Пропускаем hex цвета
                if re.match(r'^#[0-9a-fA-F]+$', text.strip()):
                    continue

                analysis = self._analyze_text(text)

                string_obj = {
                    "id": idx,
                    "line": line_num,
                    "file": os.path.basename(file_path),
                    "speaker": current_speaker if current_speaker else "narrator",
                    "speaker_prefix": self._get_speaker_prefix(current_speaker) if current_speaker else "narrator",
                    "original": text,
                    "translation": "",
                    "context": self._detect_context(text, current_speaker),
                    "tags": analysis["tags"],
                    "variables_curly": analysis["variables_curly"],
                    "variables_square": analysis["variables_square"],
                    "special_chars": analysis["special_chars"]
                }
                
                # Если есть условие - сохраняем полную строку для упаковки
                if has_condition:
                    string_obj["original_full"] = original_line
                
                strings.append(string_obj)

                idx += 1
                continue

        return strings, character_entities

    def _get_speaker_prefix(self, speaker: Optional[str]) -> str:
        """Определяет префикс персонажа (n = narrator)"""
        if not speaker:
            return "narrator"

        if speaker.startswith('n') and len(speaker) > 1:
            return 'n'  # nprincess, nmaid и т.д.

        return speaker

    def _analyze_text(self, text: str) -> Dict:
        """Анализирует текст и извлекает теги, переменные, спецсимволы"""

        # Переменные в фигурных скобках (включая {#variable})
        variables_curly = re.findall(r'\{#?(\w+)\}', text)

        # Переменные в квадратных скобках (включая сложные типа [namepov!tc])
        variables_square = re.findall(r'\[([^\]]+)\]', text)

        # Теги форматирования
        tags = re.findall(r'\{/?(?:color|b|i|u|size|center|w|nw|p|fast)[^}]*\}', text)

        # Спецсимволы (ищем буквальные escape-последовательности, как они записаны в .rpy)
        # В .rpy файлах escape-последовательности записаны как \\n (два символа)
        special_chars = {
            "newlines": text.count('\\n'),
            "tabs": text.count('\\t'),
            "escaped_quotes": text.count('\\"'),
            "has_formatting": bool(tags)
        }

        return {
            "variables_curly": variables_curly,
            "variables_square": variables_square,
            "tags": tags,
            "special_chars": special_chars
        }

    def _detect_context(self, text: str, speaker: Optional[str]) -> str:
        """Определяет контекст строки"""

        # Интерфейсные строки обычно короткие
        if len(text) < 20 and not any(c in text for c in '.!?'):
            return "ui"

        # Повествование (narrator prefix)
        if speaker and speaker.startswith('n') and len(speaker) > 1:
            return "narration"

        # Диалоги обычно содержат знаки препинания
        if any(c in text for c in '.!?'):
            return "dialogue"

        return "text"

    def save_character_map(self, character_entities: Set[str], output_file: str):
        """Сохраняет map персонажей в JSON файл для проставления пола"""

        # Создаем директорию, если не существует
        dir_name = os.path.dirname(output_file)
        os.makedirs(dir_name, exist_ok=True)
        
        # Путь к основному файлу (без даты)
        main_file = output_file
        
        # Загружаем существующую карту персонажей из основного файла
        existing_map = {}
        if os.path.exists(main_file):
            try:
                with open(main_file, 'r', encoding='utf-8') as f:
                    existing_map = json.load(f)
                print(f"✅ Загружена существующая карта: {main_file}")
            except Exception as e:
                print(f"⚠️  Ошибка загрузки существующей карты: {e}")

        # Группируем новые персонажи по базовому имени (без префикса n)
        new_character_map = {}
        all_character_map = {}

        for entity in sorted(character_entities):
            base_name = entity.lstrip('n') if entity.startswith('n') and len(entity) > 1 else entity

            # Добавляем в общую карту
            if base_name not in all_character_map:
                all_character_map[base_name] = {
                    "entities": [],
                    "gender": "",
                    "notes": ""
                }
            all_character_map[base_name]["entities"].append(entity)
            
            # Проверяем, есть ли персонаж в существующей карте
            if base_name not in existing_map:
                # Новый персонаж - добавляем в карту новых
                if base_name not in new_character_map:
                    new_character_map[base_name] = {
                        "entities": [],
                        "gender": "",
                        "notes": ""
                    }
                new_character_map[base_name]["entities"].append(entity)

        # Сохраняем только новых персонажей в файл с датой
        if new_character_map:
            base_name_file = os.path.basename(output_file)
            name, ext = os.path.splitext(base_name_file)
            
            # Формат даты: день.месяц.год-час:минута:секунда
            date_str = datetime.now().strftime("%d.%m.%Y-%H:%M:%S")
            new_file = os.path.join(dir_name, f"{name}_{date_str}{ext}")
            
            with open(new_file, 'w', encoding='utf-8') as f:
                json.dump(new_character_map, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Новые персонажи сохранены: {new_file}")
            print(f"   Новых персонажей: {len(new_character_map)}")
            print(f"   Новых сущностей: {sum(len(v['entities']) for v in new_character_map.values())}")
        else:
            print(f"✅ Новых персонажей не обнаружено")

        print(f"📊 Всего уникальных персонажей: {len(all_character_map)}")
        print(f"📊 Всего сущностей: {len(character_entities)}")

    def load_character_map(self, character_map_file: str) -> Dict[str, str]:
        """Загружает map персонажей и возвращает словарь entity -> gender"""

        if not os.path.exists(character_map_file):
            return {}

        with open(character_map_file, 'r', encoding='utf-8') as f:
            character_map = json.load(f)

        # Создаем плоский словарь entity -> gender
        entity_gender = {}
        for base_name, info in character_map.items():
            gender = info.get("gender", "")
            for entity in info["entities"]:
                entity_gender[entity] = gender

        return entity_gender

    def enrich_with_gender(self, strings: List[Dict], entity_gender: Dict[str, str]):
        """Добавляет информацию о поле персонажа в строки"""

        for string in strings:
            speaker = string.get("speaker", "")
            string["speaker_gender"] = entity_gender.get(speaker, "unknown")

    def prepare_module(self, module_file: str, output_file: str,
                      character_map_file: Optional[str] = None,
                      save_char_map: bool = True):
        """Подготавливает модуль для перевода"""

        print(f"📄 Обрабатываю исходный файл: {module_file}")

        strings, character_entities = self.parse_rpy_source(module_file)

        # Сохраняем карту персонажей, если требуется
        if save_char_map:
            if character_map_file:
                char_map_output = character_map_file
            else:
                # По умолчанию сохраняем в data/characters.json
                char_map_output = os.path.join(os.path.dirname(os.path.dirname(output_file)), 'data', 'characters.json')
            self.save_character_map(character_entities, char_map_output)

        # Загружаем информацию о поле персонажей, если файл существует
        entity_gender = {}
        if character_map_file and os.path.exists(character_map_file):
            entity_gender = self.load_character_map(character_map_file)
            self.enrich_with_gender(strings, entity_gender)
            print(f"✅ Загружена информация о поле персонажей")

        # Подсчет статистики
        total = len(strings)

        metadata = {
            "source_file": os.path.basename(module_file),
            "source_path": module_file,
            "total_strings": total,
            "character_count": len(character_entities),
            "characters": list(sorted(character_entities)),
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

        print(f"✅ Подготовлено: {total} строк")
        print(f"   Персонажей: {len(character_entities)}")
        print(f"💾 Сохранено в: {output_file}")

        return output

    def prepare_batch(self, source_dir: str, output_dir: str,
                     pattern: str = "*.rpy",
                     character_map_file: Optional[str] = None):
        """Подготавливает пакет исходных файлов"""

        import glob

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        source_files = glob.glob(os.path.join(source_dir, pattern))

        print(f"🔍 Найдено файлов: {len(source_files)}")

        # Собираем всех персонажей из всех файлов
        all_characters = set()

        for source_file in source_files:
            basename = os.path.basename(source_file).replace('.rpy', '_v2.json')
            output_file = os.path.join(output_dir, basename)

            try:
                result = self.prepare_module(
                    source_file,
                    output_file,
                    character_map_file=character_map_file,
                    save_char_map=False  # Не сохраняем для каждого файла
                )
                all_characters.update(result["metadata"]["characters"])
            except Exception as e:
                print(f"❌ Ошибка при обработке {source_file}: {e}")

        # Сохраняем общую карту персонажей
        if character_map_file:
            self.save_character_map(all_characters, character_map_file)

        print(f"\n🎉 Готово! Обработано файлов: {len(source_files)}")
        print(f"   Всего уникальных персонажей: {len(all_characters)}")


def main():
    parser = argparse.ArgumentParser(
        description="Подготовка переводов для LLM (v2 с поддержкой персонажей)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

  # Обработка одного файла
  python llm_translate_prepare_v2.py --source ../extracted_scripts/c1.rpy --output ../temp_files/c1_v2.json

  # Пакетная обработка с созданием карты персонажей
  python llm_translate_prepare_v2.py --batch ../extracted_scripts --batch-output ../temp_files/llm_json_v2 --character-map ../data/characters.json

  # Использование существующей карты персонажей
  python llm_translate_prepare_v2.py --source ../extracted_scripts/c1.rpy --output ../temp_files/c1_v2.json --character-map ../data/characters.json

Примечание: Файл персонажей сохраняется с датой, например: characters_11.10.2025-23:59:59.json
        """
    )

    parser.add_argument("--source", help="Путь к исходному .rpy файлу")
    parser.add_argument("--output", help="Путь к выходному JSON файлу")
    parser.add_argument("--batch", help="Обработать все файлы в директории")
    parser.add_argument("--batch-output", default="../temp_files/llm_json_v2",
                       help="Директория для выходных JSON (при --batch)")
    parser.add_argument("--pattern", default="*.rpy",
                       help="Паттерн для поиска файлов (при --batch)")
    parser.add_argument("--character-map",
                       help="Путь к файлу с картой персонажей (для загрузки или сохранения)")

    args = parser.parse_args()

    preparer = TranslationPreparerV2()

    if args.batch:
        preparer.prepare_batch(
            args.batch,
            args.batch_output,
            args.pattern,
            character_map_file=args.character_map
        )
    elif args.source and args.output:
        preparer.prepare_module(
            args.source,
            args.output,
            character_map_file=args.character_map
        )
    else:
        # Режим по умолчанию: подготовить все файлы из extracted_scripts
        source_dir = "../extracted_scripts"
        output_dir = "../temp_files/llm_json_v2"
        character_map = "../data/characters.json"

        print("🚀 Режим пакетной обработки")
        print(f"📁 Входная директория: {source_dir}")
        print(f"📁 Выходная директория: {output_dir}")
        print(f"📁 Карта персонажей: {character_map}")
        print()

        preparer.prepare_batch(source_dir, output_dir, character_map_file=character_map)


if __name__ == "__main__":
    main()
