from unittest.mock import Mock
import unittest
from unittest.mock import patch, MagicMock, Mock
from googleapiclient.errors import HttpError
from services.google_sheet_manager import GoogleSheetManager


class TestGoogleSheetManager(unittest.TestCase):
    @patch('services.google_sheet_manager.build')
    @patch('services.google_sheet_manager.Credentials.from_service_account_file')
    def setUp(self, mock_creds, mock_build):
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service
        self.manager = GoogleSheetManager(creds_dir='db\\#general')

    def test_authorize_google_sheets_missing_creds(self):
        with self.assertRaises(FileNotFoundError):
            self.manager._authorize_google_sheets(
                "db\\#general\\non_existent_file.json")

    
    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    def test_get_sheet_data_calls_fetch_method(self, mock_fetch_sheet_data):
        mock_fetch_sheet_data.return_value = [
            ['sku', 'price amazon', 'supplier1'],
            ['12345', '19.99', 'Supplier A']
        ]
        columns_map = {'SKU': 'sku', 'Price Amazon': 'price amazon'}
        self.manager.get_sheet_data(
            "spreadsheet_id", "worksheet_name", columns_map)

        mock_fetch_sheet_data.assert_called_once_with(
            "spreadsheet_id", "worksheet_name")
        
    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    def test_get_sheet_data_no_data(self, mock_fetch_sheet_data):
        mock_fetch_sheet_data.return_value = []  

        with self.assertRaises(ValueError) as context:
            self.manager.get_sheet_data("spreadsheet_id", "worksheet_name", {})

        self.assertIn("No data found in the sheet", str(context.exception))


        
    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    def test_get_sheet_data_invalid_format(self, mock_fetch_sheet_data):
        mock_fetch_sheet_data.return_value = [
            ['sku', 'price amazon'],
            ['12345']
        ]
        columns_map = {'SKU': 'sku', 'Price Amazon': 'price amazon'}

        result = self.manager.get_sheet_data(
            "spreadsheet_id", "worksheet_name", columns_map)

        expected_result = [{'SKU': '12345', 'Price Amazon': ''}]
        self.assertEqual(result, expected_result)

                
    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    def test_get_sheet_data_missing_column_key(self, mock_fetch_sheet_data):
        mock_fetch_sheet_data.return_value = [
            ['sku', 'price amazon'],
            ['12345', '19.99']
        ]
        columns_map = {'SKU': 'sku', 'Supplier': 'non_existent_column'}
        result = self.manager.get_sheet_data(
            "spreadsheet_id", "worksheet_name", columns_map)
        expected_result = [{'SKU': '12345'}]
        self.assertEqual(result, expected_result)

    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    def test_get_sheet_data_fetch_error(self, mock_fetch_sheet_data):
        mock_fetch_sheet_data.side_effect = ValueError(
            "No data found in the sheet")
        with self.assertRaises(ValueError) as context:
            self.manager.get_sheet_data("spreadsheet_id", "worksheet_name", {})
        self.assertIn("No data found in the sheet", str(context.exception))

    def test_map_column_indices(self):
        headers = ['sku', 'price amazon', 'supplier1']
        columns_map = {'SKU': 'sku',
                       'Price Amazon': 'price amazon', 'Supplier': 'supplier1'}
        expected_indices = {'SKU': 0, 'Price Amazon': 1, 'Supplier': 2}
        result = self.manager._map_column_indices(headers, columns_map)
        self.assertEqual(result, expected_indices)

    def test_get_column_letter(self):
        self.assertEqual(self.manager._get_column_letter(0), 'A')
        self.assertEqual(self.manager._get_column_letter(25), 'Z')
        self.assertEqual(self.manager._get_column_letter(26), 'AA')

    @patch.object(GoogleSheetManager, '_batch_update')
    def test_update_sheet_data_partial_update(self, mock_batch_update):
        self.manager.get_sheet_data = MagicMock(return_value=[
            {'SKU': '12345', 'Price Amazon': '19.99', 'Supplier': 'Supplier A'}
        ])
        self.manager._fetch_sheet_data = MagicMock(return_value=[
            ['sku', 'price amazon', 'supplier1'],
            ['12345', '19.99', 'Supplier A']
        ])
        data = [{'SKU': '12345', 'Price Amazon': '22.99'}]
        columns_map = {'SKU': 'sku',
                       'Price Amazon': 'price amazon', 'Supplier': 'supplier1'}

        self.manager.update_sheet_data(
            "spreadsheet_id", "worksheet_name", data, columns_map)
        self.assertTrue(mock_batch_update.called)

    
    @patch.object(GoogleSheetManager, '_batch_update')
    def test_prepare_updates(self, mock_batch_update):
        headers = ['sku', 'price amazon', 'supplier1']
        data = [
            {'SKU': '12345', 'Price Amazon': '19.99', 'Supplier': 'Supplier A'},
            {'SKU': '67890', 'Price Amazon': '24.99', 'Supplier': 'Supplier B'}
        ]
        columns_map = {'SKU': 'sku',
                       'Price Amazon': 'price amazon', 'Supplier': 'supplier1'}
        column_indices = self.manager._map_column_indices(headers, columns_map)

        updates = self.manager._prepare_updates(
            'worksheet_name', data, headers, column_indices)

        expected_updates = [
            {'range': 'worksheet_name!A2:A2', 'values': [['12345']]},
            {'range': 'worksheet_name!B2:B2', 'values': [['19.99']]},
            {'range': 'worksheet_name!C2:C2', 'values': [['Supplier A']]},
            {'range': 'worksheet_name!A3:A3', 'values': [['67890']]},
            {'range': 'worksheet_name!B3:B3', 'values': [['24.99']]},
            {'range': 'worksheet_name!C3:C3', 'values': [['Supplier B']]}
        ]

        self.assertEqual(updates, expected_updates)


    def test_batch_update_exception_handling(self):
        mock_resp = Mock()
        mock_resp.reason = "Mocked error reason"
        mock_error = HttpError(resp=mock_resp, content=b"error")

        self.manager.service.spreadsheets().values().batchUpdate.side_effect = mock_error

        with self.assertRaises(RuntimeError) as context:
            self.manager._batch_update("spreadsheet_id", [])

        self.assertIn("Error updating data", str(context.exception))
        

    @patch.object(GoogleSheetManager, '_batch_update')
    @patch.object(GoogleSheetManager, '_prepare_updates')
    def test_update_sheet_data_full_update(self, mock_prepare_updates, mock_batch_update):
        self.manager.get_sheet_data = MagicMock(return_value=[
            {'SKU': '12345', 'Price Amazon': '19.99', 'Supplier': 'Supplier A'}
        ])

        self.manager._fetch_sheet_data = MagicMock(return_value=[
            ['sku', 'price amazon', 'supplier1'],
            ['12345', '19.99', 'Supplier A']
        ])

       
        data = [{'SKU': '12345', 'Price Amazon': '22.99'}]
        columns_map = {'SKU': 'sku', 'Price Amazon': 'price amazon'}

        mock_prepare_updates.return_value = [
            {'range': 'worksheet_name!B2:B2', 'values': [
                ['22.99']]} 
        ]

        self.manager.update_sheet_data("spreadsheet_id", "worksheet_name", data, columns_map)
        mock_batch_update.assert_called_once_with("spreadsheet_id", mock_prepare_updates.return_value)


    def test_prepare_updates_empty_data(self):
        headers = ['sku', 'price amazon']
        data = []
        columns_map = {'SKU': 'sku', 'Price Amazon': 'price amazon'}
        column_indices = self.manager._map_column_indices(headers, columns_map)

        updates = self.manager._prepare_updates(
            'worksheet_name', data, headers, column_indices)

        self.assertEqual(updates, []) 
   
    
    
    @patch.object(GoogleSheetManager, '_fetch_sheet_data')
    @patch.object(GoogleSheetManager, '_batch_update')
    def test_update_sheet_data_with_missing_columns(self, mock_batch_update, mock_fetch_sheet_data):
        mock_fetch_sheet_data.return_value = [
            ['sku', 'price amazon'], 
            ['12345', '19.99']
        ]

        data = [{'SKU': '12345', 'Price Amazon': '22.99', 'Supplier': 'Supplier A'}]
        columns_map = {
            'SKU': 'sku',
            'Price Amazon': 'price amazon',
            'Supplier': 'supplier' 
        }

        self.manager.update_sheet_data(
            "spreadsheet_id", "worksheet_name", data, columns_map)

        mock_batch_update.assert_called_once()

        expected_updates = [
            {'range': 'worksheet_name!A2:A2', 'values': [['12345']]},
            {'range': 'worksheet_name!B2:B2', 'values': [['22.99']]}
        ]

        actual_updates = mock_batch_update.call_args[0][1]

        self.assertEqual(actual_updates, expected_updates)



