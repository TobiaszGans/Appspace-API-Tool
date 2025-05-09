from .utils import clearTerminal, certChoice, saveDfToCsv, validateGUID
from .guiUtils import updateDefaultCert, getDefaultCert, rerun
from .auth import getBearer
from datetime import datetime
import requests
import json
import pandas as pd
from tqdm import tqdm
from dataclasses import dataclass
import streamlit as st

def validateDateTime(dateString):
    validation = False
    while validation is False:
        if dateString == 'now':
            dateString = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        try:
            datetime.fromisoformat(dateString)
            validation = True
        except ValueError:
            dateString = input("Incorrect data format, should be YYYY-MM-DDTHH:MM:SS. Please enter the date: ")
    return dateString

@dataclass
class getBookings:
    fullJson: str

    @classmethod
    def cli(cls, bearer:str, resourceID:str, startTime:str, endTime:str, baseUrl, customCert:bool):
        start = 0
        headers = {
                "authorization": bearer}
        command = f'reservation/events?sort=startAt&resourceids={resourceID}&startAt={startTime}&endAt={endTime}&includesourceobject=true&page=0&start={start}'
        fullURL = baseUrl + command
        print(f'Time Range: {startTime} - {endTime}')
        print('Getting Reservation info...')

        #First request to get a total for all reservations in this
        if customCert:
            response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
        else:
            response = requests.get(url=fullURL, headers=headers)
        responseJson = json.loads(response.text)
        size = responseJson["size"]
        limit = int(responseJson["limit"])
        itmes = responseJson["items"]
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
            for i in tqdm(range(0, pages), desc='Downloading reservations'):
                command = f'/reservation/events?resourceids={resourceID}&startAt={startTime}&endAt={endTime}&start={start}'
                if customCert:
                    response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
                else:
                    response = requests.get(url= baseUrl + command, headers=headers)
                responseJson = json.loads(response.text)
                jsonList.extend(responseJson["items"])
                start = start + limit
            fullJson = jsonList
        else:
            fullJson = json.loads(response.text)["items"]
        return cls(fullJson)

    @classmethod
    def gui(cls, bearer:str, resourceID:str, startTime:str, endTime:str, baseUrl, customCert:bool):
        start = 0
        headers = {
                "authorization": bearer}
        command = f'reservation/events?sort=startAt&resourceids={resourceID}&startAt={startTime}&endAt={endTime}&includesourceobject=true&page=0&start={start}'
        fullURL = baseUrl + command
        st.write('Getting Reservation info...')

        #First request to get a total for all reservations in this
        if customCert:
            response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
        else:
            response = requests.get(url=fullURL, headers=headers)
        responseJson = json.loads(response.text)
        size = responseJson["size"]
        limit = int(responseJson["limit"])
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
            start = 0
            jsonList = []
            progressBar = st.progress(0)
            for i in range(0, pages):
                command = f'/reservation/events?resourceids={resourceID}&startAt={startTime}&endAt={endTime}&start={start}'
                if customCert:
                    response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
                else:
                    response = requests.get(url= baseUrl + command, headers=headers)
                responseJson = json.loads(response.text)
                jsonList.extend(responseJson["items"])
                start = start + limit
                progressBar.progress((i+1) / pages)
            fullJson = jsonList
        else:
            fullJson = json.loads(response.text)["items"]
        return cls(fullJson)

@dataclass
class processReservations:
    resourceDF: pd.DataFrame
    autoCancelDF: pd.DataFrame
    responseNotEmpty: bool

    @classmethod
    def process(cls, fullJson):
        resourceDF = pd.json_normalize(fullJson)
        if resourceDF.empty:
            responseNotEmpty = False
            resourceDF = pd.json_normalize([])
            autoCancelDF = pd.json_normalize([])
            return cls(resourceDF, autoCancelDF, responseNotEmpty)
        else:
            resourceDF['resourceName'] = resourceDF['resources'].apply(lambda x: x[0]['resourceName'] if x else None)
            selectColumns = ['id','reservationId','status','title','startTimeZone','startAt','endAt','createdAt','updatedAt','provider.organizer.username', 'resourceName']
            resourceDF = resourceDF[selectColumns]
            autoCancelDF = resourceDF[resourceDF['title'].str.startswith('[Room released due to no-show]')]
            responseNotEmpty = True
            return cls(resourceDF, autoCancelDF, responseNotEmpty)


def CLIgetBookingHistory(baseUrl):
    clearTerminal()
    print('Welcome to get booking history.')
    resourceIDs = input('Please enter resource ID/IDs: ')
    guidValid = False
    guidList = resourceIDs.split(',')
    while not guidValid:
        invalidguids = []
        invalidguidsBool = False
        for guid in guidList:
            validateSingleID = validateGUID(guid)
            if not validateSingleID:
                invalidguidsBool = True
                invalidguids.append(guid)
        if invalidguidsBool:
            print('Incorrect GUIDs:')
            for guid in invalidguids:
                print(guid)
            print('GUID needs to follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format.')
            resourceIDs = input('Please enter resource ID/IDs: ')
            guidList = resourceIDs.split(',')
        else:
            guidValid = True
    startTime = validateDateTime(input('Please enter start date and time in the following format yyyy-mm-ddThh:mm:ss: ')) + 'Z'
    endTime = validateDateTime(input('Please enter end time date and time in the following format yyyy-mm-ddThh:mm:ss or type now: ')) + 'Z'
    certMode = certChoice()
    print('Authenticating...')
    bearer = None
    while bearer is None:
        bearer = getBearer(baseUrl, customCert=certMode)
        if bearer is None:
            print('Failed to authenticate, probably due to certificate error.')
            certMode = certChoice()
    fullJson = getBookings.cli(bearer=bearer, resourceID=resourceIDs, startTime=startTime, endTime=endTime, customCert=certMode, baseUrl=baseUrl).fullJson
    processed = processReservations.process(fullJson)
    if not processed.responseNotEmpty:
        print('There are no items in the reservation history')
        quit()
    
    if not processed.autoCancelDF.empty:
        print('Found Auto released meetings')
        yesNoVerify = False
        while not yesNoVerify:
            saveCancels = input('Would you like to save the Auto Released data points in a separate file? (y/n): ')
            if saveCancels == 'y':
                autoOutputName = input('\nPlease provide the name for the auto-release output CSV file: ')
                autoOutputName = saveDfToCsv(df=processed.autoCancelDF, fname=autoOutputName)
                print(f'Saved reservation raport to {autoOutputName}')
                yesNoVerify = True
            elif saveCancels == 'n':
                yesNoVerify = True
    
    outputName = input('\nPlease provide the name for the full output CSV file: ')
    finalName = saveDfToCsv(df=processed.resourceDF, fname=outputName)
    print(f'Saved reservation raport to {finalName}')

