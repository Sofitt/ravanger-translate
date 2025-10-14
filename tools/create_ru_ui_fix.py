#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создает файл с настройками интерфейса для русского языка
Исправляет проблему с длинным текстом
"""

import os
import re

def create_ui_fix():
    """Создает или дополняет screens.rpy для русского языка с настройками шрифтов"""

    output_path = "../game/tl/ru/screens.rpy"

    # Маркер начала блока настроек интерфейса
    ui_marker = "## Настройки интерфейса для русского языка"
    ui_end_marker = "## КОНЕЦ НАСТРОЕК ИНТЕРФЕЙСА"

    ui_settings = f"""{ui_marker}
## Уменьшает размер шрифта для длинного текста

# Уменьшаем размер шрифта в диалогах
translate ru style say_dialogue:
    size 20
    line_spacing 2

# Настройки для choice меню - включаем перенос и уменьшаем шрифт
translate ru style choice_button:
    yminimum 40
    xfill True

translate ru style choice_button_text:
    size 18
    layout "subtitle"
    text_align 0.5
    xalign 0.5

# Уменьшаем шрифт для "centered" текста (начальный экран)
translate ru style centered_text:
    size 22

# Настройки для NVL режима
translate ru style nvl_dialogue:
    size 20
    line_spacing 2

# Межстрочный интервал для всего текста
translate ru style default:
    line_spacing 2

{ui_end_marker}
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Проверяем, существует ли файл
    if os.path.exists(output_path):
        # Читаем существующий файл
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Проверяем наличие блока настроек интерфейса
        if ui_marker in existing_content:
            # Блок уже есть - обновляем его
            # Удаляем старый блок (от маркера до конца маркера или до следующего translate)
            pattern = re.compile(
                rf'{re.escape(ui_marker)}.*?(?={ui_end_marker}.*?\n|\n\ntranslate|\Z)',
                re.DOTALL
            )

            # Если есть конечный маркер, удаляем вместе с ним
            if ui_end_marker in existing_content:
                pattern = re.compile(
                    rf'{re.escape(ui_marker)}.*?{re.escape(ui_end_marker)}\n',
                    re.DOTALL
                )

            updated_content = pattern.sub('', existing_content)
            # Добавляем новый блок в конец
            final_content = updated_content.rstrip() + "\n\n" + ui_settings

            print(f"🔄 Обновлён блок настроек интерфейса в: {output_path}")
        else:
            # Блока нет - добавляем в конец
            final_content = existing_content.rstrip() + "\n\n" + ui_settings
            print(f"➕ Добавлен блок настроек интерфейса в: {output_path}")

        # Записываем обновленный файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
    else:
        # Файла нет - создаем новый
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ui_settings)
        print(f"✅ Создан новый файл: {output_path}")
    print(f"\n⚙️  Настройка размеров шрифта:")
    print(f"  Откройте {output_path}")
    print(f"")

if __name__ == "__main__":
    create_ui_fix()
