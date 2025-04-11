from dotenv import load_dotenv
import requests
import os

def loadCredentials() -> list:
    load_dotenv()
    subjectID = os.getenv('subjectID')
    refreshToken = os.getenv('refreshToken')
    return [subjectID,refreshToken]

def getBearer(baseUrl) -> str:
    credentials = loadCredentials()
    apiUrl = baseUrl +'/authorization/token'
    authHeaders = {'Content-Type': "application/json"}
    authBody = {
        "subjectType":"Application",
        "subjectId":credentials[0],
        "grantType":"refreshToken",
        "refreshToken": credentials[1]
    }
    initResponse = requests.post(url = apiUrl, headers=authHeaders, json = authBody, verify= 'cert.pem')
    
    
    divideResponse = initResponse.text.split()
    bearer = "Bearer " + divideResponse[2].replace('"','')
    bearer = bearer.replace(",","")
    return bearer
