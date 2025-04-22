# 📦 Appspace API Interaction Tool

This Python script provides a command-line interface to interact with the Appspace API, offering a set of utilities to help manage and analyze content, bookings, and user group settings. It supports secure communication using SSL certificates and handles authentication via refresh tokens.

## 🔧 Features

### 1. Get Channel Size
- Analyze the total storage used by media items in an Appspace channel.
- Optionally exclude expired or disabled content from the calculation.
- Outputs the result in human-readable units (KiB, MiB, GiB).

### 2. Get Booking History
- Retrieve reservation history for one or multiple Appspace resources.
- Supports filtering by time range and detects auto-released (no-show) meetings.
- Exports all results to a csv file and optionally auto-cancels to a separate csv file.

### 3. Get Libraries
- Lists user groups with enabled library settings.
- Outputs the result to a csv file.

### 4. Change Auto-Delete Settings
- Batch update content expiry policies for libraries based on a CSV input.
- Allows setting deletion behavior for all content, only unallocated content, or disabling auto-delete.

## Preparation

To run this script you have to have Python 3.11 or higher installed.

### Create a Python Virtual Environment

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

### Install Necessary Dependencies

1. Upgrade pip:
```
py -m pip install --upgrade pip
```
2. Install dependencies:
```
pip install -r requirements.txt
```

#### Create an .env file

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

### Running the Script

1. Open the folder in the terminal.
2. Activate the virtual environment:
```
.venv\Scripts\activate
```
3. Run the script:

For command line interface use:
```
py run.py -cli
```
For a graphical interface use:
```
py run.py -gui
```
4. Follow the on-screen instructions.

> *Note: You only need to activate the environment once per terminal session.*

---

### Optional Automation

You can create a `.bat` file to automate the steps above (works on most Windows systems):

1. Create a file named `run.bat`.
2. Paste the following code:
```bat
@echo off
.venv\Scripts\activate
py run.py -gui
pause
```
or
```bat
@echo off
.venv\Scripts\activate
py run.py -cli
pause
```
3. Double-click run.bat to launch the script.