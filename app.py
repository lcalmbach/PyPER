import streamlit as st

#from tools import *
from config import *
from data import Dataset
from plots.piper import Piper

# https://stackoverflow.com/questions/65655712/how-to-fix-the-chromedriver-if-its-not-compatible-with-chrome-version
# from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager

# driver = webdriver.Chrome(ChromeDriverManager().install())
# driver.get("https://www.google.com/")


__version__ = '0.0.1'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2022-12-24'
MY_EMOJI = '💧'
MY_NAME = f'Fontus'
GIT_REPO = 'https://github.com/lcalmbach/Pyper'
APP_URL = 'https://lcalmbach-pyper-app-netzym.streamlit.app/'

def show_info_box():
    """
    Shows an info box the footer of the sidebar.
    """

    impressum = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
        <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
        version: {__version__} ({VERSION_DATE})<br>
        <a href="{GIT_REPO}">git-repo</a><br>
        """
    st.sidebar.markdown(impressum, unsafe_allow_html=True)


def init_layout():
    st.set_page_config(
        layout="wide",
        initial_sidebar_state = "auto", 
        page_title = MY_NAME,
        page_icon = MY_EMOJI,
    )
    with open("./style.css") as f:
        st.markdown('<style>{}</style>'.format(f.read()), unsafe_allow_html=True)

def init_settings():
    if 'data' not in st.session_state:
        st.session_state['dataset'] = Dataset()
        st.session_state['plot'] = Piper(st.session_state['dataset'])

def main():
    init_layout()
    init_settings()

    st.sidebar.markdown(f'# {MY_NAME}')
    tabs = st.tabs(['About', 'Load Data', 'Plot Settings', 'Show Plot'])
    with tabs[0]:
        st.write(ABOUT_TEXT)
    with tabs[1]:
        st.session_state['dataset'].get_user_input()
        st.session_state['plot'].dataset = st.session_state['dataset']
    with tabs[2]:
        st.session_state['plot'].get_user_input()
    with tabs[3]:
        st.session_state['plot'].show_plot()
    show_info_box()

if __name__ == '__main__':
    main()
