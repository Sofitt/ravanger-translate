#!/bin/bash

# Скрипт для массового перевода модулей через LLM
# Использование: ./llm_batch_translate.sh [--prepare-only] [--translate-only] [--apply-only]

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
JSON_DIR="../temp_files/llm_json"
BACKUP_DIR="../temp_files/backups"

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

# Создать резервную копию
backup_modules() {
    print_header "Создание резервной копии"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"

    mkdir -p "$BACKUP_PATH"
    cp -r "$MODULES_DIR"/*.rpy "$BACKUP_PATH/" 2>/dev/null || true

    print_success "Резервная копия создана: $BACKUP_PATH"
}

# Шаг 1: Подготовка
prepare_modules() {
    print_header "Шаг 1: Подготовка модулей для перевода"

    mkdir -p "$JSON_DIR"

    python3 llm_translate_prepare.py \
        --batch "$MODULES_DIR" \
        --batch-output "$JSON_DIR"

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

    # Перебираем все JSON файлы
    for input_file in "$JSON_DIR"/*.json; do
        # Пропускаем уже переведенные файлы
        basename=$(basename "$input_file" .json)
        if [[ "$basename" == *"_translated" ]]; then
            continue
        fi

        output_file="${JSON_DIR}/${basename}_translated.json"

        # Пропускаем, если перевод уже существует
        if [ -f "$output_file" ]; then
            print_warning "Пропущен (уже переведен): $basename"
            continue
        fi


        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Перевод модуля: $basename"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        # Выполняем перевод
        echo -e "${BLUE}Перевод $json_file...${NC}"
        echo -e "${YELLOW}Параметры запуска:${NC}"
        echo "  Backend: $BACKEND"
        echo "  API URL: $API_URL"
        echo "  Model: $MODEL"
        echo "  Temperature: $TEMPERATURE"
        echo "  Top-p: $TOP_P"

        if python3 llm_translate.py \
            --input "$json_file" \
            --output "${json_file%.json}_translated.json" \
            --backend "$BACKEND" \
            --api-url "$API_URL" \
            --model "$MODEL" \
            --batch-size "$BATCH_SIZE" \
            --max-retries "$MAX_RETRIES" \
            --temperature "$TEMPERATURE" \
            --top-p "$TOP_P"; then

            success=$((success + 1))
            print_success "Успешно переведен: $basename"
        else
            failed=$((failed + 1))
            print_error "Ошибка при переводе: $basename"
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

# Шаг 3: Применение переводов
apply_translations() {
    print_header "Шаг 3: Применение переводов"

    python3 llm_translate_apply.py \
        --batch-json "$JSON_DIR" \
        --batch-rpy "$MODULES_DIR"

    print_success "Переводы применены"
}

# Шаг 4: Упаковка в игру
pack_translations() {
    print_header "Шаг 4: Упаковка переводов в игру"

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
    APPLY_ONLY=false
    SKIP_BACKUP=false

    for arg in "$@"; do
        case $arg in
            --prepare-only)
                PREPARE_ONLY=true
                ;;
            --translate-only)
                TRANSLATE_ONLY=true
                ;;
            --apply-only)
                APPLY_ONLY=true
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
                echo "  --apply-only      Только применение переводов"
                echo "  --skip-backup     Пропустить резервное копирование"
                echo "  --help            Показать эту справку"
                echo ""
                echo "Переменные окружения:"
                echo "  LLM_API_URL       URL API (по умолчанию: http://localhost:8080/v1/chat/completions)"
                echo "  LLM_MODEL         Название модели (по умолчанию: local-model)"
                echo "  LLM_TEMPERATURE   Temperature (по умолчанию: 0.3)"
                echo "  LLM_MAX_TOKENS    Max tokens (по умолчанию: 2000)"
                exit 0
                ;;
        esac
    done

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
    elif [ "$APPLY_ONLY" = true ]; then
        apply_translations
        echo ""
        pack_translations
    else
        # Полный пайплайн
        prepare_modules
        echo ""

        translate_modules
        echo ""

        apply_translations
        echo ""

        pack_translations
        echo ""

        check_status
    fi

    echo ""
    print_header "🎉 Готово!"
    echo ""
    echo "Следующие шаги:"
    echo "1. Проверьте качество переводов в translation_modules/"
    echo "2. Запустите игру для тестирования: cd .. && ./Ravager.sh"
    echo "3. В игре выберите русский язык в настройках"
}

# Запуск
main "$@"
