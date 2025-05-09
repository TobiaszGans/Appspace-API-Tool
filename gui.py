import streamlit as st
from modules import shutdown, generateCert, GUIgetChannelSize, GUIgetBookingHistory, GUIgetLibraries, GUIchangeAutoDeleteSettings, backToMenuAction, backToMenuButton
from dotenv import load_dotenv
import os
import threading

def handleContinue(index):
    st.session_state.selectedIndex = index
    st.session_state.step = f'selected_{index}'

def main():
    load_dotenv()
    subdomain = os.getenv('subdomain')
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    apiUrl = baseUrl +'/authorization/token'
    

    st.set_page_config(
    page_title="Appspace API Tool",
    page_icon="🏠",
)
    if 'cert' not in st.session_state:
        threading.Thread(target=generateCert, args=(apiUrl,), daemon=True).start()
        st.session_state.cert = True

    if st.session_state.get("goBack"):
        backToMenuAction()

    #Shutdown Button
    c1, c2 = st.columns([3, 1])
    with c2:
        exit = st.button('Exit Application', use_container_width=True)
        if exit:
            shutdown()

    # Initialize session states       
    
    if 'step' not in st.session_state:
        st.session_state.step = 'menu'
    if 'selectedIndex' not in st.session_state:
        st.session_state.selectedIndex = None


    if st.session_state.step == 'menu':
        with c1:
            st.title('Appspace API Tool')
        st.markdown('Welcome to the Appspace API Tool.')

        st.markdown('### Select Operation')

        selectMenu = ['Get Channel Size', 'Get Booking History', 'Get Libraries', 'Change auto-delete type']
        selectCaptions = [
            'Analyze the total storage used by media items in an Appspace channel.',
            'Retrieve reservation history for one or multiple Appspace resources.',
            'Lists user groups with enabled library settings.',
            'Batch update content expiry policies for libraries based on a CSV input.'
        ]

        selectedOperation = st.radio(
            "Please select one of the following operations:",
            options=selectMenu,
            captions=selectCaptions,
            index=None,
            key="operationRadio"
        )

        selectedIndex = selectMenu.index(selectedOperation) + 1 if selectedOperation else None

        c1, c2 = st.columns([4, 1])
        with c2:
            st.button(
                'Continue',
                disabled=selectedIndex is None,
                on_click=lambda: handleContinue(selectedIndex)
            )


    if st.session_state.step.startswith('selected_'):
        selectedIndex = st.session_state.get('selectedIndex')

        if selectedIndex == 1:
            GUIgetChannelSize(baseUrl=baseUrl)
        elif selectedIndex == 2:
            GUIgetBookingHistory(baseUrl=baseUrl)
        elif selectedIndex == 3:
            GUIgetLibraries(baseUrl=baseUrl)
        elif selectedIndex == 4:
            GUIchangeAutoDeleteSettings(baseUrl=baseUrl)
        backToMenuButton()

main()