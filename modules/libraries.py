from .utils import clearTerminal, certChoice, saveDfToCsv, validateGUID
from .auth import getBearer
from .guiUtils import getDefaultCert, updateDefaultCert, backToMenuButton, backToMenuAction, backSession, rerun
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
    bearer = None
    while bearer is None:
        bearer = getBearer(baseUrl, customCert=customCert)
        if bearer is None:
            print('Failed to authenticate, probably due to certificate error.')
            customCert = certChoice()
    librariesDF = getLibrariesDF.cli(baseUrl=baseUrl, bearer=bearer, customCert=customCert).librariesdf
    outputName = input('\nPlease provide the name for the output CSV file: ')
    finalName = saveDfToCsv(df=librariesDF, fname=outputName)
    print(f'Saved groups with libraries to {finalName}')
    
def goTo(stage):
    st.session_state.libraryDownloads = stage

def GUIgetLibraries(baseUrl):
    
    #Initialize
    if 'libraryDownloads' not in st.session_state:
        st.session_state.libraryDownloads = 'input'
        st.session_state.certError = False

    if st.session_state.libraryDownloads == 'input':
        st.title('Welcome to get Libraries.')
        certToggle = st.toggle('Use custom cert?', 
                               value=getDefaultCert(), 
                               key='useCustomCert',
                               on_change=updateDefaultCert)
        st.session_state.customCert = certToggle
        if st.session_state.certError:
            st.error('Failed to authenticate, probably due to certificate error.')
        st.button('Download Libraries', on_click= lambda: goTo('download')) 

    elif st.session_state.libraryDownloads == 'download':
        with st.spinner("Authenticating..."):
            st.session_state.bearer = None
            while st.session_state.bearer is None:
                st.session_state.bearer = getBearer(
                baseUrl,
                customCert=st.session_state.customCert
                )
                if st.session_state.bearer is None:
                    st.session_state.certError = True
                    goTo('input')
                    rerun()
                else:
                    st.session_state.certError = False
            
        librariesDF = getLibrariesDF.gui(baseUrl=baseUrl, bearer=st.session_state.bearer, customCert=st.session_state.customCert).librariesdf
        st.session_state.file = librariesDF.to_csv().encode("utf-8")
        if st.session_state.file is not None:
            goTo('End')
            rerun()

    elif st.session_state.libraryDownloads == 'End':
        st.markdown('## The libraries list is ready:')
        st.download_button('Save file',data = st.session_state.file, file_name='Libraries.csv', mime="text/csv",icon=":material/download:",use_container_width=True)

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
        statusText = st.empty()
        for index, group in enumerate(idList):
            statusText.text(f'Patching library group... {(index + 1)} of {len(idList)}')
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
            progressBar.progress((index + 1) / len(idList))
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
        print('Extention ' + f"'{extention}'")
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
    guidValid = False
    while not guidValid:
        invalidguids = []
        invalidguidsBool = False
        for guid in idList:
            validateSingleID = validateGUID(guid)
            if not validateSingleID:
                invalidguidsBool = True
                invalidguids.append(guid)
        if invalidguidsBool:
            print('Incorrect GUIDs:')
            for guid in invalidguids:
                print(guid)
            print('GUID needs to follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format.')
            print('Please resolve issue in the CSV file')
            quit()
        else:
            guidValid = True
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
    bearer = None
    while bearer is None:
        bearer = getBearer(baseUrl, customCert=certSelect)
        if bearer is None:
            print('Failed to authenticate, probably due to certificate error.')
            certSelect = certChoice()
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

def goDelTo(stage):
    st.session_state.autoDeleteStage = stage

