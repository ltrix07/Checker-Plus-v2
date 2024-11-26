import csv
import os
import logging
from typing import List, Dict, Any


class CSV:
    def __init__(self, file_path: str, columns: dict | list):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__class__.__name__)

        self.columns = columns
        self.path = file_path

    def create_file(self):
        """
        Создает CSV файл по пути указаному при вызове класса, с указанными колонками
        :return: None
        """
        headers = self.columns if isinstance(self.columns, list) else list(self.columns.keys())

        with open(self.path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

        self.logger.info(f"The file has been created: {self.path}")

    def append_to_file(self, data: List[Dict[str, Any]]):
        """
        Добавляет в указанный при создании класса файл указанные данные.
        :param data: Данные, которые должны быть записаны в файл
        :return: None
        """
        if not os.path.isfile(self.path):
            self.create_file()

        with open(self.path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            existing_columns = next(reader, None)

        if not existing_columns:
            raise ValueError("The file does not contain any headers.")

        with open(self.path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row_data in data:
                row = [row_data.get(col, '') for col in existing_columns]
                writer.writerow(row)
        self.logger.info(f"Data added to the file: {self.path}")

