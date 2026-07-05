import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analyzer import OrderAnalyzer
import config


def main():
    """
    Основная функция запуска приложения.
    """
    try:
        app_config = {
            "data_dir": config.DATA_DIR,
            "reports_dir": config.REPORTS_DIR,
            "logs_dir": config.LOGS_DIR,
            "status_column": config.STATUS_COLUMN,
            "delivered_status": config.DELIVERED_STATUS,
            "report_filename": config.REPORT_FILENAME,
            "error_log_filename": config.ERROR_LOG_FILENAME
        }
        
        analyzer = OrderAnalyzer(app_config)
        analyzer.run()
        
    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\nКритическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
