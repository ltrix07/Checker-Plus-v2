import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleSheetManager:
    def __init__(self, creds_dir):
        self.service = self._authorize_google_sheets(creds_dir)
        self.indices = None

    def _authorize_google_sheets(self, service_account_file):
        scopes = ['https://www.googleapis.com/auth/spreadsheets']

        creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)

        service = build('sheets', 'v4', credentials=creds)

        return service

    def get_sheet_data(self, spreadsheet_id, worksheet_name, columns_map, max_retries=10, retry_delay=60):
        retries = 0
        while retries < max_retries:
            try:
                data = self._fetch_sheet_data(spreadsheet_id, worksheet_name)
                if not data:
                    raise ValueError(f"No data found in the sheet '{worksheet_name}'")

                headers, data_rows = data[0], data[1:]

                column_indices = self.map_column_indices(headers, columns_map)

                self.indices = column_indices
                return self._extract_data(data_rows, column_indices)
            except HttpError as error:
                if error.resp.status in [429, 500, 503]:
                    retries += 1
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Unhandled HTTP error: {error}") from error
            except TimeoutError:
                retries += 1
                time.sleep(retry_delay)
        else:
            raise RuntimeError(f"Failed to update data after {max_retries} attempts due to rate limiting.")

    def update_sheet_data(self, spreadsheet_id, worksheet_name, data, columns_map, max_retries=10, retry_delay=60):
        retries = 0
        while retries < max_retries:
            try:
                headers = self._fetch_sheet_data(spreadsheet_id, worksheet_name)[0]
                column_indices = self.map_column_indices(headers, columns_map)
                self._ensure_rows_exist(spreadsheet_id, worksheet_name, len(data) + 2)

                updates = self._prepare_updates(worksheet_name, data, column_indices)
                if updates:
                    self._batch_update_in_chunks(spreadsheet_id, updates, chunk_size=1000)
                    return True
            except HttpError as error:
                if error.resp.status in [429, 500, 503]:
                    retries += 1
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"Unhandled HTTP error: {error}") from error
            except ValueError:
                break
        else:
            raise RuntimeError(f"Failed to update data after {max_retries} attempts due to rate limiting.")

    def _extract_data(self, data_rows, column_indices):
        return [
            {
                key: row[idx] if idx < len(row) else ''
                for key, idx in column_indices.items()
            }
            for row in data_rows
        ]

    def _batch_update_in_chunks(self, spreadsheet_id, updates, chunk_size=1000, max_retries=15, initial_delay=2):
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i + chunk_size]
            retries = 0
            delay = initial_delay

            while retries < max_retries:
                try:
                    self._batch_update(spreadsheet_id, chunk)
                    time.sleep(2)
                    break
                except HttpError as error:
                    if error.resp.status in [429, 503]:
                        retries += 1
                        print(
                            f"Ошибка {error.resp.status}: {error.reason}. Попытка {retries}/{max_retries}. Повтор через {delay} сек...")
                        time.sleep(delay)
                        delay *= 2
                    else:
                        raise RuntimeError(f"Ошибка выполнения batch update: {error}")
            else:
                raise RuntimeError(f"Превышено количество попыток для чанка: {chunk}")

    def _batch_update(self, spreadsheet_id, updates):
        body = {
            "data": updates,
            "valueInputOption": "RAW"
        }

        try:
            result = (
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=spreadsheet_id, body=body
                ).execute()
            )
            return result
        except HttpError as error:
            print(f"Error in batch update: {error}")
            raise

    def _prepare_updates(self, worksheet_name, data, column_indices):
        updates = []
        for i, row_data in enumerate(data, start=2):
            for key, value in row_data.items():
                if key in column_indices:
                    col_letter = self._get_column_letter(column_indices[key])
                    range_str = f'{worksheet_name}!{col_letter}{i}'
                    updates.append({'range': range_str, 'values': [[value]]})
        return updates

    def _get_column_letter(self, col_index):
        letter = ""
        while col_index >= 0:
            letter = chr(col_index % 26 + 65) + letter
            col_index = col_index // 26 - 1
        return letter

    def _fetch_sheet_data(self, spreadsheet_id, worksheet_name):
        result = self.service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=worksheet_name,
            valueRenderOption='UNFORMATTED_VALUE'
        ).execute()
        return result.get('values', [])

    def map_column_indices(self, headers, columns_map):
        if not headers:
            raise ValueError("Sheet headers are empty or missing")
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

    def _ensure_rows_exist(self, spreadsheet_id, worksheet_name, required_rows):
        try:
            max_rows, _ = self._get_sheet_size(spreadsheet_id, worksheet_name)
            if required_rows > max_rows:
                worksheet_id = self._get_worksheet_id(spreadsheet_id, worksheet_name)
                self.add_rows_to_sheet(spreadsheet_id, worksheet_id, required_rows - max_rows)
        except HttpError as error:
            raise RuntimeError(f"Error ensuring rows exist: {error}")

    def _get_sheet_size(self, spreadsheet_id, worksheet_name):
        try:
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == worksheet_name:
                    grid_properties = sheet['properties']['gridProperties']
                    return grid_properties['rowCount'], grid_properties['columnCount']
            raise ValueError(f"Worksheet '{worksheet_name}' not found")
        except HttpError as error:
            raise RuntimeError(f"Error fetching sheet size: {error}")

    def _get_worksheet_id(self, spreadsheet_id, worksheet_name):
        try:
            sheet_metadata = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == worksheet_name:
                    return sheet['properties']['sheetId']
            raise ValueError(f"Worksheet '{worksheet_name}' not found")
        except HttpError as error:
            raise RuntimeError(f"Error fetching worksheet ID: {error}")

    def add_rows_to_sheet(self, spreadsheet_id, worksheet_id, num_rows):
        try:
            requests = [{
                "appendDimension": {
                    "sheetId": worksheet_id,
                    "dimension": "ROWS",
                    "length": num_rows,
                }
            }]
            body = {"requests": requests}
            self.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
        except HttpError as error:
            raise RuntimeError(f"Error adding rows: {error}")

    def update_sheet_data_by_sku(
            self, spreadsheet_id, worksheet_name, data, sku_column, columns_map, max_retries=10, retry_delay=60
    ):
        retries = 0

        while retries < max_retries:
            try:
                sheet_data = self._fetch_sheet_data(spreadsheet_id, worksheet_name)
                if not sheet_data:
                    raise ValueError(f"No data found in the sheet '{worksheet_name}'")

                headers = sheet_data[0]
                if sku_column not in headers:
                    raise ValueError(f"SKU column '{sku_column}' not found in the sheet headers")

                sku_index = headers.index(sku_column)
                column_indices = self.map_column_indices(headers, columns_map)

                sku_list = [row[sku_column] for row in data if sku_column in row]

                data_rows = [row for row in sheet_data[1:] if any(row)]

                row_map = {}
                for idx, row in enumerate(data_rows):
                    if len(row) > sku_index and row[sku_index] in sku_list:
                        if row[sku_index] not in row_map:
                            row_map[row[sku_index]] = idx + 2

                updates = []
                for row_data in data:
                    sku = row_data.get(sku_column)
                    if sku in row_map:
                        row_index = row_map[sku]
                        for key, value in row_data.items():
                            if key in column_indices:
                                col_letter = self._get_column_letter(column_indices[key])
                                range_str = f'{worksheet_name}!{col_letter}{row_index}'
                                updates.append({'range': range_str, 'values': [[value]]})

                if updates:
                    self._batch_update_in_chunks(spreadsheet_id, updates)
                    print(f"Updated {len(updates)} cells in {worksheet_name}.")
                    ret urn True
                else:
                    print("No updates were made because no matching SKU was found.")
                    return False

            except TimeoutError:
                retries += 1
                print(f"Timeout error occurred. Retrying {retries}/{max_retries}...")
                time.sleep(retry_delay)

        raise RuntimeError(f"Failed to update data after {max_retries} attempts due to rate limiting.")
