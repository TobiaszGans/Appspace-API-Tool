from .auth import getBearer
from .utils import cls
import json
import requests
from tqdm import tqdm
from datetime import datetime
import pandas as pd
import streamlit as st


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
    st.write('Welcome to get channel size.')
    ID = st.text_input('Please provide channel ID: ')
    proceed = st.button('Submit')
    if proceed:
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
                includeMenu = ["Yes","No"]
                includeOptions =["Will include all enabled and disabled card in the calculation", 
                                 "Will only calculate channel size based on enabled cards"]
            elif not disabledContent and expiredContent:
                warnText = f'There is {expiredNumber} expired cards in the playlist'
                includeMenu = ["Yes","No"]
                includeOptions =["Will include all enabled and expired card in the calculation", 
                                 "Will only calculate channel size based on enabled cards"]
            elif disabledContent and expiredContent:
                warnText = f'There is {disabledNumber} disabled cards and {expiredNumber} expired cards in the playlist'
                includeMenu = ["Yes","No", "Expired Only", "Disabled Only"]
                includeOptions =["Will include all enabled and expired card in the calculation", 
                                 "Will only calculate channel size based on enabled cards", 
                                 "Will include all enabled and expired card in the calculation",
                                 "Will include all enabled and disabled card in the calculation"]
            st.write('\n' + warnText)
            
            includeCheck = st.radio(
                "Do you want to include that content in the calculation?",
                options= includeMenu,
                captions= includeOptions,
                index=None
            )
            if includeCheck == None:
                lockProceed = True
            if st.button("Continue", disabled=lockProceed):
                if includeCheck == "No":
                    for index, row in contentDF.iterrows():
                        if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
                            contentDF = contentDF.drop([index], axis = 0)
                        elif row['isDisabled'] == True:
                            contentDF = contentDF.drop([index], axis = 0)
                elif includeCheck == "Expired Only":
                    for index, row in contentDF.iterrows():
                        if row['isDisabled'] == True:
                            contentDF = contentDF.drop([index], axis = 0)
                elif includeCheck == "Disabled Only":
                    for index, row in contentDF.iterrows():
                        if not row['expiresAt'] == 'None' and datetime.strptime(row['expiresAt'], '%Y-%m-%dT%XZ') < datetime.now():
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

                    st.write(f'There {errorString} with undetermined size. {errorString2} skipped.')
                st.write(f'\nTotal Channel size is {displaySize[0]} {displaySize[1]}')
