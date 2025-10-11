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

        # 1. Переменные в фигурных скобках
        orig_vars_curly = set(re.findall(r'\{(\w+)\}', original))
        trans_vars_curly = set(re.findall(r'\{(\w+)\}', translation))
        if orig_vars_curly != trans_vars_curly:
            errors.append(f"Переменные {{}}: {orig_vars_curly} != {trans_vars_curly}")

        # 2. Переменные в квадратных скобках
        orig_vars_square = set(re.findall(r'\[(\w+)\]', original))
        trans_vars_square = set(re.findall(r'\[(\w+)\]', translation))
        if orig_vars_square != trans_vars_square:
            errors.append(f"Переменные []: {orig_vars_square} != {trans_vars_square}")

        # 3. Теги форматирования
        orig_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', original)
        trans_tags = re.findall(r'\{/?(?:color|b|i|u|size|center)[^}]*\}', translation)
        if orig_tags != trans_tags:
            errors.append(f"Теги: {orig_tags} != {trans_tags}")

        # 4. Переносы строк
        if original.count('\\n') != translation.count('\\n'):
            errors.append(f"\\n: {original.count('\\n')} != {translation.count('\\n')}")

        # 5. Неэкранированные кавычки
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
        user_prompt = f'[INST]Переведи {gender_prefix}"{text}"[/INST]'

        # Для Ollama отправляем как обычное сообщение
        messages = [
            {"role": "user", "content": user_prompt}
        ]

        # Вызываем API
        translation = self._call_openai_api(messages)

        if translation:
            # Убираем внешние кавычки если LLM добавила их
            translation = translation.strip('"\'')

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
                    translation = translation[len(prefix):].strip('"\'')
                    break

            # Финальная очистка
            translation = translation.strip()

            # Валидация (без самопроверки - правила в модели)
            errors = self.validator.validate(text, translation)

            if errors:
                print(f"  ⚠️  Предупреждения для '{text[:50]}...':")
                for error in errors:
                    print(f"      - {error}")

            return translation

        return None

    def translate_batch(self, strings: List[Dict]) -> List[Dict]:
        """Переводит пакет строк"""

        total = len(strings)
        translated = 0
        failed = 0

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

            translation = self.translate_single(original, context, speaker_gender)

            if translation:
                string_obj["translation"] = translation
                translated += 1
                print(f"  [{idx+1}/{total}] ✅ {translation[:50]}...")
            else:
                failed += 1
                print(f"  [{idx+1}/{total}] ❌ Не удалось перевести")

            # Задержка между запросами
            time.sleep(0.5)

        print(f"\n📊 Статистика:")
        print(f"  ✅ Переведено: {translated}")
        print(f"  ❌ Ошибки: {failed}")
        print(f"  ⏭️  Пропущено: {total - translated - failed}")

        return strings

    def translate_file(self, input_file: str, output_file: str):
        """Переводит файл JSON"""

        print(f"📄 Загружаю: {input_file}")

        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        strings = data.get("strings", [])

        print(f"📊 Модуль: {metadata.get('module', 'unknown')}")
        print(f"📊 Всего строк: {len(strings)}")
        print(f"📊 Переведено: {metadata.get('translated', 0)}")
        print()

        # Переводим
        translated_strings = self.translate_batch(strings)

        # Обновляем метаданные
        translated_count = sum(1 for s in translated_strings if s.get("translation", "").strip())
        metadata["translated"] = translated_count
        metadata["untranslated"] = len(strings) - translated_count

        # Сохраняем результат
        output = {
            "metadata": metadata,
            "strings": translated_strings
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Сохранено в: {output_file}")


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
    translator.translate_file(args.input, args.output)

    print("\n🎉 Готово!")


if __name__ == "__main__":
    main()
