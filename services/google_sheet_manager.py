import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetManager:
    def __init__(self, creds_dir):
        self.service = self._authorize_google_sheets(creds_dir)
        self.indices = None

    def _authorize_google_sheets(self, creds_path):
        if not os.path.exists(creds_path):
            raise FileNotFoundError(
                f"Credentials file not found: {creds_path}")

        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        creds = Credentials.from_service_account_file(
            creds_path, scopes=scopes)
        return build('sheets', 'v4', credentials=creds)

    def get_sheet_data(self, spreadsheet_id, worksheet_name, columns_map):
        data = self._fetch_sheet_data(spreadsheet_id, worksheet_name)
        if not data:
            raise ValueError(f"No data found in the sheet '{worksheet_name}'")
        headers, data_rows = data[0], data[1:]
        column_indices = self.map_column_indices(headers, columns_map)

        self.indices = column_indices
        return self._extract_data(data_rows, column_indices)

    def _fetch_sheet_data(self, spreadsheet_id, worksheet_name):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=worksheet_name
        ).execute()
        data = result.get('values', [])
        if not data:
            raise ValueError(f"No data found in the sheet '{worksheet_name}'")
        return data

    def map_column_indices(self, headers, columns_map):
        column_indices = {}
        missing_columns = []

        for key, col in columns_map.items():
            if col in headers:
                column_indices[key] = headers.index(col)
            else:
                missing_columns.append(col)

        if missing_columns:
            print(f"Missing columns: {', '.join(missing_columns)}")

        return column_indices

    def _extract_data(self, data_rows, column_indices):
        return [
            {
                key: row[idx] if idx < len(row) else ''
                for key, idx in column_indices.items()
            }
            for row in data_rows
        ]

    def _get_column_letter(self, col_index):
        letter = ""
        while col_index >= 0:
            letter = chr(col_index % 26 + 65) + letter
            col_index = col_index // 26 - 1
        return letter

    def update_sheet_data(self, spreadsheet_id, worksheet_name, data, columns_map):
        try:
            headers = self._fetch_sheet_data(spreadsheet_id, worksheet_name)[0]
            column_indices = self.map_column_indices(headers, columns_map)

            row_offset = 2  # Начинаем обновление со второй строки после заголовков
            required_rows = len(data) + row_offset
            self.ensure_rows_exist(spreadsheet_id, worksheet_name, required_rows)

            max_rows, max_columns = self._get_sheet_size(spreadsheet_id, worksheet_name)

            updates = self._prepare_updates(
                worksheet_name, data, headers, column_indices, max_rows
            )

            if updates:
                self._batch_update(spreadsheet_id, updates)
                print("Data successfully updated")
        except HttpError as error:
            raise RuntimeError(f"Error updating data: {error}")
        except ValueError as value_error:
            print(value_error)

    def _prepare_updates(self, worksheet_name, data, headers, column_indices, max_rows):
        updates = []
        row_offset = 2  # Номер строки, с которой начинается ввод данных

        for i, row_data in enumerate(data, start=row_offset):
            if i > max_rows:
                raise ValueError(f"Row index {i} exceeds max rows: {max_rows}")

            for key, value in row_data.items():
                if key in column_indices:
                    col_index = column_indices[key]
                    col_letter = self._get_column_letter(col_index)
                    range_str = f'{worksheet_name}!{col_letter}{i}:{col_letter}{i}'

                    updates.append({'range': range_str, 'values': [[value]]})

        return updates

    def _batch_update(self, spreadsheet_id, updates):
        body = {'valueInputOption': 'USER_ENTERED', 'data': updates}
        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
        except Exception as e:
            raise RuntimeError(f"Error updating data: {e}")

    def _get_sheet_size(self, spreadsheet_id, worksheet_name):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        for sheet in sheets:
            if sheet['properties']['title'] == worksheet_name:
                grid_properties = sheet['properties']['gridProperties']
                return grid_properties['rowCount'], grid_properties['columnCount']
        raise ValueError(f"Worksheet '{worksheet_name}' not found")

    def ensure_rows_exist(self, spreadsheet_id, worksheet_name, required_rows):
        max_rows, _ = self._get_sheet_size(spreadsheet_id, worksheet_name)
        if required_rows > max_rows:
            worksheet_id = self._get_worksheet_id(spreadsheet_id, worksheet_name)
            self.add_rows_to_sheet(spreadsheet_id, worksheet_id, required_rows - max_rows)

    def _get_worksheet_id(self, spreadsheet_id, worksheet_name):
        sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        for sheet in sheets:
            if sheet['properties']['title'] == worksheet_name:
                return sheet['properties']['sheetId']
        raise ValueError(f"Worksheet '{worksheet_name}' not found")

    def add_rows_to_sheet(self, spreadsheet_id, worksheet_id, num_rows):
        requests = [
            {
                "appendDimension": {
                    "sheetId": worksheet_id,
                    "dimension": "ROWS",
                    "length": num_rows,
                }
            }
        ]
        body = {"requests": requests}
        self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
