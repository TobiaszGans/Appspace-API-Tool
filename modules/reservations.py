from .utils import cls
from .auth import getBearer
from datetime import datetime
import requests
import json
import pandas as pd
from tqdm import tqdm

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

def getBookingHistory(baseUrl):
    cls()
    print('Welcome to get booking history.')
    resourceID = input('Please enter resource ID/IDs: ')
    #resourceID = 'b541c3c9-7a8f-43b7-8e71-565e683a63ba'
    startTime = validateDateTime(input('Please enter start date and time in the following format yyyy-mm-ddThh:mm:ss: '))+'Z'
    endTime = validateDateTime(input('Please enter end time date and time in the following format yyyy-mm-ddThh:mm:ss or type now: '))+'Z'
    print('Authenticating...')
    bearer = getBearer(baseUrl)
    start = 0
    headers = {
            "authorization": bearer}
    command = f'reservation/events?sort=startAt&resourceids={resourceID}&startAt={startTime}&endAt={endTime}&includesourceobject=true&page=0&start={start}'
    fullURL = baseUrl + command
    print(f'Time Range: {startTime} - {endTime}')
    print('Getting Reservation info...')

    #First request to get a total for all reservations in this
    response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
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
            response = requests.get(url= baseUrl + command, headers=headers, verify='cert.pem')
            responseJson = json.loads(response.text)
            jsonList.extend(responseJson["items"])
            start = start + limit
        fullJson = jsonList
    else:
        fullJson = json.loads(response.text)["items"]
    resourceDF = pd.json_normalize(fullJson)
    resourceDF['resourceName'] = resourceDF['resources'].apply(lambda x: x[0]['resourceName'] if x else None)
    selectColumns = ['id','reservationId','status','title','startTimeZone','startAt','endAt','createdAt','updatedAt','provider.organizer.username', 'resourceName']
    resourceDF = resourceDF[selectColumns]
    autoCancelDF = resourceDF[resourceDF['title'].str.startswith('[Room released due to no-show]')]
    if not autoCancelDF.empty:
        print('Found Auto released meetings')
        yesNoVerify = False
        while not yesNoVerify:
            saveCancels = input('Would you like to save the Auto Released data points in a separate file? (y/n): ')
            if saveCancels == 'y':
                print('Saving to AutoRelease.csv')
                autoCancelDF.to_csv('AutoRelease.csv')
                yesNoVerify = True
            elif saveCancels == 'n':
                yesNoVerify = True
    print('Saving to Output.csv')
    resourceDF.to_csv('Output.csv')