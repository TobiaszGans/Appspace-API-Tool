from .auth import getBearer
from .utils import clearTerminal, certChoice, validateGUID
from .guiUtils import updateDefaultCert, getDefaultCert, rerun
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
    def CLI(cls, IDlist:list, baseUrl:str, bearer:str, customCert:bool):
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
    def GUI(cls, IDlist, baseUrl, bearer, customCert=False):
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
    number: float
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
    validGuid = False
    while not validGuid:
        validGuid = validateGUID(ID)
        if not validGuid:
            ID = input('Incorrect format. GUID should follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format: ')
    customCert = certChoice()
    bearer = None
    while bearer is None:
        bearer = getBearer(baseUrl, customCert=customCert)
        if bearer is None:
            print('Failed to authenticate, probably due to certificate error.')
            customCert = certChoice()
    channel = getChannelInfo(ID, baseUrl, bearer, customCert)
    channelDf = parseChannel(json.dumps(channel))
    if channelDf.empty:
        print('There is no content in the selected channel')
        quit()
    contentDF = extractContentToDf(channelDf)
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

def goTo(stage:str):
    st.session_state.channelStage = stage

def GUIgetChannelSize(baseUrl):
    #initialize input stage
    if 'channelStage' not in st.session_state:
        st.session_state.channelStage = 'input'
        st.session_state.certError = False

    # INPUT STAGE
    if st.session_state.channelStage == 'input':
        st.title('Welcome to get channel size.')
        certToggle = st.toggle('Use custom cert?', 
                               value=getDefaultCert(), 
                               key='useCustomCert',
                               on_change=updateDefaultCert)
        if st.session_state.certError:
            st.error('Failed to authenticate, probably due to certificate error.')
        channelID = st.text_input('Please provide channel ID: ')
        st.session_state.channelID = channelID.strip()
        guidvalid = validateGUID(channelID)
        if st.session_state.channelID == "":
            st.error("Channel ID is required.")
            disableButton = True
        elif not guidvalid:
            st.error("GUID needs to follow xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx format.")
            disableButton = True
        else:
            disableButton = False
        st.session_state.customCert = certToggle
        st.button('Get channel Size', on_click=lambda: goTo('fetch'), disabled=disableButton)
    
    # FETCH STAGE
    elif st.session_state.channelStage == 'fetch':
        if 'fetchDone' not in st.session_state:
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
            with st.spinner("Getting channel info..."):
                rawChannel = getChannelInfo(
                    st.session_state.channelID,
                    baseUrl,
                    st.session_state.bearer,
                    st.session_state.customCert
                )
                channelDf = parseChannel(json.dumps(rawChannel))
                if channelDf.empty:
                    st.error('There is no content in the selected channel')
                    if st.button("Calculate another channel", on_click=lambda: goTo('input')):
                        for key in [
                            'channelStage', 'customCert', 'channelID', 'bearer',
                            'contentDf', 'disabledInfo', 'filterOption', 'sizeResult'
                        ]:
                            if key in st.session_state:
                                del st.session_state[key]
                            st.rerun()
                else:
                    contentDf = extractContentToDf(channelDf)
                    st.session_state.contentDf = contentDf

                    st.session_state.disabledInfo = disabledInfo.fromDf(contentDf)

                    st.session_state.fetchDone = True
                    st.rerun()

        else:
            d = st.session_state.disabledInfo
            if d.disabledContent or d.expiredContent:
                st.session_state.channelStage = 'filter'
            else:
                st.session_state.channelStage = 'calculate'
            del st.session_state.fetchDone
            st.rerun()
    
    # FILTER STAGE
    elif st.session_state.channelStage == 'filter':
        d = st.session_state.disabledInfo
        warnLines = []
        if d.disabledContent:
            warnLines.append(f"- {d.disabledNumber} disabled cards")
        if d.expiredContent:
            warnLines.append(f"- {d.expiredNumber} expired cards")

        st.warning("Content warning:\n" + "\n".join(warnLines))

        option = st.selectbox(
            "Do you want to include that content in the calculation?",
            options=[
                (None, "-- Select an option --"),
                ("1", "Yes (Include all cards)"),
                ("2", "No (Exclude disabled and expired cards)"),
                ("3", "Expired only (Include active and expired cards)"),
                ("4", "Disabled only (Include active and disabled cards)")
            ],
            format_func=lambda x: x[1],
            index=0
        )
        if option[0] is None:
            disableButton2 = True
        else:
            disableButton2 = False
        if st.button("Continue to size calculation", disabled= disableButton2):
            optInt = option[0]
            st.session_state.filterOption = optInt

            if optInt in [2, 3, 4]:
                st.session_state.contentDf = FilterIdFrame(
                    contentDF=st.session_state.contentDf,
                    option=optInt
                )
            st.session_state.channelStage = 'calculate'
            st.rerun()
    
    # CALCULATE STAGE
    elif st.session_state.channelStage == 'calculate':
        st.subheader("Calculating total size...")

        contentIDs = st.session_state.contentDf['contentID'].tolist()
        sizeResult = sizeCalculator.GUI(
            contentIDs,
            baseUrl,
            bearer=st.session_state.bearer,
            customCert=st.session_state.customCert
        )
        st.session_state.sizeResult = sizeResult

        displaySize = roundResult.calculate(sizeResult.totalSize)
        if sizeResult.errorItems:
            errNum = sizeResult.errorNumber
            itemStr = "item was" if errNum == 1 else "items were"
            st.warning(f"There were {errNum} elements with undetermined size. These {itemStr} skipped.")

        st.success(f"Total Channel size is {displaySize.number} {displaySize.unit}")

        if st.button("Calculate another channel", on_click=lambda: goTo('input')):
            for key in [
                'channelStage', 'customCert', 'channelID', 'bearer',
                'contentDf', 'disabledInfo', 'filterOption', 'sizeResult'
            ]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()