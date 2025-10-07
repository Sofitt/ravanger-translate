#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def pack_translations():
    """Упаковывает переводы обратно в RPA архив"""
    
    # Проверяем, что unrpa может создавать архивы
    try:
        # Используем rpatool для создания архива
        cmd = "renpy_tools/bin/python -c \""
        cmd += "import os, sys; sys.path.append('renpy_tools/lib/python3.*/site-packages'); "
        cmd += "from unrpa import UnRPA; "
        cmd += "print('unrpa доступен')\""
        
        result = os.system(cmd)
        if result != 0:
            print("Ошибка: unrpa недоступен")
            return False
            
    except Exception as e:
        print(f"Ошибка при проверке unrpa: {e}")
        return False
    
    # Создаем новый архив
    print("Создание нового архива переводов...")
    
    # Используем системную команду для создания архива
    # Это упрощенный подход - в реальности нужен полноценный RPA packer
    
    cmd = f"cd _translations && tar -czf ../game/Translations_NEW.rpa.gz ."
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Архив создан: game/Translations_NEW.rpa.gz")
        print("⚠️  Это временное решение. Для полной совместимости нужен RPA packer.")
        return True
    else:
        print("❌ Ошибка создания архива")
        return False

def simple_test():
    """Простой тест - копируем файлы напрямую в папку игры"""
    
    print("🧪 Простой тест: копирование файлов напрямую...")
    
    # Создаем тестовую папку в игре
    test_dir = "game/tl"
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(f"{test_dir}/ru", exist_ok=True)
    
    # Копируем ваш измененный файл
    src = "translation_modules/c0_reference_ru.rpy"
    dst = f"{test_dir}/ru/c0_reference.rpy"
    
    try:
        import shutil
        shutil.copy2(src, dst)
        print(f"✅ Скопирован: {src} → {dst}")
        
        # Проверяем содержимое
        with open(dst, 'r', encoding='utf-8') as f:
            content = f.read()
            if "АНИМЕ ГОВНО" in content:
                print("✅ Тестовый перевод найден в файле!")
                return True
            else:
                print("❌ Тестовый перевод не найден")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка копирования: {e}")
        return False

if __name__ == "__main__":
    print("🎯 Упаковка переводов в игру...")
    
    # Сначала пробуем простой тест
    if simple_test():
        print("\n🎮 Теперь запустите игру и проверьте перевод!")
        print("   1. Запустите Ravager")
        print("   2. Зайдите в настройки")
        print("   3. Выберите русский язык")
        print("   4. Найдите строку 'ANIMATED PORTRAITS' - она должна быть 'АНИМЕ ГОВНО'")
    else:
        print("\n❌ Тест не прошел")
    
    # Пробуем создать полноценный архив
    print("\n📦 Попытка создания RPA архива...")
    pack_translations()