def GUIchangeAutoDeleteSettings(baseUrl):
        
    # Initialize input stage
    if 'autoDeleteStage' not in st.session_state:
        st.session_state.autoDeleteStage = 'input'
        st.session_state.certError = False

    # INPUT STAGE
    if st.session_state.autoDeleteStage == 'input':
        st.title('Welcome to Change auto-delete type.')
        certToggle = st.toggle('Use custom cert?', 
                               value=getDefaultCert(), 
                               key='useCustomCert',
                               on_change=updateDefaultCert)
        if st.session_state.certError:
            st.error('Failed to authenticate, probably due to certificate error.')
        file = st.file_uploader('Upload CSV file', type='csv')

        if file is None:
            disableContinueButton = True
        else:
            disableContinueButton = False
            st.session_state.groups = file
            st.session_state.customCert = certToggle
        st.button('Continue', disabled=disableContinueButton, on_click=lambda: goDelTo('ProcessCSV'))
    
    elif st.session_state.autoDeleteStage == 'ProcessCSV':
        with st.spinner('Importing...'):
            libraryGroupsDf = pd.read_csv(st.session_state.groups, index_col=0, encoding='UTF-8')
            libraryGroupsDf = libraryGroupsDf.dropna()
            idList = libraryGroupsDf['id'].tolist()
            st.session_state.idList = idList
            st.session_state.libraryGroupsDf = libraryGroupsDf
            invalidguids = []
            invalidguidsBool = False
            for guid in idList:
                validateSingleID = validateGUID(guid)
                if not validateSingleID:
                    invalidguidsBool = True
                    invalidguids.append(guid)
        if invalidguidsBool:
            st.error('Incorrect GUIDs:')
            for guid in invalidguids:
                st.write(guid)
            st.warning('GUID needs to follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format. Please resolve issue in the CSV file.')
            if st.button("Go Back to input", on_click=lambda: goDelTo('input')):
                for key in [
                    'autoDeleteStage', 'customCert', 'groups', 'bearer',
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        else:
            guidValid = True
            if len(idList) == 1:
                st.session_state.message = str(len(idList)) + ' library.'
            else:
                st.session_state.message  = str(len(idList)) + ' libraries.'
            st.session_state.numberOfGroups = len(idList)
            if st.session_state.message is not None:
                goDelTo('showRadio')
                rerun()
    
    elif st.session_state.autoDeleteStage == 'showRadio':
        
        selectMenu = ['Auto Delete all Content', 'Auto Delete unalocated content only', 'Disable autodelete']
        selectCaptions = [
            'Enables autodelete for all content in the library regardles of its allocation, one year after creation.',
            'Enables autodelete for all unallocated content in the library, one year after creation',
            'Disables automatic deletion for all content in the library.',
        ]

        selectedDelMode = st.radio(
            "Please select one of the following operations:",
            options=selectMenu,
            captions=selectCaptions,
            index=None,
            key="operationRadio"
        )
        selectedDelIndex = selectMenu.index(selectedDelMode) + 1 if selectedDelMode else None
        if selectedDelIndex is None:
            disableContinueButton2 = True
        else:
            disableContinueButton2 = False

        st.session_state.deleteModeIndex = selectedDelIndex
        st.button('Continue', disabled= disableContinueButton2, on_click= lambda: goDelTo('ConfirmAction'))
    
    elif st.session_state.autoDeleteStage == 'ConfirmAction':
        
        st.warning(f'You are about to modify settings for **{st.session_state.message}**.')
        st.write('Are you sure you want to continue?')
        confC1, confC2, confC3, confC4, confC5 = st.columns([1,1,1,1,1])
        with confC2:
            st.button('Yes, Continue.', use_container_width=True, type='primary', on_click=lambda: goDelTo('PatchSettings'))
        with confC4:
            st.button('No, cancel.', use_container_width=True, type='secondary', on_click=lambda: backSession())

    elif st.session_state.autoDeleteStage == 'PatchSettings':
        delete = deleteMode.select(int(st.session_state.deleteModeIndex))
        with st.spinner("Authenticating..."):
            st.session_state.bearer = None
            while st.session_state.bearer is None:
                st.session_state.bearer = getBearer(
                baseUrl,
                customCert=st.session_state.customCert
                )
                if st.session_state.bearer is None:
                    st.session_state.certError = True
                    goDelTo('input')
                    rerun()
                else:
                    st.session_state.certError = False
        patch = patchAutodelete.gui(baseUrl=baseUrl, 
                                duration=delete.duration, 
                                expiry=delete.expiry, 
                                deleteType=delete.deleteType, 
                                bearer=st.session_state.bearer, idList=st.session_state.idList, 
                                libraryGroupsDf=st.session_state.libraryGroupsDf,
                                customCert=st.session_state.customCert)
        st.session_state.responseError = patch.responseError
        st.session_state.errors = patch.errors
        
        if patch.responseError or not patch.responseError:
            goDelTo('Summary')
            rerun()

    elif st.session_state.autoDeleteStage == 'Summary':
        st.markdown(f'''
                    ## Finished
                    Updated delete settings for: {st.session_state.numberOfGroups} groups.
                    ''')
        if st.session_state.responseError:
            st.markdown(f'There were {len(st.session_state.errors)} erros during the API call.')
            log = ''
            for error in st.session_state.errors:
                log = log + error + '\n'
            st.download_button('Save error log', data = log, file_name="Error log.txt",mime='text/txt', icon=":material/download:")
