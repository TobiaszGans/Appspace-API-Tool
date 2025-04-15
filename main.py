from dotenv import load_dotenv
import os
from modules import generateCert, clearTerminal, CLIgetChannelSize, CLIgetBookingHistory, CLIgetLibraries, CLIchangeAutoDeleteSettings


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
    clearTerminal()
    load_dotenv()
    subdomain = os.getenv('subdomain')
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    scriptSelection = selectScript()
    apiUrl = baseUrl +'/authorization/token'
    generateCert(apiUrl)
    #Add selections when expanding script
    if scriptSelection == 1:
        CLIgetChannelSize(baseUrl)
    elif scriptSelection == 2:
        CLIgetBookingHistory(baseUrl)
    elif scriptSelection == 3:
        CLIgetLibraries(baseUrl)
    elif scriptSelection == 4:
        CLIchangeAutoDeleteSettings(baseUrl)
    os.remove('./cert.pem')

if __name__ == "__main__":
    main()