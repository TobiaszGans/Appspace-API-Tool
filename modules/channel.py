from .auth import getBearer
from .utils import cls
import json
import requests
from tqdm import tqdm
from datetime import datetime
import pandas as pd


def getChannel(channelID, baseUrl) -> str:
    print('Authenticating...')
    bearer = getBearer(baseUrl)
    headers = {
            "authorization": bearer}
    command = f'channelplaylist/{channelID}/items'
    fullURL = baseUrl + command
    print(fullURL)
    print('Getting Channel info...')
    response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
    responseJson = json.loads(response.text)
    return responseJson

def parseChannel(channelJSON):
    data = json.loads(channelJSON)
    channelDf = pd.json_normalize(data["items"])
    return channelDf

def extractContentToDf(df) -> list:
    contentIds = df['contentId'].tolist()
    contentDisabled = df['disabled'].tolist()
    try:
        contentExpireDate = df['playoutSchedule.schedule.endDate'].tolist()
    except:
        contentExpireDate = []
        for i in range(len(contentDisabled)):
            contentExpireDate.append('None')
    newDf = pd.DataFrame(
        {
            'contentID': contentIds,
            'isDisabled': contentDisabled,
            'expiresAt': contentExpireDate
        }
    )
    newDf['expiresAt'] = newDf['expiresAt'].fillna('None')
    return newDf

def requestContent(contentID, bearer, baseUrl):
    headers = {
            "authorization": bearer}
    command = 'libraries/contents/'
    fullURL = baseUrl + command + contentID
    response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
    responseJson = json.loads(response.text)
    return responseJson

def calculateSize(IDlist, baseUrl) -> int:
    sizeList = []
    bearer = getBearer(baseUrl)
    global errorItems
    global errorNumber
    errorItems = False
    errorNumber = 0
    for i in tqdm(IDlist, desc='Downloading Content info'):
        try:
            contentData = requestContent(i,bearer)
            size = contentData['size']
            sizeList.append(size)
        except:
            errorItems = True
            errorNumber = errorNumber + 1
    totalSize = sum(sizeList)
    return totalSize

def roundResult(size:int):
    if size < 1024:
        return [size, 'Bytes']
    elif 1024 <= size < 1048576:
        calcSize = round(size/1024, 2)
        return [calcSize, 'KiB']
    elif 1048576 <= size < 1073741824:
        calcSize = round(size/1048576, 2)
        return [calcSize, 'MiB']
    else:
        calcSize = round(size/1073741824, 2)
        return [calcSize, 'GiB']

def getChannelSize(baseUrl):
    cls()
    print('Welcome to get channel size.')
    ID = input('Please provide channel ID: ')
    channel = getChannel(ID, baseUrl)
    ChannelDf = parseChannel(json.dumps(channel))
    contentDF = extractContentToDf(ChannelDf)
    global disabledContent
    global disabledNumber
    global expiredContent
    global expiredNumber
    disabledContent = False
    disabledNumber = 0
    expiredContent = False
    expiredNumber = 0
    for index, row in contentDF.iterrows():
        if row['isDisabled'] == True:
            disabledContent = True
            disabledNumber = disabledNumber + 1
        if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
            expiredContent = True
            expiredNumber = expiredNumber + 1
    if disabledContent or expiredContent:
        if disabledContent and not expiredContent:
            warnText = f'There is {disabledNumber} disabled cards in the playlist'
        elif not disabledContent and expiredContent:
            warnText = f'There is {expiredNumber} expired cards in the playlist'
        elif disabledContent and expiredContent:
            warnText = f'There is {disabledNumber} disabled cards and {expiredNumber} expired cards in the playlist'
        print('\n' + warnText)
        disabledCheck = False
        while disabledCheck is False:
            includeDisabled =  input('Do you want to include that content in the calculation? (y/n): ')
            if includeDisabled in ['y','n']:
                disabledCheck = True
            else:
                disabledCheck = False
        if includeDisabled == 'n':
            for index, row in contentDF.iterrows():
                if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
                    contentDF = contentDF.drop([index], axis = 0)
                elif row['isDisabled'] == True:
                    contentDF = contentDF.drop([index], axis = 0)
    contentIDs = contentDF['contentID'].tolist()
    totalSize = calculateSize(contentIDs, baseUrl)
    displaySize = roundResult(totalSize)
    if errorItems:
        if errorNumber == 1:
            errorString = 'was 1 element'
            errorString2 = 'This item was'
        else:
            errorString = f'were {errorNumber} elements'
            errorString2 = 'These items were'

        print(f'There {errorString} with undetermined size. {errorString2} skipped.')
    print(f'\nTotal Channel size is {displaySize[0]} {displaySize[1]}')
