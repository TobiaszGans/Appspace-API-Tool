from .auth import getBearer
from .utils import cls
import json
import requests
from tqdm import tqdm
from datetime import datetime
import pandas as pd


def getChannelInfo(channelID:str, baseUrl:str, bearer:str, customCert:bool) -> str:
    headers = {
            "authorization": bearer}
    command = f'channelplaylist/{channelID}/items'
    fullURL = baseUrl + command
    if customCert:
        response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
    else:
        response = requests.get(url=fullURL, headers=headers)
    responseJson = json.loads(response.text)
    return responseJson

def parseChannel(channelJSON):
    data = json.loads(channelJSON)
    channelDf = pd.json_normalize(data["items"])
    return channelDf

def extractContentToDf(df):
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

def requestContent(contentID:str, bearer:str, baseUrl:str, customCert:bool):
    headers = {
            "authorization": bearer}
    command = 'libraries/contents/'
    fullURL = baseUrl + command + contentID
    if customCert:
        response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
    else:
        response = requests.get(url=fullURL, headers=headers)
    responseJson = json.loads(response.text)
    return responseJson

def calculateSize(IDlist, baseUrl, bearer, customCert:bool) -> list:
    sizeList = []
    global errorItems
    global errorNumber
    errorItems = False
    errorNumber = 0
    for i in tqdm(IDlist, desc='Downloading Content info'):
        try:
            contentData = requestContent(i,bearer, baseUrl, customCert=customCert)
            size = contentData['size']
            sizeList.append(size)
        except:
            errorItems = True
            errorNumber = errorNumber + 1
    totalSize = sum(sizeList)
    return [totalSize, errorItems, errorNumber]

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

def getDisabledInfo(contentDF):
    expiredNumber = 0
    disabledNumber = 0
    disabledContent = False
    expiredContent = False
    for index, row in contentDF.iterrows():
        if row['isDisabled'] == True:
            disabledContent = True
            disabledNumber = disabledNumber + 1
        if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
            expiredContent = True
            expiredNumber = expiredNumber + 1
    return [disabledContent, disabledNumber, expiredContent, expiredNumber]

def FilterIdFrame(contentDF, option:int):
    if option == 2:
        for index, row in contentDF.iterrows():
            if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
                contentDF = contentDF.drop([index], axis = 0)
            elif row['isDisabled'] == True:
                contentDF = contentDF.drop([index], axis = 0)
    elif option == 3:
        for index, row in contentDF.iterrows():
            if row['isDisabled'] == True:
                contentDF = contentDF.drop([index], axis = 0)
    elif option ==4:
        for index, row in contentDF.iterrows():
            if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
                contentDF = contentDF.drop([index], axis = 0)
    return contentDF

def getChannelSize(baseUrl):
    cls()
    print('Welcome to get channel size.')
    ID = input('Please provide channel ID: ')
    certChoiceValid = False
    while not certChoiceValid:
        certChoice = input("Use custom cert? (y/n): ")
        if certChoice == 'y':
            customCert = True
            certChoiceValid = True
        elif certChoice == 'n':
            customCert = False
            certChoiceValid = True
        else:
            certChoiceValid = False
    bearer = getBearer(baseUrl, customCert=customCert)
    channel = getChannelInfo(ID, baseUrl, bearer, customCert)
    ChannelDf = parseChannel(json.dumps(channel))
    contentDF = extractContentToDf(ChannelDf)
    disabled = getDisabledInfo(contentDF)
    if disabled[0] or disabled[2]:
        if disabled[0] and not disabled[2]:
            warnText = f'There is {disabled[1]} disabled cards in the playlist'
        elif not disabled[0] and disabled[2]:
            warnText = f'There is {disabled[3]} expired cards in the playlist'
        elif disabled[0] and disabled[2]:
            warnText = f'There is {disabled[1]} disabled cards and {disabled[3]} expired cards in the playlist'
        print('\n' + warnText)
        disabledCheck = False
        while disabledCheck is False:
            includeDisabled = input('''Do you want to include that content in the calculation?
1. Yes
2. No
3. Expired Only
4. Disabled Only
Selection: ''')
            if includeDisabled in ['1','2','3','4']:
                disabledCheck = True
            else:
                disabledCheck = False
        if includeDisabled in ['2','3','4']:
            contentDF = FilterIdFrame(contentDF=contentDF, option=int(includeDisabled))
    contentIDs = contentDF['contentID'].tolist()
    totalSize = calculateSize(contentIDs, baseUrl, bearer=bearer, customCert=customCert)
    displaySize = roundResult(totalSize[0])
    if totalSize[1]:
        if totalSize[2] == 1:
            errorString = 'was 1 element'
            errorString2 = 'This item was'
        else:
            errorString = f'were {totalSize[2]} elements'
            errorString2 = 'These items were'

        print(f'There {errorString} with undetermined size. {errorString2} skipped.')
    print(f'\nTotal Channel size is {displaySize[0]} {displaySize[1]}')
