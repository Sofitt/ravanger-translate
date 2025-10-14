#!/bin/bash

# Скрипт для массового перевода модулей через LLM (режим CLI по умолчанию)
# Использование: ./llm_batch_translate.sh [--prepare-only] [--translate-only] [--pack-only] [--skip-backup]

set -e  # Останов при ошибке

# Настройки API (можно переопределить через аргументы)
API_URL="${LLM_API_URL:-http://127.0.0.1:11434/api/chat}"  # URL API Ollama по умолчанию
BACKEND="${LLM_BACKEND:-ollama}"  # Используем ollama как бэкенд по умолчанию
MODEL="${LLM_MODEL:-saiga}"  # Имя модели по умолчанию для Ollama
BATCH_SIZE="${LLM_BATCH_SIZE:-5}"  # Размер пакета для обработки
MAX_RETRIES="${LLM_MAX_RETRIES:-3}"  # Максимальное количество попыток повтора при ошибках
TEMPERATURE="${LLM_TEMPERATURE:-0.1}"  # Температура для генерации (0.0-1.0)
TOP_P="${LLM_TOP_P:-0.7}"  # Top-p sampling (0.0-1.0)
MODULES_DIR="../translation_modules"
SOURCE_DIR="../extracted_scripts"  # Исходные .rpy файлы для v2
JSON_DIR="../temp_files/llm_json_v2"
BACKUP_DIR="../temp_files/backups"
CHARACTER_MAP="../data/characters.json"  # Карта персонажей с полом

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Интерактивный выбор файлов
select_files_cli() {
    print_header "📁 Выбор модулей для перевода"

    echo "Доступные модули (всего файлов в списке ниже):"
    echo ""

    # Получаем список всех .rpy файлов из extracted_scripts
    files=()
    index=1

    for file in "$SOURCE_DIR"/*.rpy; do
        if [ -f "$file" ]; then
            files+=("$file")
            file_name=$(basename "$file")

            # Проверяем, есть ли уже перевод
            local json_file="$JSON_DIR/${file_name%.rpy}.json"
            local translated_file="$JSON_DIR/${file_name%.rpy}_translated.json"
            local status=""

            if [ -f "$translated_file" ]; then
                status="${GREEN}[✓ Переведен]${NC}"
            elif [ -f "$json_file" ]; then
                status="${YELLOW}[○ Подготовлен]${NC}"
            else
                status="${BLUE}[  Не обработан]${NC}"
            fi

            echo -e "  ${BLUE}[$index]${NC} $file_name $status"
            index=$((index + 1))
        fi
    done

    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}Всего модулей: ${#files[@]}${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Легенда статусов:"
    echo -e "  ${GREEN}[✓ Переведен]${NC}     - перевод завершен"
    echo -e "  ${YELLOW}[○ Подготовлен]${NC}   - JSON создан, готов к переводу"
    echo -e "  ${BLUE}[  Не обработан]${NC} - еще не подготовлен"
    echo ""
    echo "Варианты выбора:"
    echo "  - Номера файлов (например: 1 3 5)"
    echo "  - Диапазон (например: 1-5)"
    echo "  - 'all' для всех файлов"
    echo "  - 'q' для отмены"
    echo ""
    echo -e "${GREEN}Прокрутите вверх ↑ чтобы увидеть весь список${NC}"
    echo ""
    read -p "Ваш выбор: " choice

    if [ "$choice" = "q" ]; then
        echo "Отменено"
        exit 0
    fi

    # Обработка выбора
    SELECTED_FILES=()

    if [ "$choice" = "all" ]; then
        SELECTED_FILES=("${files[@]}")
    elif [[ "$choice" =~ ^[0-9]+-[0-9]+$ ]]; then
        # Диапазон
        local start=$(echo "$choice" | cut -d'-' -f1)
        local end=$(echo "$choice" | cut -d'-' -f2)

        for ((i=start; i<=end; i++)); do
            if [ $i -ge 1 ] && [ $i -le ${#files[@]} ]; then
                SELECTED_FILES+=("${files[$((i-1))]}")
            fi
        done
    else
        # Отдельные номера
        for num in $choice; do
            if [ $num -ge 1 ] && [ $num -le ${#files[@]} ]; then
                SELECTED_FILES+=("${files[$((num-1))]}")
            fi
        done
    fi

    if [ ${#SELECTED_FILES[@]} -eq 0 ]; then
        print_error "Не выбрано ни одного файла"
        exit 1
    fi

    echo ""
    print_success "Выбрано файлов: ${#SELECTED_FILES[@]}"
    for file in "${SELECTED_FILES[@]}"; do
        echo "  - $(basename "$file")"
    done
    echo ""
}

# Создать резервную копию
backup_modules() {
    print_header "Создание резервной копии"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

    mkdir -p "$BACKUP_PATH"

    # Копируем финальные переводы из game/tl/ru/
    if [ -d "../game/tl/ru" ]; then
        cp -r "../game/tl/ru" "$BACKUP_PATH/" 2>/dev/null || true
        print_success "Резервная копия создана: $BACKUP_PATH"
    else
        print_warning "Директория ../game/tl/ru не существует, резервная копия не создана"
    fi
}

# Синхронизация JSON с исходным .rpy файлом
sync_json_with_source() {
    local source_file="$1"
    local json_file="$2"

    print_warning "Синхронизация: $(basename "$json_file")"

    # Создаем временный файл с актуальными строками из .rpy
    local temp_json="${json_file}.temp"
    python3 llm_translate_prepare_v2.py \
        --source "$source_file" \
        --output "$temp_json" \
        --character-map "$CHARACTER_MAP" >/dev/null 2>&1

    if [ ! -f "$temp_json" ]; then
        print_error "Не удалось создать временный файл"
        return 1
    fi

    # Если существующий JSON есть, объединяем
    if [ -f "$json_file" ]; then
        python3 - <<EOF
import json
import sys

# Загружаем оба файла
with open('$temp_json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

with open('$json_file', 'r', encoding='utf-8') as f:
    existing_data = json.load(f)

# Создаем словарь существующих строк по original
existing_originals = {}
for item in existing_data.get('strings', []):
    original = item.get('original', '')
    existing_originals[original] = item

# Собираем итоговый список строк
result_strings = list(existing_data.get('strings', []))
added_count = 0

# Добавляем новые строки, которых нет в существующем файле
for new_item in new_data.get('strings', []):
    original = new_item.get('original', '')
    if original not in existing_originals:
        result_strings.append(new_item)
        added_count += 1

# Обновляем метаданные
metadata = existing_data.get('metadata', {})
metadata['total_strings'] = len(result_strings)
if added_count > 0:
    metadata['last_sync'] = new_data.get('metadata', {}).get('source_path', '')

# Сохраняем результат
output = {
    'metadata': metadata,
    'strings': result_strings
}

with open('$json_file', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

if added_count > 0:
    print(f"  ➕ Добавлено новых строк: {added_count}")
else:
    print(f"  ✓ Новых строк не найдено")

sys.exit(0)
EOF
    else
        # Если существующего файла нет, просто переименовываем временный
        mv "$temp_json" "$json_file"
        print_success "  ✓ Создан новый JSON"
    fi

    # Удаляем временный файл
    rm -f "$temp_json"
}

# Шаг 1: Подготовка
prepare_modules() {
    print_header "Шаг 1: Подготовка модулей для перевода"

    mkdir -p "$JSON_DIR"

    if [ ${#SELECTED_FILES[@]} -gt 0 ]; then
        # CLI режим: обрабатываем только выбранные файлы
        for file in "${SELECTED_FILES[@]}"; do
            file_base=$(basename "$file" .rpy)
            echo "Подготовка: $file_base"
            python3 llm_translate_prepare_v2.py \
                --source "$file" \
                --output "$JSON_DIR/${file_base}.json" \
                --character-map "$CHARACTER_MAP"
        done
    else
        # Обычный режим: обрабатываем все файлы
        python3 llm_translate_prepare_v2.py \
            --batch "$SOURCE_DIR" \
            --batch-output "$JSON_DIR" \
            --character-map "$CHARACTER_MAP"
    fi

    print_success "Модули подготовлены"
}

# Шаг 2: Перевод через LLM
translate_modules() {
    print_header "Шаг 2: Перевод через LLM"

    echo "API URL: $API_URL"
    echo "Model: $MODEL"
    echo "Temperature: $TEMPERATURE"
    echo ""

    # Счетчики
    total=0
    success=0
    failed=0

    # Определяем список файлов для обработки
    files_to_process=()

    if [ ${#SELECTED_FILES[@]} -gt 0 ]; then
        # CLI режим: только выбранные файлы
        for file in "${SELECTED_FILES[@]}"; do
            local file_base=$(basename "$file" .rpy)
            local json_file="$JSON_DIR/${file_base}.json"

            # Если JSON не существует, подготовим его автоматически
            if [ ! -f "$json_file" ]; then
                print_warning "JSON не найден: $json_file"
                echo "Автоматическая подготовка..."
                python3 llm_translate_prepare_v2.py \
                    --source "$file" \
                    --output "$json_file" \
                    --character-map "$CHARACTER_MAP"
            fi

            if [ -f "$json_file" ]; then
                files_to_process+=("$json_file")
            else
                print_error "Не удалось подготовить: $file_base"
            fi
        done
    else
        # Обычный режим: все JSON файлы
        for json_file in "$JSON_DIR"/*.json; do
            if [ -f "$json_file" ]; then
                files_to_process+=("$json_file")
            fi
        done
    fi

    # Перебираем файлы для перевода
    for input_file in "${files_to_process[@]}"; do
        # Пропускаем уже переведенные файлы
        file_base=$(basename "$input_file" .json)
        if [[ "$file_base" == *"_translated" ]]; then
            continue
        fi

        output_file="${JSON_DIR}/${file_base}_translated.json"

        # Синхронизация JSON с исходным .rpy файлом (всегда, даже если уже переведен)
        source_rpy="${SOURCE_DIR}/${file_base}.rpy"
        if [ -f "$source_rpy" ]; then
            # Если уже переведен, синхронизируем _translated.json и используем его как input
            if [ -f "$output_file" ]; then
                sync_json_with_source "$source_rpy" "$output_file"
                # Используем _translated.json как входной файл для дополнения перевода
                input_file="$output_file"
            else
                sync_json_with_source "$source_rpy" "$input_file"
            fi
        else
            print_warning "Исходный файл не найден: $source_rpy (пропускаем синхронизацию)"
        fi

        total=$((total + 1))

        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Перевод модуля: $file_base"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        # Выполняем перевод
        echo -e "${BLUE}Перевод $input_file...${NC}"
        echo -e "${YELLOW}Параметры запуска:${NC}"
        echo "  Backend: $BACKEND"
        echo "  API URL: $API_URL"
        echo "  Model: $MODEL"
        echo "  Temperature: $TEMPERATURE"
        echo "  Top-p: $TOP_P"

        if python3 llm_translate.py \
            --input "$input_file" \
            --output "$output_file" \
            --backend "$BACKEND" \
            --api-url "$API_URL" \
            --model "$MODEL" \
            --batch-size "$BATCH_SIZE" \
            --max-retries "$MAX_RETRIES" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P"; then

            success=$((success + 1))
            print_success "Успешно переведен: $file_base"
        else
            failed=$((failed + 1))
            print_error "Ошибка при переводе: $file_base"
        fi
    done

    echo ""
    print_header "Статистика перевода"
    echo "Всего обработано: $total"
    print_success "Успешно: $success"
    if [ $failed -gt 0 ]; then
        print_error "Ошибки: $failed"
    fi
}

# Шаг 3: Упаковка в игру (включает конвертацию JSON->RPY и упаковку в game/tl/ru)
pack_translations() {
    print_header "Шаг 3: Упаковка переводов в игру"

    python3 smart_pack_translations.py

    print_success "Переводы упакованы"
}

# Проверка статуса перевода
check_status() {
    print_header "Проверка статуса перевода"

    python3 translation_helper.py
}

# Основная логика
main() {
    cd "$(dirname "$0")"  # Переход в директорию скрипта

    print_header "🤖 LLM Batch Translation Pipeline"
    echo "API: $API_URL"
    echo "Model: $MODEL"
    echo ""

    # Парсинг аргументов
    PREPARE_ONLY=false
    TRANSLATE_ONLY=false
    PACK_ONLY=false
    SKIP_BACKUP=false
    CLI_MODE=true  # CLI режим включен по умолчанию
    SELECTED_FILES=()

    for arg in "$@"; do
        case $arg in
            --prepare-only)
                PREPARE_ONLY=true
                ;;
            --translate-only)
                TRANSLATE_ONLY=true
                ;;
            --pack-only)
                PACK_ONLY=true
                ;;
            --skip-backup)
                SKIP_BACKUP=true
                ;;
            --help)
                echo "Использование: $0 [опции]"
                echo ""
                echo "Опции:"
                echo "  --prepare-only    Только подготовка JSON"
                echo "  --translate-only  Только перевод через LLM"
                echo "  --pack-only       Только упаковка в игру (JSON->RPY->game/tl/ru)"
                echo "  --skip-backup     Пропустить резервное копирование"
                echo "  --help            Показать эту справку"
                echo ""
                echo "Переменные окружения:"
                echo "  LLM_API_URL       URL API (по умолчанию: http://127.0.0.1:11434/api/chat)"
                echo "  LLM_MODEL         Название модели (по умолчанию: saiga)"
                echo "  LLM_BACKEND       Backend (по умолчанию: ollama)"
                echo "  LLM_TEMPERATURE   Temperature (по умолчанию: 0.1)"
                echo "  LLM_TOP_P         Top-p (по умолчанию: 0.7)"
                exit 0
                ;;
        esac
    done

    # Интерактивный выбор файлов (по умолчанию)
    select_files_cli
    echo ""

    # Резервное копирование (если не пропущено)
    if [ "$SKIP_BACKUP" = false ] && [ "$TRANSLATE_ONLY" = false ] && [ "$PREPARE_ONLY" = false ]; then
        backup_modules
        echo ""
    fi

    # Выполнение этапов
    if [ "$PREPARE_ONLY" = true ]; then
        prepare_modules
    elif [ "$TRANSLATE_ONLY" = true ]; then
        translate_modules
    elif [ "$PACK_ONLY" = true ]; then
        pack_translations
    else
        # Полный пайплайн
        prepare_modules
        echo ""

        translate_modules
        echo ""

        pack_translations
        echo ""

        check_status
    fi

    echo ""
    print_header "🎉 Готово!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Проверьте переводы в game/tl/ru/"
    echo "2. Запустите игру для тестирования: cd .. && ./Ravager.sh"
    echo "3. В игре выберите русский язык в настройках"
    echo ""
    echo "💡 Промежуточные файлы:"
    echo "   - JSON переводы: temp_files/llm_json_v2/*_translated.json"
    echo "   - RPY модули: translation_modules/*_ru.rpy"
    echo "   - Финальные переводы: game/tl/ru/*.rpy"
}

# Запуск
main "$@"
