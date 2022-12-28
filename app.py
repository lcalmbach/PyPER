"""
    app.py
    ------
    Fontus is a software dedicated to analyse and explore water quality data.
    It allows users to upload data and generates Piper plots. More plots are
    are planned.
    This module contains the app menu and calls the differen analysis modules.
"""
import streamlit as st

from config import ABOUT_TEXT
from project import Project
from plots.piper import Piper

__version__ = "0.0.2"
__author__ = "Lukas Calmbach"
__author_email__ = "lcalmbach@gmail.com"
VERSION_DATE = "2022-12-27"
MY_EMOJI = "💧"
MY_NAME = "Fontus"
GIT_REPO = "https://github.com/lcalmbach/Pyper"
APP_URL = "https://lcalmbach-pyper-app-netzym.streamlit.app/"
SPLASH_IMAGE = "./water-2630618-wide.jpg"


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
    """
    Sets the page configuration and loads the style.css stylesheet to addjust some
    of the default Stramlit styling.
    """

    st.set_page_config(
        layout="wide",
        initial_sidebar_state="auto",
        page_title=MY_NAME,
        page_icon=MY_EMOJI,
    )
    with open("./style.css") as f:
        st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


def init_settings():
    """
    Generates the initial project and plot instances in the sessions state to
    make it persistent.
    """
    if "data" not in st.session_state:
        st.session_state["project"] = Project()
        st.session_state["plot"] = Piper(st.session_state["project"])


def main():
    """
    Allows the user to select a tab and creates the respectives analysis type 
    instances.
    """
    init_layout()
    init_settings()

    st.sidebar.markdown(f"# {MY_NAME}")
    tabs = st.tabs(["About", "Load Data", "Plot Settings", "Show Plot"])
    with tabs[0]:
        st.image(SPLASH_IMAGE)
        st.write(ABOUT_TEXT.format(__author_email__))
    with tabs[1]:
        st.session_state["project"].get_user_input()
        st.session_state["plot"].dataset = st.session_state["project"]
    with tabs[2]:
        st.session_state["plot"].get_user_input()
    with tabs[3]:
        st.session_state["plot"].show_plot()
    show_info_box()


if __name__ == "__main__":
    main()
