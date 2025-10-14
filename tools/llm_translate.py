#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Перевод текста через локальную LLM
Поддерживает различные backends: OpenAI-compatible API, llama.cpp, Ollama
"""

import os
import re
import json
import argparse
import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TranslationConfig:
    """Конфигурация для перевода"""
    backend: str = "openai"  # openai, ollama, llamacpp
    api_url: str = "http://localhost:8080/v1/chat/completions"
    api_key: str = "not-needed"
    model: str = "local-model"
    temperature: float = 0.1
    top_p: float = 0.7
    max_tokens: int = 2000
    batch_size: int = 10


class TranslationValidator:
    """Валидатор переводов"""

    @staticmethod
    def validate(original: str, translation: str) -> List[str]:
        """Проверяет корректность перевода"""
        errors = []

        if not translation or not translation.strip():
            return errors  # Пустые переводы не ошибка

        # 1. Переменные в фигурных скобках (включая {variable} и {#variable})
        orig_vars_curly = set(re.findall(r'\{#?(\w+)\}', original))
        trans_vars_curly = set(re.findall(r'\{#?(\w+)\}', translation))
        if orig_vars_curly != trans_vars_curly:
            errors.append(f"Переменные {{}}: {orig_vars_curly} != {trans_vars_curly}")

        # 2. Переменные с решеткой {#variable} - должны сохраняться полностью
        orig_hash_vars = re.findall(r'\{#\w+\}', original)
        trans_hash_vars = re.findall(r'\{#\w+\}', translation)
        if orig_hash_vars != trans_hash_vars:
            errors.append(f"Переменные {{#}}: {orig_hash_vars} != {trans_hash_vars}")

        # 3. Переменные в квадратных скобках (включая модификаторы !tc, !t, !u и т.д.)
        orig_vars_square = re.findall(r'\[[^\]]+\]', original)
        trans_vars_square = re.findall(r'\[[^\]]+\]', translation)
        if orig_vars_square != trans_vars_square:
            errors.append(f"Переменные []: {orig_vars_square} != {trans_vars_square}")

        # 4. Теги форматирования
        orig_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', original)
        trans_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', translation)
        if orig_tags != trans_tags:
            errors.append(f"Теги: {orig_tags} != {trans_tags}")

        # 5. Переносы строк (escape-последовательности \\n)
        if original.count('\\n') != translation.count('\\n'):
            errors.append(f"\\n: {original.count('\\n')} != {translation.count('\\n')}")

        # 6. Реальные переводы строк (символ \n) - не должны добавляться
        orig_real_newlines = original.count('\n')
        trans_real_newlines = translation.count('\n')
        if orig_real_newlines != trans_real_newlines:
            errors.append(f"Реальные переводы строк: {orig_real_newlines} != {trans_real_newlines}")

        # 7. Проверка пробелов перед переменными {#variable}
        # Ищем паттерны word{#variable} и проверяем наличие пробела
        orig_no_space = re.findall(r'\w\{#\w+\}', original)
        trans_with_space = re.findall(r'\w\s+\{#\w+\}', translation)
        if orig_no_space and trans_with_space:
            errors.append(f"Лишний пробел перед переменной: найдено {len(trans_with_space)} случаев")

        # 8. Неэкранированные кавычки
        if '"' in translation and '\\"' not in translation:
            # Проверяем, что это не внешние кавычки
            inner_text = translation.strip('"')
            if '"' in inner_text:
                errors.append('Кавычки должны быть экранированы: \\"')

        return errors


class LLMTranslator:
    """Переводчик через LLM"""

    def __init__(self, config: TranslationConfig):
        self.config = config
        self.validator = TranslationValidator()
        # system_prompt закомментирован - правила зашиты в модель
        # self.system_prompt = self._create_system_prompt()

    def _call_openai_api(self, messages: List[Dict]) -> Optional[str]:
        """Вызов API (OpenAI или Ollama)"""
        try:
            import requests

            if self.config.backend == "ollama":
                # Формат запроса для Ollama
                data = {
                    "model": self.config.model,
                    "messages": messages,
                    "options": {
                        "temperature": self.config.temperature,
                        "top_p": self.config.top_p,
                        "num_predict": self.config.max_tokens
                    },
                    "stream": False
                }

                # Ollama не требует API ключа
                headers = {"Content-Type": "application/json"}

                response = requests.post(
                    self.config.api_url,
                    headers=headers,
                    json=data,
                    timeout=300  # Увеличиваем таймаут для Ollama
                )

                response.raise_for_status()
                result = response.json()

                # Формат ответа Ollama
                return result["message"]["content"].strip()

            else:
                # Стандартный формат OpenAI
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config.api_key}"
                }

                data = {
                    "model": self.config.model,
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens
                }

                response = requests.post(
                    self.config.api_url,
                    headers=headers,
                    json=data,
                    timeout=120
                )

                response.raise_for_status()
                result = response.json()

                return result["choices"][0]["message"]["content"].strip()

        except Exception as e:
            print(f"❌ Ошибка API ({self.config.backend}): {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Ответ сервера: {e.response.text}")
            return None

    def should_skip_translation(self, text: str) -> bool:
        """Проверяет, нужно ли пропустить перевод этой строки"""
        # Служебные слова Ren'Py
        renpy_keywords = {
            "centered", "left", "right", "top", "bottom",
            "True", "False", "None"
        }

        # Пропускаем служебные слова
        if text.strip() in renpy_keywords:
            return True

        # Пропускаем очень короткие строки (1-2 символа)
        if len(text.strip()) <= 2:
            return True

        return False

    def translate_single(self, text: str, context: str = "", speaker_gender: str = "") -> Optional[str]:
        """Переводит одну строку"""

        # Проверяем, нужно ли пропустить перевод
        if self.should_skip_translation(text):
            return text  # Возвращаем оригинал без изменений

        # Формируем промпт в формате Instruct
        # Правила перевода зашиты в модель, поэтому используем простой формат
        gender_prefix = f"{speaker_gender}: " if speaker_gender else ""
        user_prompt = f'[INST]Переведи {gender_prefix} {text} [/INST]'

        # Для Ollama отправляем как обычное сообщение
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        # Вызываем API
        raw_translation = self._call_openai_api(messages)

        if raw_translation:
            # Сохраняем сырой ответ
            translation = raw_translation
            # Убираем markdown разделители
            translation = translation.replace('---\n\n', '').replace('---\n', '').replace('---', '')
            translation = translation.strip()

            # Убираем лишние префиксы, которые иногда добавляет LLM
            prefixes_to_remove = [
                "Перевод: ", "Translation: ", "Переведённый текст: ",
                "Переведенный текст: ", "Результат: ", "Ответ: ", "Ответ:\n"
            ]
            for prefix in prefixes_to_remove:
                if translation.startswith(prefix):
                    translation = translation[len(prefix):].strip()
                    break

            # Убираем внешние кавычки только если они добавлены LLM (оригинал без кавычек)
            # Проверяем: если оригинал не начинался с кавычки, но перевод обёрнут в них - убираем
            if not text.startswith(("'", '"')):
                # Убираем одну пару внешних двойных кавычек
                if translation.startswith('"') and translation.endswith('"') and len(translation) > 1:
                    translation = translation[1:-1]
                # Убираем одну пару внешних одинарных кавычек
                elif translation.startswith("'") and translation.endswith("'") and len(translation) > 1:
                    translation = translation[1:-1]

            # Финальная очистка пробелов
            translation = translation.strip()
            
            # Восстанавливаем escape-последовательности, если они были в оригинале
            # LLM может преобразовать \\n в реальный перевод строки, нужно вернуть обратно
            if '\\n' in text and '\n' in translation and '\\n' not in translation:
                translation = translation.replace('\n', '\\n')
            if '\\t' in text and '\t' in translation and '\\t' not in translation:
                translation = translation.replace('\t', '\\t')

            # Валидация (без самопроверки - правила в модели)
            errors = self.validator.validate(text, translation)

            if errors:
                print(f"  ⚠️  Предупреждения для '{text[:50]}...':")
                for error in errors:
                    print(f"      - {error}")
                
                # Проверяем критичные ошибки, которые должны отклонить перевод
                critical_errors = [
                    "Реальные переводы строк",
                    "Переменные {#}",
                    "Лишний пробел перед переменной"
                ]
                for error in errors:
                    for critical in critical_errors:
                        if critical in error:
                            print(f"  ❌ Критичная ошибка - перевод отклонён")
                            return (None, raw_translation)

            # Возвращаем кортеж (обработанный перевод, сырой ответ)
            return (translation, raw_translation)

        return (None, None)

    def _save_progress(self, output_file: str, strings: List[Dict], metadata: Optional[Dict], translated: int, failed: int):
        """Сохраняет текущий прогресс перевода"""
        if metadata:
            metadata["translated"] = translated
            metadata["failed"] = failed
            metadata["untranslated"] = len(strings) - translated - failed

        output = {
            "metadata": metadata or {},
            "strings": strings
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def _save_errors(self, output_file: str, error_strings: List[Dict], metadata: Optional[Dict]):
        """Сохраняет строки с ошибками валидации для повторного перевода"""
        if not error_strings:
            return

        # Формируем имя файла для ошибок
        base_name = output_file.rsplit('.', 1)[0]
        error_file = f"{base_name}_errors.json"

        # Загружаем существующие ошибки, если файл есть
        existing_errors = []
        existing_originals = set()
        
        if os.path.exists(error_file):
            try:
                with open(error_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_errors = existing_data.get('strings', [])
                    existing_originals = {item.get('original', '') for item in existing_errors}
                print(f"  📝 Загружено существующих ошибок: {len(existing_errors)}")
            except Exception as e:
                print(f"  ⚠️  Ошибка загрузки существующего файла ошибок: {e}")

        # Добавляем только новые ошибки (без дубликатов)
        new_errors_count = 0
        for error in error_strings:
            original = error.get('original', '')
            if original not in existing_originals:
                existing_errors.append(error)
                existing_originals.add(original)
                new_errors_count += 1

        error_metadata = metadata.copy() if metadata else {}
        error_metadata["error_count"] = len(existing_errors)
        error_metadata["description"] = "Строки с ошибками валидации для повторного перевода"

        output = {
            "metadata": error_metadata,
            "strings": existing_errors
        }

        with open(error_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        if new_errors_count > 0:
            print(f"\n⚠️  Добавлено новых ошибок: {new_errors_count} (всего: {len(existing_errors)}) в {error_file}")
        else:
            print(f"\n✓ Новых ошибок не обнаружено (всего: {len(existing_errors)})")

    def translate_batch(self, strings: List[Dict], output_file: Optional[str] = None, metadata: Optional[Dict] = None, save_errors: bool = True) -> List[Dict]:
        """Переводит пакет строк с сохранением после каждой строки
        
        Args:
            save_errors: Если False, не создает файл _errors.json
        """

        total = len(strings)
        translated = 0
        failed = 0
        error_strings = []  # Строки с ошибками валидации

        print(f"🔄 Начинаю перевод {total} строк...")

        for idx, string_obj in enumerate(strings):
            # Пропускаем уже переведенные
            if string_obj.get("translation", "").strip():
                print(f"  [{idx+1}/{total}] ⏭️  Пропущено (уже переведено): {string_obj['original'][:50]}...")
                continue

            original = string_obj["original"]
            context = string_obj.get("context", "")
            speaker_gender = string_obj.get("speaker_gender", "")

            print(f"  [{idx+1}/{total}] 🔄 Перевожу: {original[:50]}...")

            result = self.translate_single(original, context, speaker_gender)

            if result and result[0]:
                translation, raw_translation = result
                
                # Проверяем валидацию ПЕРЕД сохранением в string_obj
                errors = self.validator.validate(original, translation)
                if errors:
                    # Валидация не прошла - сохраняем ТОЛЬКО в error_strings
                    error_obj = string_obj.copy()
                    error_obj["translation"] = translation
                    error_obj["translated_raw"] = raw_translation
                    error_obj["validation_errors"] = errors
                    error_strings.append(error_obj)
                    
                    failed += 1
                    print(f"  [{idx+1}/{total}] ⚠️  Ошибка валидации:")
                    for error in errors:
                        print(f"      - {error}")
                else:
                    # Валидация прошла - сохраняем в string_obj (попадёт в _translated)
                    # Вставляем поля в нужном порядке: translation, translated_raw
                    # Создаем временный словарь с нужным порядком
                    temp_obj = {}
                    for key in string_obj:
                        temp_obj[key] = string_obj[key]
                        if key == "translation" or (key == "original" and "translation" not in string_obj):
                            temp_obj["translation"] = translation
                            temp_obj["translated_raw"] = raw_translation
                    
                    # Если translation не было добавлено, добавляем в конец
                    if "translation" not in temp_obj:
                        temp_obj["translation"] = translation
                        temp_obj["translated_raw"] = raw_translation
                    
                    string_obj.clear()
                    string_obj.update(temp_obj)
                    
                    translated += 1
                    print(f"  [{idx+1}/{total}] ✅ {translation[:50]}...")
            else:
                # Перевод не удался или был отклонён из-за критичных ошибок
                failed += 1
                print(f"  [{idx+1}/{total}] ❌ Не удалось перевести")
                
                # Добавляем в список ошибок для повторного перевода
                error_obj = string_obj.copy()
                error_obj["validation_errors"] = ["Перевод отклонён или не получен"]
                error_strings.append(error_obj)

            # Сохраняем прогресс после каждой строки
            if output_file:
                self._save_progress(output_file, strings, metadata, translated, failed)

            # Задержка между запросами
            time.sleep(0.5)

        print(f"\n📊 Статистика:")
        print(f"  ✅ Переведено: {translated}")
        print(f"  ❌ Ошибки: {failed}")
        print(f"  ⏭️  Пропущено: {total - translated - failed}")
        print(f"  ⚠️  С предупреждениями: {len(error_strings)}")

        # Сохраняем строки с ошибками в отдельный файл (если разрешено)
        if save_errors and output_file and error_strings:
            self._save_errors(output_file, error_strings, metadata)

        return strings

    def translate_file(self, input_file: str, output_file: str, save_errors: bool = True):
        """Переводит файл JSON
        
        Args:
            save_errors: Если False, не создает файл _errors.json
        """

        print(f"📄 Загружаю: {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        strings = data.get("strings", [])

        print(f"📊 Модуль: {metadata.get('module', 'unknown')}")
        print(f"📊 Всего строк: {len(strings)}")
        print(f"📊 Переведено: {metadata.get('translated', 0)}")
        print()

        # Переводим с автосохранением прогресса
        translated_strings = self.translate_batch(strings, output_file, metadata, save_errors)

        print(f"\n💾 Перевод завершен и сохранен в: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Перевод через LLM")
    parser.add_argument("--input", required=True, help="Входной JSON файл")
    parser.add_argument("--output", required=True, help="Выходной JSON файл")
    parser.add_argument("--backend", default="openai", choices=["openai", "ollama"],
                       help="Backend для LLM")
    parser.add_argument("--api-url", default="http://localhost:8080/v1/chat/completions",
                       help="URL API")
    parser.add_argument("--api-key", default="not-needed",
                       help="API ключ (если нужен)")
    parser.add_argument("--model", default="local-model",
                       help="Название модели")
    parser.add_argument("--temperature", type=float, default=0.1,
                       help="Temperature для генерации")
    parser.add_argument("--top-p", type=float, default=0.7,
                       help="Top-p sampling")
    parser.add_argument("--max-tokens", type=int, default=2000,
                       help="Максимум токенов в ответе")
    parser.add_argument("--batch-size", type=int, default=10,
                       help="Размер пакета для обработки (не используется, для совместимости)")
    parser.add_argument("--max-retries", type=int, default=3,
                       help="Максимум попыток повтора (не используется, для совместимости)")
    parser.add_argument("--no-error-file", action="store_true",
                       help="Не создавать файл _errors.json")

    args = parser.parse_args()

    # Создаем конфигурацию
    config = TranslationConfig(
        backend=args.backend,
        api_url=args.api_url,
        api_key=args.api_key,
        model=args.model,
        temperature=args.temperature,
        top_p=args.top_p,
        max_tokens=args.max_tokens
    )

    # Создаем переводчик
    translator = LLMTranslator(config)

    # Переводим файл
    translator.translate_file(args.input, args.output, save_errors=not args.no_error_file)

    print("\n🎉 Готово!")


if __name__ == "__main__":
    main()
