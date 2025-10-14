#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from typing import Dict, List, Tuple

class TranslationHelper:
    def __init__(self, modules_dir="../translation_modules"):
        self.modules_dir = modules_dir
        self.progress_file = "translation_progress.json"
        self.load_progress()
    
    def load_progress(self):
        """Загружает прогресс перевода"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                self.progress = json.load(f)
        else:
            self.progress = {}
    
    def save_progress(self):
        """Сохраняет прогресс перевода"""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def get_module_stats(self) -> Dict[str, Dict]:
        """Получает статистику по модулям"""
        stats = {}
        
        for filename in os.listdir(self.modules_dir):
            if filename.endswith('_ru.rpy'):
                filepath = os.path.join(self.modules_dir, filename)
                
                total_strings = 0
                translated_strings = 0
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Подсчитываем строки
                old_matches = re.findall(r'old "([^"]*)"', content)
                new_matches = re.findall(r'new "([^"]*)"', content)
                
                total_strings = len(old_matches)
                translated_strings = sum(1 for new in new_matches if new.strip())
                
                completion = (translated_strings / total_strings * 100) if total_strings > 0 else 0
                
                stats[filename] = {
                    'total': total_strings,
                    'translated': translated_strings,
                    'completion': completion,
                    'size_mb': os.path.getsize(filepath) / 1024 / 1024
                }
        
        return stats
    
    def create_work_plan(self):
        """Создает план работы по переводу"""
        stats = self.get_module_stats()
        
        # Группируем по приоритетам
        high_priority = []  # Основной сюжет
        medium_priority = []  # Интерфейс
        low_priority = []  # Остальное
        
        for filename, data in stats.items():
            if any(chapter in filename for chapter in ['c1_', 'c2_', 'c3_', 'c4_', 'c5_', 'c6_']):
                high_priority.append((filename, data))
            elif any(ui in filename for ui in ['screens_', 'options_', 'gallery_']):
                medium_priority.append((filename, data))
            else:
                low_priority.append((filename, data))
        
        # Сортируем по размеру (меньшие файлы сначала для быстрого прогресса)
        high_priority.sort(key=lambda x: x[1]['total'])
        medium_priority.sort(key=lambda x: x[1]['total'])
        low_priority.sort(key=lambda x: x[1]['total'])
        
        plan_file = "translation_work_plan.md"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write("# План работы по переводу Ravager\n\n")
            
            f.write("## 🎯 Этап 1: Основной сюжет (высокий приоритет)\n\n")
            total_high = 0
            for filename, data in high_priority:
                f.write(f"- [ ] **{filename}** - {data['total']} строк ({data['completion']:.1f}% готово)\n")
                total_high += data['total']
            
            f.write(f"\n**Итого этап 1:** {total_high} строк\n\n")
            
            f.write("## 🎮 Этап 2: Интерфейс (средний приоритет)\n\n")
            total_medium = 0
            for filename, data in medium_priority:
                f.write(f"- [ ] **{filename}** - {data['total']} строк ({data['completion']:.1f}% готово)\n")
                total_medium += data['total']
            
            f.write(f"\n**Итого этап 2:** {total_medium} строк\n\n")
            
            f.write("## 📚 Этап 3: Дополнительный контент (низкий приоритет)\n\n")
            total_low = 0
            for filename, data in low_priority:
                f.write(f"- [ ] **{filename}** - {data['total']} строк ({data['completion']:.1f}% готово)\n")
                total_low += data['total']
            
            f.write(f"\n**Итого этап 3:** {total_low} строк\n\n")
            
            f.write("## 📊 Общая статистика\n\n")
            f.write(f"- **Всего модулей:** {len(stats)}\n")
            f.write(f"- **Всего строк:** {total_high + total_medium + total_low}\n")
            f.write(f"- **Рекомендуемый порядок:** сначала маленькие файлы для быстрого прогресса\n\n")
            
            f.write("## 💡 Рекомендации\n\n")
            f.write("1. **Начните с файлов c1_ru.rpy, c2_*.rpy** - это начало игры\n")
            f.write("2. **Переводите по 50-100 строк за раз** для поддержания качества\n")
            f.write("3. **Тестируйте перевод в игре** после каждого модуля\n")
            f.write("4. **Ведите глоссарий** для консистентности терминов\n")
        
        print(f"План работы создан: {plan_file}")
        return plan_file
    

def main():
    helper = TranslationHelper()
    
    print("🎯 Анализ модулей перевода...")
    stats = helper.get_module_stats()
    
    print(f"\n📊 Найдено модулей: {len(stats)}")
    total_strings = sum(s['total'] for s in stats.values())
    total_translated = sum(s['translated'] for s in stats.values())
    overall_progress = (total_translated / total_strings * 100) if total_strings > 0 else 0
    
    print(f"📈 Общий прогресс: {total_translated}/{total_strings} ({overall_progress:.1f}%)")
    
    print("\n📋 Создание плана работы...")
    plan_file = helper.create_work_plan()
    
    print("\n🎯 Топ-5 модулей для начала работы:")
    sorted_modules = sorted(stats.items(), key=lambda x: x[1]['total'])
    for filename, data in sorted_modules[:5]:
        print(f"  {filename}: {data['total']} строк")
    
    print(f"\n✅ Готово! Проверьте файл {plan_file} для детального плана.")

if __name__ == "__main__":
    main()
