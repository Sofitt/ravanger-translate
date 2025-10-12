#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Преобразование JSON-файла model.json в текст для Modelfile
"""

import json
import sys


def json_to_modelfile_text(json_file_path):
    """
    Преобразует JSON-файл в текст формата для Modelfile

    Args:
        json_file_path: путь к JSON-файлу

    Returns:
        str с форматированным текстом
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Начало
    result = 'FROM ./saiga_nemo_12b.Q8_0.gguf\n\n'
    result += 'PARAMETER num_gpu 99\n'
    result += 'PARAMETER stop "</s>"\n'
    result += 'PARAMETER temperature 0.1\n'
    result += 'PARAMETER top_p 0.7\n\n'

    result += 'SYSTEM """\n'

    # Добавляем текст из массива "text" (объединяем через пробел)
    if 'text' in data and data['text']:
        # Экранируем и заменяем кавычки в каждом элементе отдельно
        processed_text = []
        for line in data['text']:
            line = line.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('"', "'")
            processed_text.append(line)
        result += ' '.join(processed_text)

    # Добавляем специальные правила из массива "special"
    if 'special' in data and data['special']:
        result += '\n\n'
        # Экранируем и заменяем кавычки в каждом элементе отдельно
        processed_special = []
        for line in data['special']:
            # Экранируем \n и \t внутри строки, заменяем кавычки
            line = line.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t').replace('"', "'")
            processed_special.append(line)
        result += '\n'.join(processed_special)

    # Добавляем инструкции в формате [INST]...[/INST]...</s>
    if 'instruction' in data and data['instruction']:
        result += '\n\n'
        for item in data['instruction']:
            before = item.get('before', '')
            after = item.get('after', '')
            # Экранируем обратно escape-последовательности
            before = before.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')
            after = after.replace('\\', '\\\\').replace('\n', '\\n').replace('\t', '\\t')
            result += f'[INST]{before}[/INST]{after}</s>'

    result += '\n"""\n\n'

    result += 'TEMPLATE """\n'
    result += '{{- if .System }}\n'
    result += '<s>{{ .System }} {{ .Prompt }}\n'
    result += '{{- else }}\n'
    result += '<s>[INST]{{ .Prompt }}[/INST]\n'
    result += '{{- end }}\n'
    result += '"""\n'

    return result


if __name__ == "__main__":
    import os

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = '/media/sofit/nvme0n1p2/SteamLibrary/steamapps/common/Ravager/Ravager/model/scripts/model.json'

    result_text = json_to_modelfile_text(input_file)

    # Путь к выходному файлу
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, '../Modelfile')

    # Записываем в файл
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result_text)

    print(f"Результат записан в: {output_file}")
