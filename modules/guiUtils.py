import keyboard
import psutil
import os
import json
import streamlit as st

def shutdown():
    # Close streamlit browser tab
    keyboard.press_and_release('ctrl+w')
    # Terminate streamlit python process
    pid = os.getpid()
    p = psutil.Process(pid)
    p.terminate()

def getDefaultCert():
    try:
        with open('./modules/preferences.json', 'r', encoding='UTF-8') as file:
            fullString = json.load(file)
            state = fullString.get("CustomCert")
            return state
    except:
        print("Except")
        return False
    
def updateDefaultCert():
    currentCertSetting = st.session_state.useCustomCert
    with open('./modules/preferences.json', 'w', encoding='UTF-8') as file:
        Key = {"CustomCert": currentCertSetting}
        json.dump(Key, file)

#def saveDefaultCert(certState):
    