def goTo(stage:str):
    st.session_state.resStage = stage

def GUIgetBookingHistory(baseUrl):
    # Initialize input stage
    if 'resStage' not in st.session_state:
        st.session_state.resStage = 'input'
        st.session_state.certError = False

    # INPUT STAGE
    if st.session_state.resStage == 'input':
        st.title('Welcome to get booking history.')
        certToggle = st.toggle('Use custom cert?', 
                               value=getDefaultCert(), 
                               key='useCustomCert',
                               on_change=updateDefaultCert)
        if st.session_state.certError:
            st.error('Failed to authenticate, probably due to certificate error.')
        resourceID = st.text_input('Please enter resource ID/IDs: ')
        st.session_state.resourceID = resourceID
        guidList = resourceID.split(',')
        invalidguids = []
        invalidguidsBool = False
        for guid in guidList:
            validateSingleID = validateGUID(guid)
            if not validateSingleID:
                invalidguidsBool = True
                invalidguids.append(guid)
        if invalidguidsBool:
            incorrectGuis = ''
            for guid in invalidguids:
                incorrectGuis = incorrectGuis + guid + ' ,'
        dates, times = st.columns([1,1])
        with dates:
            startDate = st.date_input(label= "Reservations start date")
            endDate = st.date_input(label= "Reservations end date")
        with times:
            startTime = st.time_input(label= "Reservations start time")
            endTime = st.time_input(label= "Reservations end time")
        
        startDateTime = datetime.combine(startDate, startTime)
        endDateTime = datetime.combine(endDate, endTime)
        
        if st.session_state.resourceID.strip() == "":
            st.error("Resource ID/IDs are required.")
            dissableFetchButton = True
        elif invalidguidsBool:
            st.error(f'Incorrect GUIDs: {incorrectGuis}')
            st.warning('GUID needs to follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format.')
            dissableFetchButton = True
        elif startDateTime >= endDateTime:
            st.error('Start date and time must be before the end date and time')
            dissableFetchButton = True
        else:
            dissableFetchButton = False
        startDateTimeStr = datetime.strftime(startDateTime,'%Y-%m-%dT%H:%M:%SZ')
        endDateTimeStr = datetime.strftime(endDateTime,'%Y-%m-%dT%H:%M:%SZ')
        st.session_state.startDateTime = startDateTimeStr
        st.session_state.endDateTime = endDateTimeStr
        st.session_state.customCert = certToggle
        

        st.button('Fetch reservations', disabled=dissableFetchButton, on_click= lambda: goTo('download'))
    
    #Download Stage
    elif st.session_state.resStage == 'download':
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
        fullJson = getBookings.gui(bearer=st.session_state.bearer, resourceID=st.session_state.resourceID, startTime=st.session_state.startDateTime, endTime=st.session_state.endDateTime, customCert=st.session_state.customCert, baseUrl=baseUrl).fullJson
        processed = processReservations.process(fullJson)
        if not processed.responseNotEmpty:
            st.error('There are no items in the reservation history.')
            if st.button("Go Back to input", on_click=lambda: goTo('input')):
                for key in [
                    'resStage', 'customCert', 'resourceID', 'bearer',
                    'contentDf'
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        elif not processed.autoCancelDF.empty:
            st.session_state.autorelease = processed.autoCancelDF
            st.session_state.reservations = processed.resourceDF
            st.session_state.resStage = 'autorelease'
            st.rerun()
        else:
            st.session_state.reservations = processed.resourceDF
            st.session_state.resStage = 'saveFiles'
            st.rerun()

    elif st.session_state.resStage == 'autorelease':
        st.success('Found Auto released meetings')
        st.markdown('Would you like to save the Auto Released data points in a separate file?')
        Autoreleasefile = st.session_state.autorelease.to_csv().encode("utf-8")
        downCol1, downCol2, downCol3, downCol4 ,downCol5 = st.columns([1,1,1,1,1])
        with downCol2:
            if st.download_button('Save file',data = Autoreleasefile, file_name='AutoRelease.csv', mime="text/csv",icon=":material/download:",use_container_width=True):
                st.session_state.resStage = 'saveFiles'
                st.rerun()
        with downCol4:
            if st.button('Skip',use_container_width=True):
                st.session_state.resStage = 'saveFiles'
                st.rerun()

    elif st.session_state.resStage == 'saveFiles':
        st.markdown('''
                    ### Your Raport Is Ready
                    Press the bellow button to save the file.
        ''')
        fullRaport = st.session_state.reservations.to_csv().encode("utf-8")
        st.download_button('Save file',data = fullRaport, file_name='Reservations.csv', mime="text/csv",icon=":material/download:",use_container_width=True)
