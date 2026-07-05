import os

# Пути к папкам
DATA_DIR = "data"
REPORTS_DIR = "reports"
LOGS_DIR = "logs"

# Настройки для фильтрации
STATUS_COLUMN = "status"
DELIVERED_STATUS = "Delivered"

# Настройки для отчета
REPORT_FILENAME = "summary_report.csv"  # Имя выходного файла
ERROR_LOG_FILENAME = "errors.log"

# Создание необходимых папок, если они не существуют
for directory in [DATA_DIR, REPORTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)
