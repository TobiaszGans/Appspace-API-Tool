# Preparation

To run this script you have to have Python 3.11 or higher installed.

## Create a Python Virtual Environment

It's recommended to use a separate virtual environment for this script, as it has several dependencies. Installing them globally may cause conflicts with other scripts.

*This guide assumes you're using Windows.*

1. Open the folder containing the script in your terminal.
2. Run the following command to create a virtual environment:

```
py -m venv .venv
```
3. Activate the environment using:
```
.venv\Scripts\activate
```

## Install Necessary Dependencies

1. Upgrade pip:
```
py -m pip install --upgrade pip
```
2. Install dependencies:
```
pip install -r requirements.txt
```

### Create an .env file

In the root folder of the project, create a file named `.env` with the following contents:
```
subjectID = "<Your Appspace Subject ID>"
refreshToken = "<Your Appspace Refresh Token>"
subdomain = "<Your private cloud subdomain>"
```
- `subdomain` refers to the part **before** `.cloud.appspace.com`, e.g., if your URL is  
  `https://acme.cloud.appspace.com`, then your subdomain is `acme`.

- If you're using Appspace's **public cloud**, use:
```
subdomain = "api"
```

---

## Running the Script

1. Open the folder in the terminal.
2. Activate the virtual environment:
```
.venv\Scripts\activate
```
3. Run the script:
```
py main.py
```
4. Follow the on-screen instructions.

> *Note: You only need to activate the environment once per terminal session.*

---

## Optional Automation

You can create a `.bat` file to automate the steps above (works on most Windows systems):

1. Create a file named `run.bat`.
2. Paste the following code:
```bat
@echo off
.venv\Scripts\activate
py main.py
pause
```
3. Double-click run.bat to launch the script.