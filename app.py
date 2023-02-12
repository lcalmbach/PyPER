"""
    app.py
    ------
    Fontus is a software dedicated to analyse and explore water quality data.
    It allows users to upload data and generates Piper plots. More plots are
    are planned.
    This module contains the app menu and calls the differen analysis modules.
"""
import streamlit as st
from streamlit_option_menu import option_menu
from pathlib import Path
import os
from datetime import datetime
import time

from config import ABOUT_TEXT, TEMP_FOLDER, CalculatorsEnum
from project import Project, AnalysisEnum
from plots.piper import Piper
from plots.map import Map
from calculators.formula_weight import FormulaWeightConversion, FormulaWeightCalculator
from calculators.sar_calculator import IrrigationWaterQuality
from calculators.saturation_index import SaturationIndex
from analysis.mann_kendall import MannKendall
from helper import get_base64_encoded_image, load_css


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
    Shows an info box in the footer section of the sidebar.
    """

    @st.cache
    def get_impressum() -> str:
        bin_str = get_base64_encoded_image(URL_GIT_LOGO)
        impressum = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
            <small>App created by {__author__} <a href="mailto:{__author_email__}">✉️</a><br>
            version: {__version__} ({VERSION_DATE})<br>
            <a href="{GIT_REPO}">
                <img src="data:image/png;base64,{bin_str}" style='width:25px'/>
            </a><a href="{LICENSE}">🎗️ License</a><br>
            Current dataset: {st.session_state['project'].source_file}
            """
        return impressum

    st.sidebar.markdown(get_impressum(), unsafe_allow_html=True)


def show_documentation_link():
    """
    Shows a link to the documentation site. The image needs to be byte-encoded.
    """

    @st.cache
    def get_html_link() -> str:
        html_link = "<br><a href = '{}' target = '_blank'><img src='data:image/png;base64, {}' class='img-fluid' style='width:45px;height:45px;'></a><br>".format(
            DOCUMENTATION_LINK, get_base64_encoded_image("./images/documentation.png")
        )
        return html_link

    st.sidebar.markdown(get_html_link(), unsafe_allow_html=True)


def init_layout():
    """
    Sets the page configuration and loads the style.css stylesheet to adjust some
    of the default Stramlit styling.
    """

    st.set_page_config(
        layout="wide",
        initial_sidebar_state="auto",
        page_title=MY_NAME,
        page_icon=MY_EMOJI,
    )
    load_css("./style.css")


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


def init_project():
    """
    Generates the initial project and plot instances in the sessions state to
    make it persistent.
    """
    if "project" not in st.session_state:
        st.session_state["project"] = Project()
        cleanup_image_files()


def handle_plots():
    plot_dict = st.session_state["project"].plot_options_dict
    if plot_dict:
        plot_name = st.sidebar.selectbox(
            label="Select a Plot",
            options=list(plot_dict.keys()),
            format_func=lambda x: plot_dict[x],
        )
        if plot_name == AnalysisEnum.PIPER.value:
            st.session_state["plot"] = Piper(st.session_state["project"])
        elif plot_name == AnalysisEnum.MAP.value:
            st.session_state["plot"] = Map(st.session_state["project"])
        else:
            st.info("Not implemented yet")
        # elif plot_name == ALL_PLOTS[2]:
        #     st.session_state["plot"] = TimeSeries(st.session_state["project"])
        tabs = st.tabs(["Plot Settings", "Show Plot"])
        with tabs[0]:
            st.session_state["plot"].get_user_input()
        with tabs[1]:
            st.session_state["plot"].show_options()
            st.session_state["plot"].show_plot()
    else:
        st.warning(
            """The current dataset does not include one or several 
mandatory fields for generating any of the available plot types. Please check the 
required format for the plot you wish to generate in the documentation"""
        )


def handle_analysis():
    analysis_dict = st.session_state["project"].analysis_options_dict
    if analysis_dict:
        analysis_name = st.sidebar.selectbox(
            label="Select an analysis",
            options=list(analysis_dict.keys()),
            format_func=lambda x: analysis_dict[x],
        )
        if analysis_name == AnalysisEnum.MKTREND.value:
            st.session_state["analysis"] = MannKendall(st.session_state["project"])
        else:
            st.info("Not implemented yet")
        tabs = st.tabs(["Analysis Settings", "Show Analysis"])
        with tabs[0]:
            st.session_state["analysis"].get_user_input()
        with tabs[1]:
            st.session_state["analysis"].show()
    else:
        st.warning(
            """The current dataset does not include one or several 
mandatory fields for generating any of the available analyses. Please check 
the required format for the analysis you wish to generate in the documentation"""
        )


def handle_calculators():
    """
    some calculations are possible even without any data, therefore no check if there
    are available calculators.
    """
    calculator_list = st.session_state["project"].calculator_list
    calculator_name = st.sidebar.selectbox(
        "Select a Calculator", options=calculator_list
    )
    if calculator_name == CalculatorsEnum.FORMULA_WEIGHT_CONVERSION.value:
        st.session_state["calculator"] = FormulaWeightConversion(
            st.session_state["project"]
        )
    elif calculator_name == CalculatorsEnum.IWQ.value:
        st.session_state["calculator"] = IrrigationWaterQuality(
            st.session_state["project"]
        )
    elif calculator_name == CalculatorsEnum.FORMULA_WEIGHT_CALCULATION.value:
        st.session_state["calculator"] = FormulaWeightCalculator(
            st.session_state["project"]
        )
    elif calculator_name == CalculatorsEnum.SATURATION_INDEX.value:
        st.session_state["calculator"] = SaturationIndex(st.session_state["project"])
    st.session_state["calculator"].show()


def main():
    """
    Allows the user to select a tab and creates the respectives analysis type
    instances.
    """
    init_layout()
    init_project()
    MENU_OPTIONS = ["Home", "Data", "Plots", "Analyses", "Calculator"]
    menu_action = option_menu(
        "",
        MENU_OPTIONS,
        icons=["house", "server", "graph-up", "search", "calculator", "key"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    menu_id = MENU_OPTIONS.index(menu_action)

    st.sidebar.markdown(f"# {MY_NAME}")
    if menu_id == 0:
        st.image(SPLASH_IMAGE)
        st.write(ABOUT_TEXT.format(__author_email__))
    elif menu_id == 1:
        st.session_state["project"].get_user_input()
    elif menu_id == 2:
        handle_plots()
    elif menu_id == 3:
        handle_analysis()
    elif menu_id == 4:
        handle_calculators()

    show_documentation_link()
    show_info_box()


if __name__ == "__main__":
    main()
