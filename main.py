from dotenv import load_dotenv
import os
from modules import generateCert, cls, getChannelSize, getBookingHistory, getLibraries, changeAutoDeleteSettings


def selectScript():
    print('Welcome to the Appspace API interaction tool. Please select required script.')
    menuTxt =[
    '1. Get Channel size',
    '2. Get Booking History',
    '3. Get libraries',
    '4. Change auto-delete type'
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
    cls()
    load_dotenv()
    subdomain = os.getenv('subdomain')
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    scriptSelection = selectScript()
    apiUrl = baseUrl +'/authorization/token'
    generateCert(apiUrl)
    #Add selections when expanding script
    if scriptSelection == 1:
        getChannelSize(baseUrl)
    elif scriptSelection == 2:
        getBookingHistory(baseUrl)
    elif scriptSelection == 3:
        getLibraries(baseUrl)
    elif scriptSelection == 4:
        changeAutoDeleteSettings(baseUrl)
    os.remove('./cert.pem')
main()