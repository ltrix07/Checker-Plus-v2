from tenacity import retry, stop_after_attempt, wait_fixed
import os
import requests
from db.config import TOKEN_URL, BASE_URL, MARKETPLACES
import logging
import time


def get_access_token(client_id: str, client_secret: str, refresh_token: str):
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    try:
        response = requests.post(TOKEN_URL, data=payload)
        response.raise_for_status()
        token_data = response.json()
        return token_data.get("access_token")
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении access token: {e}")
        return None


def get_resource_link(access_token: str, seller_id: str):
    link = 'https://sellingpartnerapi-na.amazon.com/definitions/2020-09-01/productTypes/PRODUCT'
    params = {
        'marketplaceIds': MARKETPLACES,
        'sellerId': seller_id,
        'requirements': 'LISTING_OFFER_ONLY',
        'locale': 'en_US'
    }
    headers = {
        'x-amz-access-token': access_token,
        'Accept': 'application/json',
        'Content_Type': 'application/json'
    }
    try:
        response = requests.get(link, params=params, headers=headers)
        response.raise_for_status()
        schema_data = response.json()
        resource_link = schema_data.get('schema', {}).get('link', {}).get('resource')
        if not resource_link:
            logging.error(f"Получены не те данные, что ожидались.\n\n{schema_data}")
            return
        return resource_link
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении resource link: {e}")


def get_shipping_ids(access_token: str, seller_id: str):
    resource_link = get_resource_link(access_token, seller_id)
    try:
        response = requests.get(resource_link)
        response.raise_for_status()
        resp_json = response.json()
        enum = resp_json.get('properties', {}).get('merchant_shipping_group', {}).get('items', {}).get('properties', {}).get('value', {}).get('enum')
        enum_names = resp_json.get('properties', {}).get('merchant_shipping_group', {}).get('items', {}).get('properties', {}).get('value', {}).get('enumNames')
        if not enum or not enum_names:
            logging.error(f"Получены не те данные, что ожидались.\n\n{resp_json}")
            return
        return dict(zip(enum_names, enum))
    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при получении shipping ids: {e}")


def create_headers(amz_creds):
    client_id = amz_creds.get('lwa_app_id')
    client_secret = amz_creds.get('lwa_client_secret')
    refresh_token = amz_creds.get('refresh_token')
    access_token = get_access_token(client_id, client_secret, refresh_token)
    if not access_token:
        raise Exception("Не удалось получить access token.")
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-amz-access-token": access_token
    }


@retry(stop=stop_after_attempt(3), wait=wait_fixed(120))
def create_feed_document(amz_creds):
    url = f"{BASE_URL}/feeds/2021-06-30/documents"
    headers = create_headers(amz_creds)
    payload = {"contentType": "application/json; charset=UTF-8"}
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(120))
def upload_to_feed_document(upload_url, json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as file:
        json_data = file.read()
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    response = requests.put(upload_url, headers=headers, data=json_data)
    response.raise_for_status()
    return response.status_code == 200


@retry(stop=stop_after_attempt(3), wait=wait_fixed(120))
def create_feed(feed_document_id, marketplace_ids: list[str], amz_creds):
    url = f"{BASE_URL}/feeds/2021-06-30/feeds"
    headers = create_headers(amz_creds)
    payload = {
        "feedType": "JSON_LISTINGS_FEED",
        "marketplaceIds": marketplace_ids,
        "inputFeedDocumentId": feed_document_id
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def get_feed_status(feed_id, amz_creds):
    url = f"{BASE_URL}/feeds/2021-06-30/feeds/{feed_id}"
    headers = create_headers(amz_creds)
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def process_file(json_file_path, marketplace_ids, amz_creds):
    if not os.path.exists(json_file_path):
        return

    try:
        feed_document = create_feed_document(amz_creds)
        feed_document_id = feed_document["feedDocumentId"]
        upload_url = feed_document["url"]
        logging.info(f"Feed Document создан: {feed_document_id}")
    except Exception as e:
        logging.error(f"Ошибка при создании Feed Document: {e}")
        return

    if not upload_to_feed_document(upload_url, json_file_path):
        logging.error("Ошибка при загрузке JSON.")
        return
    logging.info("JSON успешно загружен.")

    try:
        feed_response = create_feed(feed_document_id, marketplace_ids, amz_creds)
        feed_id = feed_response["feedId"]
        logging.info(f"Feed создан: {feed_id}")
    except Exception as e:
        logging.error(f"Ошибка при создании Feed: {e}")
        return

    while True:
        try:
            feed_status = get_feed_status(feed_id, amz_creds)
            status = feed_status.get("processingStatus", "UNKNOWN")
            logging.info(f"Текущий статус Feed: {status}")

            if status == "DONE":
                processing_end_time = feed_status.get(
                    "processingEndTime", "Время завершения отсутствует"
                )
                logging.info(f"Фид завершен. Время завершения: {processing_end_time}")
                break

            if status in ["CANCELLED", "FATAL"]:
                logging.warning(f"Обработка фида завершилась с ошибкой: {status}")
                break

            if status in ["IN_QUEUE", "IN_PROGRESS"]:
                logging.info("Фид обрабатывается, ждем...")
            else:
                logging.warning(f"Неизвестный статус: {status}")
                break

        except Exception as e:
            logging.error(f"Ошибка при проверке статуса: {e}")
            break

        time.sleep(60)
