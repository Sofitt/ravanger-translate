#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import shutil

def extract_game_scripts():
    """Извлекает .rpy скрипты из архивов игры"""
    
    print("🔍 Извлечение скриптов игры из архивов...")
    
    # Проверяем наличие архивов
    archives = [
        "../_game/Scripts.rpa",
        "../game/Scripts.rpa",
        "../_game/Translations.rpa",
        "../game/Translations.rpa"
    ]
    
    found_archives = []
    for archive in archives:
        if os.path.exists(archive):
            found_archives.append(archive)
            print(f"  ✅ Найден: {archive}")
    
    if not found_archives:
        print("❌ Ошибка: архивы не найдены!")
        print("   Убедитесь, что игра установлена в правильной папке")
        return False
    
    # Создаем папку для извлечения
    output_dir = "../extracted_scripts"
    
    if os.path.exists(output_dir):
        print(f"  ⚠️  Папка {output_dir} уже существует")
        response = input("  Удалить и создать заново? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(output_dir)
            print("  🗑️  Старая папка удалена")
        else:
            print("  ⏭️  Пропускаем извлечение")
            return True
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Извлекаем архивы
    for archive in found_archives:
        print(f"\n📦 Извлечение из {os.path.basename(archive)}...")
        
        try:
            # Используем unrpa для извлечения
            cmd = ["python3", "-m", "unrpa", "-mp", output_dir, archive]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"  ✅ Успешно извлечено")
            else:
                print(f"  ⚠️  Ошибка: {result.stderr}")
                # Пробуем альтернативный способ с установленным unrpa
                print(f"  🔄 Пробуем альтернативный метод...")
                
                cmd2 = ["unrpa", "-mp", output_dir, archive]
                result2 = subprocess.run(cmd2, capture_output=True, text=True)
                
                if result2.returncode == 0:
                    print(f"  ✅ Успешно извлечено (альтернативный метод)")
                else:
                    print(f"  ❌ Не удалось извлечь: {result2.stderr}")
        
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
    
    # Проверяем результат
    if os.path.exists(output_dir):
        rpy_files = [f for f in os.listdir(output_dir) if f.endswith('.rpy')]
        print(f"\n✅ Извлечено .rpy файлов: {len(rpy_files)}")
        
        if len(rpy_files) > 0:
            print(f"📁 Файлы находятся в: {output_dir}")
            return True
        else:
            print("⚠️  Файлы не найдены. Возможно, нужно установить unrpa:")
            print("   pip install unrpa")
            return False
    
    return False

def check_unrpa():
    """Проверяет наличие unrpa"""
    print("🔍 Проверка наличия unrpa...")
    
    try:
        result = subprocess.run(["python3", "-m", "unrpa", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ unrpa установлен")
            return True
    except:
        pass
    
    try:
        result = subprocess.run(["unrpa", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("  ✅ unrpa установлен")
            return True
    except:
        pass
    
    print("  ❌ unrpa не найден")
    print("  📦 Установите его: pip install unrpa")
    return False

if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════╗")
    print("║       ИЗВЛЕЧЕНИЕ СКРИПТОВ ИГРЫ ИЗ АРХИВОВ               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")
    
    # Проверяем unrpa
    if not check_unrpa():
        print("\n❌ Установите unrpa для продолжения")
        exit(1)
    
    # Извлекаем скрипты
    if extract_game_scripts():
        print("\n🎉 Готово! Теперь можно извлекать строки для перевода:")
        print("   python3 extract_dialogue_only.py")
    else:
        print("\n❌ Не удалось извлечь скрипты")
        exit(1)
