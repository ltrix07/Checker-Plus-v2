import csv
import os
import logging
from typing import List, Dict, Any


class FileHandler:
    def __init__(self, file_path: str, delete_prev: bool = False):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.path = file_path

        if delete_prev:
            self.delete_file()

    def delete_file(self):
        if os.path.isfile(self.path):
            os.remove(self.path)
            self.logger.info(f"File deleted: {self.path}")
        else:
            self.logger.info(f"File not found: {self.path}")

    def file_exists(self) -> bool:
        return os.path.isfile(self.path)


class CSV(FileHandler):
    def create_file(self, columns: dict | list):
        """
        Создает CSV файл с указанными колонками.
        """
        headers = columns if isinstance(columns, list) else list(columns.keys())

        with open(self.path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

        self.logger.info(f"The file has been created: {self.path}")

    def read(self):
        """
        Читает данные из CSV файла и возвращает их в виде списка словарей.
        """
        data_list = []

        with open(self.path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                formatted_row = {
                    key: int(value) if value.isdigit() else float(value) if value.replace('.', '', 1).isdigit() else value
                    for key, value in row.items()
                }
                data_list.append(formatted_row)
        return data_list

    def append_to_file(self, data: List[Dict[str, Any]], col_map: dict | list):
        """
        Добавляет данные в CSV файл.
        """
        if not self.file_exists():
            self.create_file(col_map)

        with open(self.path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            existing_columns = next(reader, None)

        if not existing_columns:
            raise ValueError("The file does not contain any headers.")

        with open(self.path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)

            for row_data in data:
                if not row_data:
                    continue
                row = [row_data.get(col, '') for col in existing_columns]
                writer.writerow(row)
        self.logger.info(f"Data added to the file: {self.path}")


class TXT(FileHandler):
    def create_file(self, columns: dict | list):
        headers = columns if isinstance(columns, list) else list(columns.keys())

        with open(self.path, 'w') as txt_file:
            txt_file.write("\t".join(headers) + "\n")

        self.logger.info(f"The file has been created: {self.path}")

    def read(self):
        data_list = []

        with open(self.path, 'r') as txt_file:
            lines = txt_file.readlines()

        if not lines:
            return data_list

        headers = lines[0].strip().split("\t")

        for line in lines[1:]:
            values = line.strip().split("\t")
            formatted_row = {
                headers[i]: int(values[i]) if values[i].isdigit() else float(values[i]) if values[i].replace('.', '', 1).isdigit() else values[i]
                for i in range(len(headers))
            }
            data_list.append(formatted_row)

        return data_list

    def append_to_file(self, data: List[Dict[str, Any]], col_map: dict | list):
        if not self.file_exists():
            self.create_file(col_map)

        with open(self.path, 'r') as txt_file:
            existing_columns = txt_file.readline().strip().split("\t")

        if not existing_columns:
            raise ValueError("The file does not contain any headers.")

        with open(self.path, 'a') as txt_file:
            for row_data in data:
                if not row_data:
                    continue
                row = [str(row_data.get(col, '')) for col in existing_columns]
                txt_file.write("\t".join(row) + "\n")
