from .utils import clearTerminal, certChoice, saveDfToCsv
from .auth import getBearer
import json
import pandas as pd
import requests
from tqdm import tqdm
import os
from dataclasses import dataclass
import streamlit as st

@dataclass
class getLibrariesDF:
    librariesdf: pd.DataFrame

    @classmethod
    def cli(cls, baseUrl:str, bearer:str, customCert:bool):
        command = 'users/usergroups?limit=20&start=0&sort=Name&includeSubnetworksUserGroups=false'
        fullUrl = baseUrl + command
        headers = {
                "authorization": bearer}
        if customCert:
            response =  json.loads(requests.get(url=fullUrl, headers=headers, verify='cert.pem').text)
        else:
            response =  json.loads(requests.get(url=fullUrl, headers=headers).text)
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
                if customCert:
                    response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
                else:
                    response = requests.get(url= baseUrl + command, headers=headers)
                responseJson = json.loads(response.text)["items"]
                jsonList.extend(responseJson)
                start = start + limit
            fullJson = jsonList
        else:
            fullJson = json.loads(response.text)["items"]
        userGroupsDf = pd.json_normalize(fullJson)
        librariesDf = userGroupsDf.loc[userGroupsDf['isLibraryEnabled'] == True].reset_index()[['id', 'name']]
        return cls(librariesDf)
    
    @classmethod
    def gui(cls, baseUrl:str, bearer:str, customCert:bool):
        command = 'users/usergroups?limit=20&start=0&sort=Name&includeSubnetworksUserGroups=false'
        fullUrl = baseUrl + command
        headers = {
                "authorization": bearer}
        if customCert:
            response =  json.loads(requests.get(url=fullUrl, headers=headers, verify='cert.pem').text)
        else:
            response =  json.loads(requests.get(url=fullUrl, headers=headers).text)
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
            st.write(f'size: {size} entries ({pages} pages)')
        else:
            paging = False
        if paging:
            progressBar = st.progress(0)
            statusText = st.empty()
            start = 0
            jsonList = []
            for i in range(0, pages):
                statusText.text(f'Downloading user groups... {i + 1} of {pages}')
                command = f'users/usergroups?limit=20&start={start}&sort=Name&includeSubnetworksUserGroups=false'
                if customCert:
                    response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
                else:
                    response = requests.get(url= baseUrl + command, headers=headers)
                responseJson = json.loads(response.text)["items"]
                jsonList.extend(responseJson)
                start = start + limit
                progressBar.progress((i+1)/pages)
            fullJson = jsonList
        else:
            fullJson = json.loads(response.text)["items"]
        userGroupsDf = pd.json_normalize(fullJson)
        librariesDf = userGroupsDf.loc[userGroupsDf['isLibraryEnabled'] == True].reset_index()[['id', 'name']]
        return cls(librariesDf)

def CLIgetLibraries(baseUrl):
    clearTerminal()
    print('Welcome to get Libraries.')
    customCert = certChoice()
    print('Authenticating...')
    bearer = getBearer(baseUrl, customCert=customCert)
    librariesDF = getLibrariesDF.cli(baseUrl=baseUrl, bearer=bearer, customCert=customCert).librariesdf
    outputName = input('\nPlease provide the name for the output CSV file: ')
    finalName = saveDfToCsv(df=librariesDF, fname=outputName)
    print(f'Saved groups with libraries to {finalName}')
    
##### NOTHING CHANGED YET! #####
def GUIgetLibraries(baseUrl):
    clearTerminal()
    print('Welcome to get Libraries.')
    customCert = certChoice()
    print('Authenticating...')
    bearer = getBearer(baseUrl, customCert=customCert)
    librariesDF = getLibrariesDF.cli(baseUrl=baseUrl, bearer=bearer, customCert=customCert).librariesdf
    outputName = input('\nPlease provide the name for the output CSV file: ')
    finalName = saveDfToCsv(df=librariesDF, fname=outputName)
    print(f'Saved groups with libraries to {finalName}')

