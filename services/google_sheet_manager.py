import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleSheetManager:
    def __init__(self, creds_dir='db\\#general'):
        self.service = self._authorize_google_sheets(
            os.path.join(creds_dir, 'credentials.json'))

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
        column_indices = self._map_column_indices(headers, columns_map)
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


    def _map_column_indices(self, headers, columns_map):
        column_indices = {}
        missing_columns = []  

        for key, col in columns_map.items():
            if col in headers:
                column_indices[key] = headers.index(col)
            else:
                missing_columns.append(col)  

        # Виводимо відсутні колонки
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

    def _get_column_letter(self, column_index):
        letters = ""
        while column_index >= 0:
            letters = chr((column_index % 26) + ord('A')) + letters
            column_index = column_index // 26 - 1
        return letters

    def update_sheet_data(self, spreadsheet_id, worksheet_name, data, columns_map):
        try:
            headers = self._fetch_sheet_data(spreadsheet_id, worksheet_name)[0]
            column_indices = self._map_column_indices(headers, columns_map)

            updates = self._prepare_updates(
                worksheet_name, data, headers, column_indices)

            if updates:
                self._batch_update(spreadsheet_id, updates)
                print("Data successfully updated")
        except HttpError as error:
            raise RuntimeError(f"Error updating data: {error}")
        except ValueError as value_error:
            print(value_error)


    def _prepare_updates(self, worksheet_name, data, headers, column_indices):
        updates = []
        for i, row_data in enumerate(data):
            row_index = i + 2

            row_update = [''] * len(headers)

            for key, value in row_data.items():
                if key in column_indices:
                    row_update[column_indices[key]] = value

            for key in row_data.keys():
                if key in column_indices:
                    col_index = column_indices[key]
                    col_letter = self._get_column_letter(col_index)
                    range_str = f'{worksheet_name}!{col_letter}{row_index}:{col_letter}{row_index}'

                    updates.append({'range': range_str, 'values': [
                                [row_update[col_index]]]})

        return updates
    

    def _batch_update(self, spreadsheet_id, updates):
        body = {'valueInputOption': 'USER_ENTERED', 'data': updates}
        try:
            self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=spreadsheet_id, body=body).execute()
        except Exception as e:
            raise RuntimeError(f"Error updating data: {e}")

    
