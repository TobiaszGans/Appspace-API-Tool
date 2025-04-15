import streamlit as st
from modules import shutdown, GUIgetChannelSize, generateCert
from dotenv import load_dotenv
import os

def handle_continue(index):
    st.session_state.selected_index = index
    st.session_state.step = f'selected_{index}'

def main():
    load_dotenv()
    subdomain = os.getenv('subdomain')
    baseUrl = f'https://{subdomain}.cloud.appspace.com/api/v3/'
    apiUrl = baseUrl +'/authorization/token'
    generateCert(apiUrl)

    st.set_page_config(
    page_title="Appspace API Tool",
    page_icon="🏠",
)
    #Shutdown Button
    c1, c2 = st.columns([4, 1])
    with c2:
        exit = st.button('Exit Application')
        if exit:
            os.remove('./cert.pem')
            shutdown()

    if 'step' not in st.session_state:
        st.session_state.step = 'menu'

    if 'selected_index' not in st.session_state:
        st.session_state.selected_index = None
    if st.session_state.step == 'menu':
        #Text
        with c1:
            st.title('Appspace API Tool')
        st.markdown('''
            Welcome to the Appspace API Tool.
            ''')
        
        st.markdown('### Select Operation')
        #Select Function
        selectMenu = ['Get Channel Size', 'Get Booking History', 'Get Libraries', 'Change auto-delete type']
        selectCaptions = [
            'Analyze the total storage used by media items in an Appspace channel.',
            'Retrieve reservation history for one or multiple Appspace resources.',
            'Lists user groups with enabled library settings.',
            'Batch update content expiry policies for libraries based on a CSV input.'
            ]
        selectOperation = st.radio(
            "Please select one of the following operations:",
            options=selectMenu,
            captions=selectCaptions,
            index=None
        )
        selectIndex = selectMenu.index(selectOperation) + 1 if selectOperation else None
        #Proceed Button
        c1, c2 = st.columns([4, 1])
        with c2:
            st.button(
                'Continue',
                disabled=selectIndex is None,
                on_click=lambda: handle_continue(selectIndex)
            )

    if selectIndex == 1:
        GUIgetChannelSize(baseUrl=baseUrl)

    if st.button("🔙 Back to Menu"):
        st.session_state.step = 'menu'
        st.session_state.selected_index = None
main()