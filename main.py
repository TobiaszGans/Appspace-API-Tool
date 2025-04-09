import requests
from OpenSSL import SSL, crypto
import socket
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
import json
import pandas as pd
from tqdm import tqdm
from datetime import datetime

# SSL PART START
def getPEMFile(reqUrl, port=443):
    ctx = SSL.Context(SSL.SSLv23_METHOD)
    s = socket.create_connection((reqUrl, port))
    s = SSL.Connection(ctx, s)
    s.set_connect_state()
    s.set_tlsext_host_name(str.encode(reqUrl))

    s.sendall(str.encode('HEAD / HTTP/1.0\n\n'))

    peerCertChain = s.get_peer_cert_chain()
    pemFile = ''

    for cert in peerCertChain:
        pemFile += crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8")

    return pemFile

def generate(urlAddress):
    parseUrl = urlparse(urlAddress)
    url = parseUrl.hostname
    cert = getPEMFile(url)
    with open('cert.pem', 'w') as file_object:
        file_object.writelines(cert)
# SSL End

def loadCredentials() -> list:
    load_dotenv()
    subjectID = os.getenv('subjectID')
    refreshToken = os.getenv('refreshToken')
    return [subjectID,refreshToken]

def getBearer() -> str:
    credentials = loadCredentials()
    apiUrl = baseUrl +'/authorization/token'
    authHeaders = {'Content-Type': "application/json"}
    authBody = {
        "subjectType":"Application",
        "subjectId":credentials[0],
        "grantType":"refreshToken",
        "refreshToken": credentials[1]
    }
    cert = generate(apiUrl)
    initResponse = requests.post(url = apiUrl, headers=authHeaders, json = authBody, verify= 'cert.pem')
    
    
    divideResponse = initResponse.text.split()
    bearer = "Bearer " + divideResponse[2].replace('"','')
    bearer = bearer.replace(",","")
    return bearer

def getChannel(channelID) -> str:
    print('Authenticating...')
    bearer = getBearer()
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

def requestContent(contentID, bearer):
    headers = {
            "authorization": bearer}
    command = 'libraries/contents/'
    fullURL = baseUrl + command + contentID
    response = requests.get(url=fullURL, headers=headers, verify='cert.pem')
    responseJson = json.loads(response.text)
    return responseJson

def calculateSize(IDlist) -> int:
    sizeList = []
    bearer = getBearer()
    global errorItems
    global errorNumber
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

def getChannelSize():
    os.system('cls')
    print('Welcome to get channel size.')
    ID = input('Please provide channel ID: ')
    channel = getChannel(ID)
    ChannelDf = parseChannel(json.dumps(channel))
    contentDF = extractContentToDf(ChannelDf)
    global disabledContent
    global disabledNumber
    global expiredContent
    global expiredNumber
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
    totalSize = calculateSize(contentIDs)
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

def validateDateTime(dateString):
    validation = False
    while validation is False:
        if dateString == 'now':
            dateString = datetime.now().strftime('%Y-%m-%dT%X')
        try:
            datetime.fromisoformat(dateString)
            validation = True
        except ValueError:
            dateString = input("Incorrect data format, should be YYYY-MM-DDTHH:MM:SS. Please enter the date: ")
    return dateString

def getBookingHistory():
    os.system('cls')
    print('Welcome to get booking history.')
    resourceID = input('Please enter resource ID/IDs: ')
    #resourceID = 'b541c3c9-7a8f-43b7-8e71-565e683a63ba'
    startTime = validateDateTime(input('Please enter start date and time in the following format yyyy-mm-ddThh:mm:ss: '))+'Z'
    endTime = validateDateTime(input('Please enter end time date and time in the following format yyyy-mm-ddThh:mm:ss or type now: '))+'Z'
    print('Authenticating...')
    bearer = getBearer()
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


#------------ Global Variables ------------

#Get Channel Size:
errorItems = False
errorNumber = 0
disabledContent = False
disabledNumber = 0
expiredContent = False
expiredNumber = 0

def selectScript():
    print('Welcome to the Appspace API interaction tool. Please select required script.')
    menuTxt =[
    '1. Get Channel size',
    '2. Get Booking History'
    ]
    for item in menuTxt:
        print(item)
    selection = input("\nPlease type script number: ")
    selectionVerify = False
    while not selectionVerify:
        try:
            int(selection)
            if int(selection) <= len(menuTxt) and int(selection) >= 1:
                selectionVerify = True
            else:
                selection = input("Incorrect number. Please type script number: ")
        except:
            selection = input("Incorrect input type. Please type script number: ")
    return int(selection)      

def main():
    os.system('cls')
    load_dotenv()
    subdomain = os.getenv('subdomain')
    global baseUrl
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    scriptSelection = selectScript()
    #Add selections when expanding script
    if scriptSelection == 1:
        getChannelSize()
    elif scriptSelection ==2:
        getBookingHistory()
    os.remove('./cert.pem')
main()