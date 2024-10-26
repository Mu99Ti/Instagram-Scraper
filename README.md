# Instagram User Data Collector

A Python script that automates the collection of Instagram user data based on hashtag searches. This tool uses Selenium WebDriver to navigate Instagram and extract usernames and profile pictures from posts.

## Features

- Automated Instagram login with session cookie management
- Hashtag-based post collection
- Username and profile picture extraction
- Rate limiting and pause mechanisms to avoid detection
- CSV export functionality
- Detailed logging system
- Headless browser operation

## Prerequisites

- Python 3.6 or higher
- Chrome browser installed
- Required Python packages (install using `pip install -r requirements.txt`):
  - selenium
  - webdriver-manager

## Installation

1. Clone this repository or download the script
2. Install the required packages:
```bash
pip install -r requirements.txt
