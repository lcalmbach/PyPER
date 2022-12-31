"""
    app.py
    ------
    Fontus is a software dedicated to analyse and explore water quality data.
    It allows users to upload data and generates Piper plots. More plots are
    are planned.
    This module contains the app menu and calls the differen analysis modules.
"""
import streamlit as st
from pathlib import Path
import os
from datetime import datetime
import time

from config import ABOUT_TEXT, TEMP_FOLDER
from project import Project
from plots.piper import Piper
from helper import get_base64_encoded_image


__version__ = "0.0.3"
__author__ = "Lukas Calmbach"
__author_email__ = "lcalmbach@gmail.com"
VERSION_DATE = "2022-12-31"
LICENSE = "https://github.com/lcalmbach/fontus/blob/master/LICENSE.txt"
MY_EMOJI = "💧"
MY_NAME = "Fontus"
GIT_REPO = "https://github.com/lcalmbach/fontus"
APP_URL = "https://lcalmbach-pyper-app-netzym.streamlit.app/"
SPLASH_IMAGE = "./images/water-2630618-wide.jpg"
DOCUMENTATION_LINK = "https://lcalmbach.github.io/fontus-help/"
URL_GIT_LOGO = "./images/git_logo.png"


def show_info_box():
    """
    Shows an info box the footer of the sidebar.
    """

    @st.cache
    def get_impressum():
        bin_str = get_base64_encoded_image(URL_GIT_LOGO)
        impressum = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
            <small>App created by {__author__} <a href="mailto:{__author_email__}">✉️</a><br>
            version: {__version__} ({VERSION_DATE})<br>
            <a href="{GIT_REPO}">
                <img src="data:image/png;base64,{bin_str}" style='width:20px'/>
            </a><a href="{LICENSE}">🎗️ License</a><br>
            """
        return impressum

    st.sidebar.markdown(get_impressum(), unsafe_allow_html=True)


def show_documentation_link():
    """
    Shows a link to the documentation site. The image needs to be byte-encoded.
    """

    @st.cache
    def get_html_link():
        return "<br><a href = '{}' target = '_blank'><img src='data:image/png;base64, {}' class='img-fluid' style='width:45px;height:45px;'></a><br>".format(
            DOCUMENTATION_LINK, get_base64_encoded_image("./images/documentation.png")
        )

    st.sidebar.markdown(get_html_link(), unsafe_allow_html=True)


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


def cleanup_image_files():
    now = time.mktime(datetime.now().timetuple())
    for file in Path(TEMP_FOLDER).iterdir():
        if file.is_file():
            file_timestamp = os.path.getmtime(file)
            time_since_creation_s = now - (file_timestamp / 60)
            if time_since_creation_s > 10:
                try:
                    os.remove(file)
                except:
                    pass


def init_settings():
    """
    Generates the initial project and plot instances in the sessions state to
    make it persistent.
    """
    if "data" not in st.session_state:
        st.session_state["project"] = Project()
        st.session_state["plot"] = Piper(st.session_state["project"])
        cleanup_image_files()


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
        st.session_state["plot"].show_options()
        st.session_state["plot"].show_plot()
    show_documentation_link()
    show_info_box()


if __name__ == "__main__":
    main()