#-----Auto Delete Section-----
@dataclass
class patchAutodelete: 
    responseError: bool
    errors: list

    @classmethod
    def cli(cls, baseUrl:str, duration:int, deleteType:str, expiry:bool, bearer:str, idList:list, libraryGroupsDf:pd.DataFrame, customCert:bool):
        payload = {
        "isLibraryEnabled": True,
        "libraryConfiguration": {
            "contentExpiryDuration": duration,
            "contentExpiryType": deleteType,
            "isContentExpiryEnabled": expiry
            }
        }
        headers = {
                "authorization": bearer}
        errors = []
        responseError = False
        for group in tqdm(idList):
            command = f'users/usergroups/{group}'
            fullUrl = baseUrl + command
            if customCert:
                response = requests.patch(url=fullUrl, json= payload, headers=headers, verify='cert.pem')
            else:
                response = requests.patch(url=fullUrl, json= payload, headers=headers)
            if response.status_code != 200:
                responseError = True
                errorMessage = f'''
Error on patch request for group ID: {group} ({libraryGroupsDf.loc[libraryGroupsDf['id'] == group, 'name'].item()})
Error Code: {response.status_code}
Error Message: {response.text}
                    '''
                errors.append(errorMessage)
        return cls(responseError, errors)
    
    @classmethod
    def gui(cls, baseUrl:str, duration:int, deleteType:str, expiry:bool, bearer:str, idList:list, libraryGroupsDf:pd.DataFrame, customCert:bool):
        payload = {
        "isLibraryEnabled": True,
        "libraryConfiguration": {
            "contentExpiryDuration": duration,
            "contentExpiryType": deleteType,
            "isContentExpiryEnabled": expiry
            }
        }
        headers = {
                "authorization": bearer}
        errors = []
        responseError = False
        progressBar = st.progress(0)
        for group in idList:
            command = f'users/usergroups/{group}'
            fullUrl = baseUrl + command
            if customCert:
                response = requests.patch(url=fullUrl, json= payload, headers=headers, verify='cert.pem')
            else:
                response = requests.patch(url=fullUrl, json= payload, headers=headers)
            if response.status_code != 200:
                responseError = True
                errorMessage = f'''
Error on patch request for group ID: {group} ({libraryGroupsDf.loc[libraryGroupsDf['id'] == group, 'name'].item()})
Error Code: {response.status_code}
Error Message: {response.text}
                    '''
                errors.append(errorMessage)
            progressBar.progress((group + 1) / len(idList))
        return cls(responseError, errors)
            
@dataclass
class deleteMode:
    deleteType: str
    expiry: str
    duration: int
    
    @classmethod
    def select(cls, selection:int):
        if selection == 1:
            deleteType = 'Any'
            expiry = True
            duration = 365
        elif selection == 2:
            deleteType = 'Unallocated'
            expiry = True
            duration =365
        elif selection == 3:
            duration =0
            deleteType = 'Undefined'
            expiry = False
        return cls(deleteType, expiry, duration)

def CLIchangeAutoDeleteSettings(baseUrl):
    clearTerminal()
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
    deleteModeMenu =[
    '1. Auto Delete all Content',
    '2. Auto Delete unalocated content only',
    '3. Disable autodelete'
    ]
    for item in deleteModeMenu:
        print(item)
    selection = input("\nPlease type script number: ")
    selectionVerify = False
    while not selectionVerify:
        try:
            int(selection)
            if int(selection) <= len(deleteModeMenu) and int(selection) >= 1:
                selectionVerify = True
            else:
                selection = input("Incorrect number. Please type option number: ")
        except:
            selection = input("Incorrect input type. Please type option number: ")

    delete = deleteMode.select(int(selection))

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
    certSelect = certChoice()
    print('Authenticating.')
    bearer = getBearer(baseUrl, customCert=certSelect)
    patch = patchAutodelete.cli(baseUrl=baseUrl, 
                                duration=delete.duration, 
                                expiry=delete.expiry, 
                                deleteType=delete.deleteType, 
                                bearer=bearer, idList=idList, 
                                libraryGroupsDf=libraryGroupsDf,
                                customCert=certSelect)
    if patch.responseError:
        print(f'There were {len(patch.errors)} erros during the API call.')
        saveErrorsValid = False
        while not saveErrorsValid:
            saveErrors = input('Do you want to save the responses? (y/n): ')
            if saveErrors == 'y'or saveErrors == 'n':
                saveErrorsValid = True
        if saveErrors == 'y':
            with open('ErrorDump.txt', 'a', encoding='UTF-8') as file:
                for log in patch.errors:
                    file.write(log)
                print('Saved Errors to ErrorDump.txt')


##### NOTHING CHANGED YET! #####
def GUIchangeAutoDeleteSettings(baseUrl):
    clearTerminal()
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
    deleteModeMenu =[
    '1. Auto Delete all Content',
    '2. Auto Delete unalocated content only',
    '3. Disable autodelete'
    ]
    for item in deleteModeMenu:
        print(item)
    selection = input("\nPlease type script number: ")
    selectionVerify = False
    while not selectionVerify:
        try:
            int(selection)
            if int(selection) <= len(deleteModeMenu) and int(selection) >= 1:
                selectionVerify = True
            else:
                selection = input("Incorrect number. Please type option number: ")
        except:
            selection = input("Incorrect input type. Please type option number: ")

    delete = deleteMode.select(int(selection))

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
    certSelect = certChoice()
    print('Authenticating.')
    bearer = getBearer(baseUrl, customCert=certSelect)
    patch = patchAutodelete.cli(baseUrl=baseUrl, 
                                duration=delete.duration, 
                                expiry=delete.expiry, 
                                deleteType=delete.deleteType, 
                                bearer=bearer, idList=idList, 
                                libraryGroupsDf=libraryGroupsDf,
                                customCert=certSelect)
    if patch.responseError:
        print(f'There were {len(patch.errors)} erros during the API call.')
        saveErrorsValid = False
        while not saveErrorsValid:
            saveErrors = input('Do you want to save the responses? (y/n): ')
            if saveErrors == 'y'or saveErrors == 'n':
                saveErrorsValid = True
        if saveErrors == 'y':
            with open('ErrorDump.txt', 'a', encoding='UTF-8') as file:
                for log in patch.errors:
                    file.write(log)
                print('Saved Errors to ErrorDump.txt')