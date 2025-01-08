import time
import requests
import logging
from sp_api.base import Marketplaces, SellingApiForbiddenException
from sp_api.base.reportTypes import ReportType
from sp_api.api import Feeds


class AmazonAPI:
    def __init__(self, creds: dict):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__class__.__name__)

        self.creds = creds
        self.lwa_app_id = creds.get('lwa_app_id')
        self.lwa_client_secret = creds.get('lwa_client_secret')
        self.refresh_token = creds.get('refresh_token')

    def _refresh_access_token(self, retries=5, delay=5):
        url = 'https://api.amazon.com/auth/o2/token'
        payload = {
            'grant_type': 'refresh_token',
            'client_id': self.lwa_app_id,
            'client_secret': self.lwa_client_secret,
            'refresh_token': self.refresh_token
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        for _ in range(retries):
            try:
                response = requests.get(url, data=payload, headers=headers)
                if response.status_code == 200:
                    tokens = response.json()
                    return tokens['access_token']
                else:
                    return None
            except (ConnectionError, TimeoutError) as e:
                print(f'Connection failed: {e}')
                time.sleep(delay)

    def upload_to_amz(self, file_path: str):
        new_token = self._refresh_access_token()
        try:
            res = Feeds(credentials=self.creds, marketplace=Marketplaces.US, restricted_data_token=new_token)
            with open(file_path, 'rb') as file:
                create_file = res.create_feed_document(file=file,
                                                       content_type='text/tab-separated-values; charset=UTF-8')

            url = create_file.payload.get('url')
            feed_doc_id = create_file.payload.get('feedDocumentId')

            with open(file_path, 'rb') as file:
                requests.put(url, data=file.read())

            res.create_feed(ReportType.POST_FLAT_FILE_INVLOADER_DATA, feed_doc_id)

            return {
                'status': 'success',
                'feed_document_id': feed_doc_id,
                'url': url
            }
        except SellingApiForbiddenException:
            self.logger.error('Not valid key for Amazon API')
        except Exception as e:
            self.logger.error(e)
