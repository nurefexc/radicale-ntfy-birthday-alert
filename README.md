# Radicale Birthday ntfy Alert

[![Docker Hub](https://img.shields.io/docker/pulls/nurefexc/radicale-ntfy-birthday-alert.svg)](https://hub.docker.com/r/nurefexc/radicale-ntfy-birthday-alert)
[![Docker Image Size](https://img.shields.io/docker/image-size/nurefexc/radicale-ntfy-birthday-alert/latest)](https://hub.docker.com/r/nurefexc/radicale-ntfy-birthday-alert)
[![Docker Image Version](https://img.shields.io/docker/v/nurefexc/radicale-ntfy-birthday-alert/latest)](https://hub.docker.com/r/nurefexc/radicale-ntfy-birthday-alert)

A lightweight Python script that monitors your Radicale CardDAV address book for birthdays and sends real-time alerts to your [ntfy](https://ntfy.sh) topic.

## Features

- **Radicale CardDAV Sync:** Automatically discovers and parses `.vcf` files from your Radicale server.
- **Smart Birthday Parsing:** Supports various birthday formats (YYYY-MM-DD, YYYYMMDD, --MMDD, etc.) and calculates age.
- **Actionable Notifications:** 
    - 📞 **One-tap Call:** Includes a "Call" button if a phone number is present in the vCard.
    - 💬 **Matrix Integration:** Direct link to Matrix chat if a Matrix ID is found in the contact notes.
- **Timezone Support:** Customizable execution window (runs daily between 00:00 and 01:00 in your local timezone).
- **Docker Ready:** Optimized for containerized deployment with minimal footprint.

## Prerequisites

1. **ntfy Topic:** Create a topic on [ntfy.sh](https://ntfy.sh) (e.g., `my_birthdays`).
2. **Radicale Server:** Access to a Radicale instance with a CardDAV address book.

## Setup & Installation

### Option 1: Using Docker (Recommended)

The easiest way to run the monitor is using the official Docker image:

1. Pull the image from Docker Hub:
   ```bash
   docker pull nurefexc/radicale-ntfy-birthday-alert:latest
   ```
2. Run the container:
   ```bash
   docker run -d \
     --name birthday-monitor \
     --restart always \
     -e RADICALE_URL=https://your-radicale-server.com/user/calendar/ \
     -e RADICALE_USER=your_username \
     -e RADICALE_PASS=your_password \
     -e NTFY_URL=https://ntfy.sh/your_topic \
     -e TZ=Europe/Budapest \
     nurefexc/radicale-ntfy-birthday-alert:latest
   ```

### Option 2: Build Locally
If you want to build the image yourself:
1. Clone this repository.
2. Build the image:
   ```bash
   docker build -t nurefexc/radicale-ntfy-birthday-alert:latest .
   ```
3. Run the container as shown in Option 1.

## CI/CD (Automation)

This repository includes a GitHub Action that automatically builds and pushes the Docker image to **Docker Hub** whenever you push to the `master` branch.

To enable this, add the following **Secrets** to your GitHub repository (`Settings > Secrets and variables > Actions`):
- `DOCKERHUB_USERNAME`: Your Docker Hub username.
- `DOCKERHUB_TOKEN`: Your Docker Hub Personal Access Token (PAT).

### Option 3: Manual Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables (see `env.sample`).
3. Run the script:
   ```bash
   python main.py
   ```

## Configuration

The following environment variables are supported:

| Variable | Description | Default |
|----------|-------------|---------|
| `RADICALE_URL` | Full URL to your Radicale address book (required) | - |
| `RADICALE_USER` | Radicale username (required) | - |
| `RADICALE_PASS` | Radicale password (required) | - |
| `NTFY_URL` | Full ntfy topic URL (required) | - |
| `NTFY_TOKEN` | ntfy authentication token (optional) | - |
| `TZ` | System timezone (e.g., `Europe/Budapest`) | `UTC` |

## How it works

The script starts and then waits for the daily execution window (00:00 - 01:00). Within this window, it performs a synchronization with the Radicale server, checks for birthdays occurring today, and sends notifications via ntfy. After execution, it sleeps until the next day.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
