from .utils import clearTerminal, certChoice, saveDfToCsv
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
        st.write(f'Time Range: {startTime} - {endTime}')
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

    @classmethod
    def process(cls, fullJson):
        resourceDF = pd.json_normalize(fullJson)
        resourceDF['resourceName'] = resourceDF['resources'].apply(lambda x: x[0]['resourceName'] if x else None)
        selectColumns = ['id','reservationId','status','title','startTimeZone','startAt','endAt','createdAt','updatedAt','provider.organizer.username', 'resourceName']
        resourceDF = resourceDF[selectColumns]
        autoCancelDF = resourceDF[resourceDF['title'].str.startswith('[Room released due to no-show]')]
        return cls(resourceDF, autoCancelDF)


def CLIgetBookingHistory(baseUrl):
    clearTerminal()
    print('Welcome to get booking history.')
    resourceID = input('Please enter resource ID/IDs: ')
    startTime = validateDateTime(input('Please enter start date and time in the following format yyyy-mm-ddThh:mm:ss: ')) + 'Z'
    endTime = validateDateTime(input('Please enter end time date and time in the following format yyyy-mm-ddThh:mm:ss or type now: ')) + 'Z'
    certMode = certChoice()
    print('Authenticating...')
    bearer = getBearer(baseUrl, customCert=certMode)
    fullJson = getBookings.cli(bearer=bearer, resourceID=resourceID, startTime=startTime, endTime=endTime, customCert=certMode, baseUrl=baseUrl).fullJson
    processed = processReservations.process(fullJson)
    
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

##### ALL TO BE CHANGED #####
def GUIgetBookingHistory(baseUrl):
    clearTerminal()
    print('Welcome to get booking history.')
    resourceID = input('Please enter resource ID/IDs: ')
    startTime = validateDateTime(input('Please enter start date and time in the following format yyyy-mm-ddThh:mm:ss: ')) + 'Z'
    endTime = validateDateTime(input('Please enter end time date and time in the following format yyyy-mm-ddThh:mm:ss or type now: ')) + 'Z'
    certMode = certChoice()
    print('Authenticating...')
    bearer = getBearer(baseUrl, customCert=certMode)
    fullJson = getBookings.cli(bearer=bearer, resourceID=resourceID, startTime=startTime, endTime=endTime, customCert=certMode, baseUrl=baseUrl).fullJson
    processed = processReservations.process(fullJson)
    
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