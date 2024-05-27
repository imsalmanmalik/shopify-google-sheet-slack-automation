# Shopify Data Automation

This project automates the fetching of Shopify data, appending it to a Google Sheet, and sending notifications to a Slack channel.

## Features

- Fetch orders data from Shopify API.
- Calculate differences between current and previous values.
- Append data to a Google Sheet and format headers.
- Send notifications to a Slack channel.

## Setup

### Prerequisites

- Python 3.8 or higher
- Docker
- A Google Cloud project with Google Sheets API enabled.
- A Slack workspace and API token.

### Environment Variables

You need to set the following environment variables. These will be configured as secrets in GitHub Actions:

- `SHOP_NAME`: Your Shopify store name.
- `API_VERSION`: The version of the Shopify API you are using.
- `ADMIN_API_ACCESS_TOKEN`: Your Shopify Admin API access token.
- `GOOGLE_SHEET_ID`: The ID of the Google Sheet you want to update.
- `SLACK_API_TOKEN`: Your Slack API token.
- `SLACK_CHANNEL_ID`: The Slack channel ID where notifications will be sent.
- `GOOGLE_PROJECT_ID`: Your Google Cloud project ID.
- `GOOGLE_PRIVATE_KEY_ID`: Your Google private key ID.
- `GOOGLE_PRIVATE_KEY`: Your Google private key (ensure newline characters are replaced by `\n`).
- `GOOGLE_CLIENT_EMAIL`: Your Google client email.
- `GOOGLE_CLIENT_ID`: Your Google client ID.
- `GOOGLE_AUTH_URI`: The Google auth URI.
- `GOOGLE_TOKEN_URI`: The Google token URI.
- `GOOGLE_AUTH_PROVIDER_X509_CERT_URL`: The Google auth provider x509 cert URL.
- `GOOGLE_CLIENT_X509_CERT_URL`: The Google client x509 cert URL.
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions.

### Local Development

1. **Install Dependencies**

    ```sh
    pip3 install -r requirements.txt
    ```

2. **Run the Script**

    ```sh
    python3 fetch_shopify_data.py
    ```

### Using `requirements.in`

If you want to use `requirements.in` to manage your dependencies, you can generate a `requirements.txt` file using `pip-compile`. This is useful for repeatable builds and to have more control over the updates.

1. **Install `pip-tools`**

    ```sh
    pip install pip-tools
    ```

2. **Generate `requirements.txt` from `requirements.in`**

    ```sh
    pip-compile --output-file=requirements.txt requirements.in
    ```


### Docker

1. **Build the Docker Image**

    ```sh
    docker build -t shopify-automation:latest .
    ```

2. **Run the Docker Container**

    ```sh
    docker run --rm \
        -e SHOP_NAME=your_shop_name \
        -e API_VERSION=your_api_version \
        -e ADMIN_API_ACCESS_TOKEN=your_admin_api_access_token \
        -e GOOGLE_SHEET_ID=your_google_sheet_id \
        -e SLACK_API_TOKEN=your_slack_api_token \
        -e SLACK_CHANNEL_ID=your_slack_channel_id \
        -e GOOGLE_PROJECT_ID=your_google_project_id \
        -e GOOGLE_PRIVATE_KEY_ID=your_google_private_key_id \
        -e GOOGLE_PRIVATE_KEY="your_google_private_key" \
        -e GOOGLE_CLIENT_EMAIL=your_google_client_email \
        -e GOOGLE_CLIENT_ID=your_google_client_id \
        -e GOOGLE_AUTH_URI=your_google_auth_uri \
        -e GOOGLE_TOKEN_URI=your_google_token_uri \
        -e GOOGLE_AUTH_PROVIDER_X509_CERT_URL=your_google_auth_provider_x509_cert_url \
        -e GOOGLE_CLIENT_X509_CERT_URL=your_google_client_x509_cert_url \
        shopify-automation:latest
    ```

### GitHub Actions

This project includes two GitHub Actions workflows:

1. **CI/CD Pipeline**: Builds the Docker image, scans it for vulnerabilities, fails the build if HIGH or CRITICAL vulnerabilities are found, and pushes the Docker image to GitHub Container Registry (GHCR).
2. **Scheduled Task**: Runs the Docker image every midnight to update the Google Sheet and send a Slack notification.

## CI/CD Pipeline

![CI/CD Pipeline](/images/ci-cd.png)

## Scheduled Task

![Scheduled Task](/images/schedule.png)


