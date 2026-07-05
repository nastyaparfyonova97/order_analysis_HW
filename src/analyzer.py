"""
Модуль содержит класс OrderAnalyzer для анализа данных о заказах.
"""

import pandas as pd
import os
import datetime
from typing import Dict, List, Optional, Tuple


class OrderAnalyzer:
    """
    Класс для анализа данных о заказах из CSV-файлов.
    """
    
    def __init__(self, config: Dict):
        """
        Инициализация анализатора с параметрами из конфигурации.
        """
        self.data_dir = config.get("data_dir", "data")
        self.reports_dir = config.get("reports_dir", "reports")
        self.logs_dir = config.get("logs_dir", "logs")
        self.status_column = config.get("status_column", "status")
        self.delivered_status = config.get("delivered_status", "Delivered")
        self.report_filename = config.get("report_filename", "summary_report.csv")
        self.error_log_filename = config.get("error_log_filename", "errors.log")
        
        self.processed_files = 0
        self.error_files = 0
        self.error_messages = []  # Храним ошибки для логирования
        
    def _log_error(self, file_name: str, error_message: str):
        """
        Записывает ошибку в лог-файл.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - ERROR - Файл '{file_name}': {error_message}\n"
        
        # Добавляем в список для сохранения
        self.error_messages.append(log_entry)
        
        # Сразу записываем в файл
        log_file_path = os.path.join(self.logs_dir, self.error_log_filename)
        try:
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Ошибка при записи в лог: {e}")
    
    def _validate_file(self, file_path: str) -> bool:
        """
        Проверяет, существует ли файл и не пустой ли он.
        """
        if not os.path.exists(file_path):
            self._log_error(os.path.basename(file_path), f"Файл не найден: {file_path}")
            return False
            
        if os.path.getsize(file_path) == 0:
            self._log_error(os.path.basename(file_path), "Файл пуст")
            return False
            
        return True
    
    def load_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Загружает CSV-файл с обработкой ошибок.
        """
        file_name = os.path.basename(file_path)
        
        try:
            # Проверяем существование и размер файла
            if not self._validate_file(file_path):
                return None
            
            # Пробуем загрузить файл 
            try:
                df = pd.read_csv(file_path)
            except pd.errors.EmptyDataError:
                self._log_error(file_name, "Файл пуст или содержит только заголовки")
                return None
            except pd.errors.ParserError as e:
                self._log_error(file_name, f"Ошибка парсинга CSV: {str(e)}")
                return None
            except Exception as e:
                self._log_error(file_name, f"Ошибка при чтении файла: {str(e)}")
                return None
            
            # Проверяем, что файл не пустой после загрузки
            if df.empty:
                self._log_error(file_name, "Файл не содержит данных")
                return None
            
            # Проверяем наличие необходимых колонок
            required_columns = ["order_id", "person_id", "order_date", "status", 
                              "total_amount", "currency", "payment_method", "shipping_method"]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self._log_error(file_name, f"Отсутствуют обязательные колонки: {missing_columns}")
                return None
            
            # Проверяем и конвертируем total_amount в числа
            try:
                # Пробуем конвертировать в числовой формат
                df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce")
                
                # Проверяем, есть ли хоть какие-то числа
                if df["total_amount"].isna().all():
                    self._log_error(file_name, "Колонка total_amount не содержит числовых значений")
                    return None
                
                # Проверяем, есть ли отрицательные суммы (ошибка в данных)
                negative_values = df[df["total_amount"] < 0]["total_amount"].count()
                if negative_values > 0:
                    self._log_error(file_name, f"Обнаружено {negative_values} отрицательных сумм")
                    # Заменяем отрицательные на 0 (или можно удалить такие строки)
                    df.loc[df["total_amount"] < 0, "total_amount"] = 0
                    
            except Exception as e:
                self._log_error(file_name, f"Ошибка при конвертации total_amount: {str(e)}")
                return None
            
            return df
            
        except Exception as e:
            self._log_error(file_name, f"Неизвестная ошибка при загрузке файла: {str(e)}")
            return None
    
    def filter_delivered_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Фильтрует заказы со статусом "Доставлен" с помощью pandas.
        """
        try:
            # Используем pandas для фильтрации
            delivered_df = df[df[self.status_column] == self.delivered_status].copy()
            return delivered_df
        except Exception as e:
            raise Exception(f"Ошибка при фильтрации заказов: {str(e)}")
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Рассчитывает метрики для доставленных заказов с помощью pandas.
        """
        try:
            if df.empty:
                return {
                    "total_revenue": 0.0,
                    "average_order_value": 0.0,
                    "orders_count": 0
                }
            
            total_revenue = df["total_amount"].sum()
            orders_count = len(df)
            
            # Вычисляем среднее
            average_order_value = df["total_amount"].mean() if orders_count > 0 else 0.0
            
            # Можно также использовать describe() для дополнительной статистики
            # stats = df["total_amount"].describe()
            
            return {
                "total_revenue": round(float(total_revenue), 2),
                "average_order_value": round(float(average_order_value), 2),
                "orders_count": int(orders_count)
            }
        except Exception as e:
            raise Exception(f"Ошибка при расчете метрик: {str(e)}")
    
    def get_file_stats(self, df: pd.DataFrame) -> Dict:
        """
        Получает дополнительную статистику по файлу.
        """
        try:
            total_orders = len(df)
            unique_customers = df["person_id"].nunique()
            status_counts = df[self.status_column].value_counts().to_dict()
            
            # Статистика по суммам
            amount_stats = df["total_amount"].describe().to_dict()
            
            return {
                "total_orders": total_orders,
                "unique_customers": unique_customers,
                "status_distribution": status_counts,
                "amount_stats": amount_stats
            }
        except Exception:
            # Если не получилось - возвращаем пустой словарь
            return {}
    
    def process_single_file(self, file_path: str) -> Optional[Dict]:
        """
        Обрабатывает один файл: загружает, фильтрует и рассчитывает метрики.
        """
        file_name = os.path.basename(file_path)
        
        # Загружаем файл
        df = self.load_file(file_path)
        if df is None:
            self.error_files += 1
            return None
        
        try:
            # Фильтруем доставленные заказы
            delivered_df = self.filter_delivered_orders(df)
            
            # Рассчитываем метрики
            metrics = self.calculate_metrics(delivered_df)
            
            # Добавляем имя файла к результатам
            result = {
                "filename": file_name,
                **metrics
            }
            
            self.processed_files += 1
            return result
            
        except Exception as e:
            self._log_error(file_name, f"Ошибка при обработке файла: {str(e)}")
            self.error_files += 1
            return None
    
    def process_all_files(self) -> List[Dict]:
        """
        Обрабатывает все CSV-файлы в папке data.
        """
        results = []
        
        # Получаем все CSV-файлы в папке data
        try:
            all_files = os.listdir(self.data_dir)
            csv_files = [f for f in all_files if f.lower().endswith('.csv')]
        except FileNotFoundError:
            self._log_error("system", f"Папка {self.data_dir} не найдена")
            print(f"Ошибка: Папка {self.data_dir} не найдена")
            return results
        except Exception as e:
            self._log_error("system", f"Ошибка при чтении папки: {str(e)}")
            print(f"Ошибка: {str(e)}")
            return results
        
        if not csv_files:
            self._log_error("system", "В папке data не найдено CSV-файлов")
            print("Предупреждение: В папке data не найдено CSV-файлов")
            return results
        
        print(f"Найдено файлов для обработки: {len(csv_files)}")
        print("-" * 40)
        
        for i, csv_file in enumerate(csv_files, 1):
            file_path = os.path.join(self.data_dir, csv_file)
            print(f"Обработка файла {i}/{len(csv_files)}: {csv_file}")
            
            result = self.process_single_file(file_path)
            if result is not None:
                results.append(result)
                print(f"  ✓ Обработан успешно")
            else:
                print(f"  ✗ Ошибка при обработке (см. лог)")
        
        print("-" * 40)
        print(f"\nОбработка завершена:")
        print(f"Успешно обработано файлов: {self.processed_files}")
        print(f"Файлов с ошибками: {self.error_files}")
        
        return results
    
    def save_results(self, results: List[Dict], filename: str = None):
        """
        Сохраняет результаты в CSV-файл с помощью pandas.
        """
        if not results:
            print("Нет результатов для сохранения")
            return
        
        if filename is None:
            filename = self.report_filename
        
        report_path = os.path.join(self.reports_dir, filename)
        
        try:
            # Создаем DataFrame из результатов
            df_results = pd.DataFrame(results)
            
            # Добавляем индекс (можно убрать, если не нужно)
            # df_results.index = range(1, len(df_results) + 1)
            
            # Сохраняем в CSV 
            df_results.to_csv(report_path, index=False, encoding='utf-8')
            
            print(f"\nРезультаты сохранены в файл: {report_path}")
            
            # Выводим краткую сводку
            print("\nСводка по файлам:")
            print(df_results.to_string(index=False))
            
        except Exception as e:
            error_msg = f"Ошибка при сохранении результатов: {str(e)}"
            self._log_error("system", error_msg)
            print(f"Ошибка: {error_msg}")
    
    def run(self):
        """
        Основной метод для запуска полного цикла обработки.
        """
        print("=" * 60)
        print("НАЧАЛО АНАЛИЗА ДАННЫХ О ЗАКАЗАХ")
        print("=" * 60)
        print()
        
        # Обрабатываем все файлы
        results = self.process_all_files()
        
        # Сохраняем результаты
        if results:
            self.save_results(results)
            print(f"\n✅ Всего успешно обработано файлов: {len(results)}")
        else:
            print("\n⚠️ Не было обработано ни одного файла")
        
        # Проверяем, были ли ошибки
        if self.error_messages:
            print(f"\n⚠️ Были ошибки при обработке {self.error_files} файлов")
            print(f"   Подробности в файле: {os.path.join(self.logs_dir, self.error_log_filename)}")
        
        print("\n" + "=" * 60)
        print("АНАЛИЗ ЗАВЕРШЕН")
        print("=" * 60)
