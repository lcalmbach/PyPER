import streamlit as st
import pandas as pd
import random, string
from datetime import datetime
import time
import base64
from config import PARAMETER_DICT


def flash_text(text: str, type: str):
    placeholder = st.empty()
    if type == "info":
        placeholder.info(text)
    elif type == "success":
        placeholder.success(text)
    else:
        placeholder.warning(text)
    time.sleep(5)
    placeholder.write("")


def get_random_filename(prefix: str, folder: str, ext: str) -> str:
    """
    Generates a random file by concatenating a folder name, the given 
    prefix and the current time to the second and the extension

    Args:
        prefix (str): used to identify the file more easily
        folder (str): folder where file is to be stored
        ext (str): file extension

    Returns:
        str: full path of filename
    """
    # add a trailing / if not present for foldername
    folder = folder + '/' if folder[-1] != '/' else folder
    suffix = datetime.now().strftime("%y%m%d_%H%M%S")
    result = f"{folder}{prefix}-{suffix}.{ext}"
    return result


def add_pct_columns(df: pd.DataFrame, par_dict: dict, pmd) -> pd.DataFrame:
    """
    converts mg/L concentrations to meq/L, meq% to be used in the piper diagram
    and the ion balance.

    Args:
        df (pd.DataFrame):  dataframe in the sample per row format with all major ions columns
        par_dict(dict):     dict holding formula weights

    Returns:
        pd.DataFrame: same dataframe with added columns xx_meqpl, xx_meqpct for each major ion
    """
    df = calc_meql(df, par_dict, pmd)
    df = calc_pct(df)
    df = calculate_electroneutrality(df)
    return df


def major_ions_complete(df: pd.DataFrame) -> bool:
    """
    Return wether there are columns for all major ions:
    Na, Ca, Mg, Alk, Cl, SO4. K is optionional but is used when present.

    Args:
        df (pd.DataFrame): [description]

    Returns:
        bool: [description]
    """
    ok = [False] * 6
    ok[0] = "ca_pct" in df.columns
    ok[1] = "mg_pct" in df.columns
    ok[2] = "na_pct" in df.columns
    ok[3] = "cl_pct" in df.columns
    ok[4] = ("alk_pct" in df.columns) or ("hco3_pct" in df.columns)
    ok[5] = "so4_pct" in df.columns
    return all(ok)


def add_meqpl_columns(data: pd.DataFrame, parameters: list):
    """
    Returns a grid with meq converted columns for each item in a
    list of column names. columns must be valid chemcial parameters
    defined in PARAMETERS_DICT, which contains the formula weight and
    valence.

    Args:
        data (pd.DataFrame): grid input to which the converted columns should
                             be added
        parameters (list):   list of parameter names, included in the input 
                             table

    Returns:
        pd.DataFrame: input grid with added converted columns.
    """
    for par in parameters:
        if par in data.columns:
            col = f"{par}_meqpl"
            fact = 1 / PARAMETER_DICT[par]["fmw"] * abs(PARAMETER_DICT[par]["valence"])
            data[col] = data[par] * fact
    return data


def is_chemical(par: str) -> bool:
    """
    A parameter name is a chemical, if it is included in the parameter
    dict.

    Args:
        par (str): column name

    Returns:
        bool: True if the expression is a valid parameter key
    """
    return par in PARAMETER_DICT.keys()


def random_string(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))

def get_base64_encoded_image(image_path):
    """
    returns bytecode for an image file
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')