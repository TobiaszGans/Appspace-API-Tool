from .utils import cls
from .auth import getBearer
import json
import pandas as pd
import requests
from tqdm import tqdm
import os

def getLibraries(baseUrl):
    cls()
    print('Welcome to get Libraries.')
    print('Authenticating...')
    bearer = getBearer(baseUrl)
    command = 'users/usergroups?limit=20&start=0&sort=Name&includeSubnetworksUserGroups=false'
    fullUrl = baseUrl + command
    headers = {
            "authorization": bearer}
    response =  json.loads(requests.get(url=fullUrl, headers=headers, verify='cert.pem').text)
    size = response["size"]
    limit = int(response["limit"])
    if size > limit:
        paging = True
        fullPages = size // limit
        reminder = size % limit
        if reminder == 0:
            pages = fullPages
        else:
            pages = fullPages + 1
        print(f'size: {size} entries ({pages} pages)')
    else:
        paging = False
    if paging:
        start = 0
        jsonList = []
        for i in tqdm(range(0, pages), desc='Downloading user groups'):
            command = f'users/usergroups?limit=20&start={start}&sort=Name&includeSubnetworksUserGroups=false'
            response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
            responseJson = json.loads(response.text)["items"]
            jsonList.extend(responseJson)
            start = start + limit
        fullJson = jsonList
    else:
        fullJson = json.loads(response.text)["items"]
    userGroupsDf = pd.json_normalize(fullJson)
    librariesDf = userGroupsDf.loc[userGroupsDf['isLibraryEnabled'] == True].reset_index()[['id', 'name']]
    outputName = input('\nPlease provide the name for the output CSV file: ')
    if outputName[-4:] != '.csv':
        outputName = outputName + '.csv'
    print(f'Saving groups with libraries to {outputName}')
    librariesDf.to_csv(outputName)

def changeAutoDeleteSettings(baseUrl):
    cls()
    print('Welcome to Change auto-delete type.')
    filePathValid = False
    while not filePathValid:
        filePath = input('Please enter the file path to your .csv file: ')
        extention = filePath[-4:]
        if extention == ".csv":
            filePathValid = os.path.isfile(filePath)
            if not filePathValid:
                print("Could not find the file.")
        else:
            print("File must be a .csv file")
    libraryGroupsDf = pd.read_csv(filePath, index_col=0, encoding='UTF-8')
    deleteMode =[
    '1. Auto Delete all Content',
    '2. Auto Delete unalocated content only',
    '3. Disable autodelete'
    ]
    for item in deleteMode:
        print(item)
    selection = input("\nPlease type script number: ")
    selectionVerify = False
    while not selectionVerify:
        try:
            int(selection)
            if int(selection) <= len(deleteMode) and int(selection) >= 1:
                selectionVerify = True
            else:
                selection = input("Incorrect number. Please type option number: ")
        except:
            selection = input("Incorrect input type. Please type option number: ")

    if selection == '1':
        deleteType = 'Any'
        expiry = True
        duration = 365
    elif selection == '2':
        deleteType = 'Unallocated'
        expiry = True
        duration =365
    elif selection == '3':
        duration =0
        deleteType = 'Undefined'
        expiry = False

    idList = libraryGroupsDf['id'].tolist()
    if len(idList) == 1:
        message = str(len(idList)) + ' library.'
    else:
        message  = str(len(idList)) + ' libraries.'
    print(f'You are about to modify settings for {message}')
    consentValid = False
    while not consentValid:
        consent = input('Are you sure you want to conitnue? (y/n): ')
        if consent == 'y':
            consentValid = True
        elif consent == 'n':
            consentValid = True
            print('Aborting.')
            quit()
        else:
            consentValid = False

    payload = {
    "isLibraryEnabled": True,
    "libraryConfiguration": {
        "contentExpiryDuration": duration,
        "contentExpiryType": deleteType,
        "isContentExpiryEnabled": expiry
        }
    }

    print('Authenticating.')
    bearer = getBearer(baseUrl)
    headers = {
            "authorization": bearer}
    errors = []
    responseError = False
    for group in tqdm(idList):
        command = f'users/usergroups/{group}'
        fullUrl = baseUrl + command
        response = requests.patch(url=fullUrl, json= payload, headers=headers, verify='cert.pem')
        if response.status_code != 200:
            responseError = True
            errorMessage = f'''
Error on patch request for group ID: {group} ({libraryGroupsDf.loc[libraryGroupsDf['id'] == group, 'name'].item()})
Error Code: {response.status_code}
Error Message: {response.text}
                '''
            errors.append(errorMessage)
    if responseError:
        print(f'There were {len(errors)} erros during the API call.')
        saveErrorsValid = False
        while not saveErrorsValid:
            saveErrors = input('Do you want to save the responses? (y/n): ')
            if saveErrors == 'y'or saveErrors == 'n':
                saveErrorsValid = True
        if saveErrors == 'y':
            with open('ErrorDump.txt', 'a', encoding='UTF-8') as file:
                for log in errors:
                    file.write(log)
                print('Saved Errors to ErrorDump.txt')