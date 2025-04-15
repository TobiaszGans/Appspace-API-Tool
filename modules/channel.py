from .auth import getBearer
from .utils import clearTerminal, certChoice
import json
import requests
from datetime import datetime
import pandas as pd
import streamlit as st
from dataclasses import dataclass

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

@dataclass
class sizeCalculator:
    totalSize: int
    errorItems: bool
    errorNumber: int

    @classmethod
    def CLI(cls, IDlist:str, baseUrl:str, bearer:str, customCert:bool):
        from tqdm import tqdm
        sizeList = []
        errorItems = False
        errorNumber = 0

        for i in tqdm(IDlist, desc='Downloading Content info'):
            try:
                contentData = requestContent(i, bearer, baseUrl, customCert=customCert)
                sizeList.append(int(contentData['size']))
            except:
                errorItems = True
                errorNumber += 1
        summary = sum(sizeList)
        return cls(totalSize = summary, errorItems = errorItems, errorNumber = errorNumber)
    
    @classmethod
    def GUI(cls, IDlist, baseUrl, bearer, st, customCert=False):
        sizeList = []
        errorItems = False
        errorNumber = 0
        progressBar = st.progress(0)

        for idx, i in enumerate(IDlist):
            try:
                contentData = requestContent(i, bearer, baseUrl, customCert=customCert)
                sizeList.append(contentData['size'])
            except:
                errorItems = True
                errorNumber += 1
            progressBar.progress((idx + 1) / len(IDlist))
        totalSize = sum(sizeList)
        return cls(totalSize, errorItems, errorNumber)

@dataclass
class roundResult:
    number: int
    unit: str

    @classmethod
    def calculate(cls, size:int):
        if size < 1024:
            return cls(number = size, unit ='Bytes')
        elif 1024 <= size < 1048576:
            calcSize = round(size/1024, 2)
            return cls(number = calcSize, unit ='KiB')
        elif 1048576 <= size < 1073741824:
            calcSize = round(size/1048576, 2)
            return cls(number = calcSize, unit ='MiB')
        else:
            calcSize = round(size/1073741824, 2)
            return cls(number = calcSize, unit ='GiB')

@dataclass
class disabledInfo:
    disabledContent: bool
    disabledNumber: int
    expiredContent: bool
    expiredNumber: int
    
    @classmethod
    def fromDf(cls, contentDF):
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
        return cls(disabledContent, disabledNumber, expiredContent, expiredNumber)


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

def CLIgetChannelSize(baseUrl):
    clearTerminal()
    print('Welcome to get channel size.')
    ID = input('Please provide channel ID: ')
    customCert = certChoice()
    bearer = getBearer(baseUrl, customCert=customCert)
    channel = getChannelInfo(ID, baseUrl, bearer, customCert)
    ChannelDf = parseChannel(json.dumps(channel))
    contentDF = extractContentToDf(ChannelDf)
    disabled = disabledInfo.fromDf(contentDF)
    if disabled.disabledContent or disabled.expiredContent:
        if disabled.disabledContent and not disabled.expiredContent:
            warnText = f'There is {disabled.disabledNumber} disabled cards in the playlist.'
        elif not disabled.disabledContent and disabled.expiredContent:
            warnText = f'There is {disabled.expiredNumber} expired cards in the playlist.'
        elif disabled.disabledContent and disabled.expiredContent:
            warnText = f'There is {disabled.expiredNumber} disabled cards and {disabled.expiredNumber} expired cards in the playlist.'
        print('\n' + warnText)
        disabledCheck = False
        while disabledCheck is False:
            includeDisabled = input('''Do you want to include that content in the calculation?:
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
    contentSize = sizeCalculator.CLI(contentIDs, baseUrl, bearer=bearer, customCert=customCert)
    displaySize = roundResult.calculate(contentSize.totalSize)
    if contentSize.errorItems:
        if contentSize.errorNumber == 1:
            errorString = 'was 1 element'
            errorString2 = 'This item was'
        else:
            errorString = f'were {contentSize.errorNumber} elements'
            errorString2 = 'These items were'

        print(f'There {errorString} with undetermined size. {errorString2} skipped.')
    print(f'\nTotal Channel size is {displaySize.number} {displaySize.unit}')
