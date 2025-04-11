from dotenv import load_dotenv
import os
from modules import generateCert, cls, getChannelSize, getBookingHistory, getLibraries, changeAutoDeleteSettings
import streamlit as st


def selectScript():
    print('Welcome to the Appspace API interaction tool. Please select required script.')
    

def main():
    st.set_page_config(
        page_title="Main Page",
        page_icon="🏠",
    )
    load_dotenv()
    subdomain = os.getenv('subdomain')
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    #scriptSelection = selectScript()
    st.markdown('''
        # Main Page
        
    ''')
    apiUrl = baseUrl +'/authorization/token'
    generateCert(apiUrl)
    menu =(
    '1. Get Channel size',
    '2. Get Booking History',
    '3. Get libraries',
    '4. Change auto-delete type'
    )   
    scriptSelection = st.selectbox('Please select a script from the dropdown:', range(len(menu)), format_func=lambda x: menu[x], index=None)
    if scriptSelection is not None: scriptSelection = scriptSelection + 1
    #Add selections when expanding script
    if scriptSelection == 1:
        getChannelSize(baseUrl)
    #elif scriptSelection == 2:
    #    getBookingHistory(baseUrl)
    #elif scriptSelection == 3:
    #    getLibraries(baseUrl)
    #elif scriptSelection == 4:
    #    changeAutoDeleteSettings(baseUrl)
    os.remove('./cert.pem')

if __name__ == "__main__":
    main()