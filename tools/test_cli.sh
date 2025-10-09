#!/bin/bash
MODULES_DIR="../translation_modules"
JSON_DIR="../temp_files/llm_json"

# Массив
SELECTED_FILES=()

files=()
for file in "$MODULES_DIR"/*_ru.rpy; do
    if [ -f "$file" ]; then
        files+=("$file")
    fi
done

# Выбираем файл 17 (c4_peaks_ru.rpy)
SELECTED_FILES+=("${files[16]}")

echo "SELECTED_FILES: ${#SELECTED_FILES[@]}"
echo "File: ${SELECTED_FILES[0]}"

# Проверяем условие
if [ ${#SELECTED_FILES[@]} -gt 0 ]; then
    echo "Условие выполнено"
    for file in "${SELECTED_FILES[@]}"; do
        basename=$(basename "$file" .rpy)
        echo "Basename: $basename"
    done
fi
