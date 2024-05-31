import os
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
SHOP_NAME = os.getenv('SHOP_NAME')
API_VERSION = os.getenv('API_VERSION')
ADMIN_API_ACCESS_TOKEN = os.getenv('ADMIN_API_ACCESS_TOKEN')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
SLACK_CHANNEL_ID = os.getenv('SLACK_CHANNEL_ID')

# Define Google Sheets API scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def fetch_shopify_data(date):
    """
    Fetch orders data from Shopify API for a given date.
    """
    url = f'https://{SHOP_NAME}.myshopify.com/admin/api/{API_VERSION}/orders.json'
    headers = {
        'X-Shopify-Access-Token': ADMIN_API_ACCESS_TOKEN
    }
    params = {
        'created_at_min': date.isoformat(),
        'created_at_max': (date + timedelta(days=1)).isoformat(),
        'status': 'any'
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def calculate_differences(current, previous):
    """
    Calculate percentage differences between current and previous values.
    """
    if previous == 0:
        return 'N/A'
    return (current - previous) / previous * 100

def get_google_credentials():
    """
    Get Google credentials from environment variables or Application Default Credentials.
    """
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        return None  # ADC will be used
    else:
        info = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key_id": os.getenv('GOOGLE_PRIVATE_KEY_ID'),
            "private_key": os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n'),
            "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
            "client_id": os.getenv('GOOGLE_CLIENT_ID'),
            "auth_uri": os.getenv('GOOGLE_AUTH_URI'),
            "token_uri": os.getenv('GOOGLE_TOKEN_URI'),
            "auth_provider_x509_cert_url": os.getenv('GOOGLE_AUTH_PROVIDER_X509_CERT_URL'),
            "client_x509_cert_url": os.getenv('GOOGLE_CLIENT_X509_CERT_URL')
        }
        return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)

def create_sheet_if_not_exists(service, spreadsheet_id, sheet_title):
    """
    Create a new sheet in the Google Sheets document if it doesn't already exist.
    """
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    sheet_names = [sheet['properties']['title'] for sheet in sheets]

    if sheet_title in sheet_names:
        return

    body = {
        'requests': [{
            'addSheet': {
                'properties': {
                    'title': sheet_title
                }
            }
        }]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()

def append_to_google_sheet(data, sheet_title):
    """
    Append data to a Google Sheet, and format the header row to be bold.
    """
    credentials = get_google_credentials()
    service = build('sheets', 'v4', credentials=credentials)

    create_sheet_if_not_exists(service, GOOGLE_SHEET_ID, sheet_title)

    # Clear the existing data if any
    service.spreadsheets().values().clear(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f'{sheet_title}!A1:Z1000'
    ).execute()

    body = {
        'values': data
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f'{sheet_title}!A1',
        valueInputOption='RAW',
        body=body
    ).execute()
    print(f"{result.get('updatedCells')} cells updated.")

    # Format the header row to be bold
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": get_sheet_id(service, GOOGLE_SHEET_ID, sheet_title),
                    "startRowIndex": 0,
                    "endRowIndex": 1
                },
                "cell": {
                    "userEnteredFormat": {
                        "textFormat": {
                            "bold": True
                        }
                    }
                },
                "fields": "userEnteredFormat.textFormat.bold"
            }
        }
    ]

    body = {
        'requests': requests
    }
    service.spreadsheets().batchUpdate(spreadsheetId=GOOGLE_SHEET_ID, body=body).execute()

def get_sheet_id(service, spreadsheet_id, sheet_title):
    """
    Get the sheet ID for a given sheet title.
    """
    spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheets = spreadsheet.get('sheets', [])
    for sheet in sheets:
        if sheet['properties']['title'] == sheet_title:
            return sheet['properties']['sheetId']
    return None

def send_to_slack(message, file_path=None):
    """
    Send a message to a Slack channel.
    """
    client = WebClient(token=SLACK_API_TOKEN)
    try:
        if file_path:
            response = client.files_upload(
                channels=SLACK_CHANNEL_ID,
                file=file_path,
                initial_comment=message
            )
        else:
            response = client.chat_postMessage(
                channel=SLACK_CHANNEL_ID,
                text=message
            )
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

def get_previous_month_same_day(date):
    """
    Get the same day of the previous month, adjusting if necessary.
    """
    previous_month = date - relativedelta(months=1)
    while True:
        try:
            return date.replace(month=previous_month.month, day=date.day)
        except ValueError:
            # If the day is out of range for the previous month, adjust by subtracting one day
            date = date - timedelta(days=1)

def main():
    current_date = datetime.now()
    dates = [
        current_date,
        current_date - timedelta(days=1),
        get_previous_month_same_day(current_date)
    ]

    all_data = [['Date', 'Total Orders', 'Total Orders % Diff', 'Total Revenue', 'Total Revenue % Diff',
                 'Total Sessions', 'Total Sessions % Diff', 'Conversion Rate', 'Conversion Rate % Diff',
                 'Average Order Value', 'AOV % Diff']]

    previous_data = None

    for date in dates:
        shopify_data = fetch_shopify_data(date)
        orders = shopify_data.get('orders', [])
        total_orders = len(orders)
        total_revenue = sum(float(order['total_price']) for order in orders)
        total_sessions = 1000  # Example static value, replace with actual logic if available
        conversion_rate = total_orders / total_sessions if total_sessions else 0
        average_order_value = total_revenue / total_orders if total_orders else 0

        if previous_data:
            orders_diff = calculate_differences(total_orders, previous_data['total_orders'])
            revenue_diff = calculate_differences(total_revenue, previous_data['total_revenue'])
            sessions_diff = calculate_differences(total_sessions, previous_data['total_sessions'])
            conversion_rate_diff = calculate_differences(conversion_rate, previous_data['conversion_rate'])
            aov_diff = calculate_differences(average_order_value, previous_data['average_order_value'])
        else:
            orders_diff = 'N/A'
            revenue_diff = 'N/A'
            sessions_diff = 'N/A'
            conversion_rate_diff = 'N/A'
            aov_diff = 'N/A'

        all_data.append([
            date.strftime('%Y-%m-%d'),
            total_orders, orders_diff,
            total_revenue, revenue_diff,
            total_sessions, sessions_diff,
            conversion_rate, conversion_rate_diff,
            average_order_value, aov_diff
        ])

        previous_data = {
            'total_orders': total_orders,
            'total_revenue': total_revenue,
            'total_sessions': total_sessions,
            'conversion_rate': conversion_rate,
            'average_order_value': average_order_value
        }

    sheet_title = current_date.strftime('%Y-%m-%d')
    append_to_google_sheet(all_data, sheet_title)
    send_to_slack(f"Shopify data has been updated. Check the Google Sheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")

if __name__ == "__main__":
    main()
