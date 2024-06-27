# Project Name
## ABCGovt Web scrapping
* This project focuses on creating a comprehensive tool for scraping data from various social media platforms such as Instagram, Twitter, and Facebook using Python and Django. The tool will allow users to gather and analyze social media data efficiently.
### Overview
* The Social Media Scraping Tool is designed to extract data from multiple social media platforms. This document details the module specifically for Twitter scraping, outlining the available APIs and their functionalities.

# Setup Instructions

## Installation

### Python Installation Process
Before proceeding, ensure Python is installed on your system. If not, you can download and install Python from [python.org](https://www.python.org/downloads/).



### Installing Django
Once the virtual environment is set up, you can install Django within it. Refer to the [Django documentation](https://docs.djangoproject.com/en/stable/intro/install/) for detailed instructions on installing Django.

## Getting Started

### Clone the Project
```bash
git clone https://github.com/exoticaitsolutions/ABCGovtWebscrapping.git
```

## Navigate to the Project Directory

```bash
  cd ABCGovtWebscrapping
```
### Setting up a Virtual Environment
To work with Django, it's recommended to create a virtual environment. Follow the steps outlined in the [Python documentation](https://docs.python.org/3/tutorial/venv.html) or use tools like `virtualenv` or `venv`.
Windows:
```
py -m venv myworld
```
Unix/MacOS:
```
 python3 -m venv myworld
```
Then you have to activate the environment, by typing this command:
Windows:
```
myworld\Scripts\activate.bat
```
Unix/MacOS:
```
source myworld/bin/activate
```

# Install Dependencies
### Using requirements.txt
```
pip install -r requirements.txt
```

# Individual Dependencies

***pyppeteer***
```
pip install pyppeteer
```
***Fake Useragent***
```
pip install fake-useragent
```

***Setuptools***
```
python -m pip install --upgrade pip setuptools
```
***Wbdriver Manager***
```
pip install webdriver-manager
```
***selenium-wire***
```
pip install selenium-wire
```

***python-dotenv***
```
pip install python-dotenv
```

## Environment Variables
 To run this project, you will need to add the following environment variables to your .env file
# Create .env file
in linux
```
touch .env
```
in window 
```
type nul > .env
```
## Setup .env File 
```
PAIDPROXY = FALSE
PROXY_HOST = PROXY_HOST
PROXY_PORT = PROXY_PORT
PROXY_USERNAME = PROXY_USERNAME
PROXY_PASSWORD = PROXY_PASSWORD
```
## Chromedriver
* Ensure that the version of Chromedriver matches the version of Google Chrome installed on your system for proper functionality.
# Redish
```
sudo apt install redis-server
```
```commandline
sudo apt install redis-tools
```
```commandline
redis-cli ping
```
```commandline
redis-cli
```
```commandline
redis-server
```
```commandline
pip install django-redis
```
# Run Project
**Windows:**

```bash
python manage.py runserver
```

**Unix/MacOS/LLinux:**

```bash
python3 manage.py runserver
```


