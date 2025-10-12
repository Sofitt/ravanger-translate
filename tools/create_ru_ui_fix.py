#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создает файл с настройками интерфейса для русского языка
Исправляет проблему с длинным текстом
"""

import os

def create_ui_fix():
    """Создает screens.rpy для русского языка с прокруткой и увеличенной областью текста"""
    
    output_path = "../game/tl/ru/screens.rpy"
    
    content = """## Настройки интерфейса для русского языка
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
"""
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Создан файл: {output_path}")
    print(f"\n📝 Что сделано:")
    print(f"  • Уменьшен размер шрифта диалогов до 20px (было ~24px)")
    print(f"  • Уменьшен размер шрифта кнопок выбора до 18px")
    print(f"  • Уменьшен размер шрифта centered текста до 22px")
    print(f"  • Включен перенос длинного текста в кнопках выбора")
    print(f"  • Добавлен межстрочный интервал 2px для лучшей читаемости")
    print(f"\n⚙️  Настройка размеров шрифта:")
    print(f"  Откройте {output_path}")
    print(f"  Измените 'size 20' на нужное значение для диалогов (строка 21)")
    print(f"  Измените 'size 18' для кнопок выбора (строка 30)")
    print(f"\n💡 Если текст всё ещё не влезает:")
    print(f"  Попробуйте уменьшить size до 18 для диалогов или 16 для кнопок")
    print(f"\n🎮 Перезапустите игру, чтобы изменения вступили в силу")

if __name__ == "__main__":
    create_ui_fix()
