import keyboard
import psutil
import os
import json
import streamlit as st
import time

def shutdown():
    # Close streamlit browser tab
    keyboard.press_and_release('ctrl+w')
    time.sleep(100)
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

def backToMenu(label="🔙 Back to Menu", container_ratio=[3, 1], bottom_mode=False):
    cb1, cb2 = st.columns(container_ratio)
    with cb2:
        if st.button(label, use_container_width=True):
            # Clear everything but skip rerun if bottom_mode=True
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.step = 'menu'
            if bottom_mode:
                st.session_state.go_back = True  # 👈 only mark, don't rerun yet
            else:
                st.rerun()
            return True
    return False

def backToMenuAction():
    st.session_state.clear()
    st.session_state["step"] = "menu"
    st.session_state["goBack"] = False
    st.rerun()

def backSession():
    st.session_state.goBack = True

def backToMenuButton(label="🔙 Back to Menu", container_ratio=[3, 1]):
    cb1, cb2 = st.columns(container_ratio)
    with cb2:
        st.button(label, use_container_width=True, on_click=lambda: backSession())

def rerun():
    st.rerun()
