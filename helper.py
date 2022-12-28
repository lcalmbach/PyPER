import streamlit as st
import pandas as pd
import math
import random, string
from datetime import datetime
import time
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


def get_random_filename(prefix: str, ext: str):
    # todo: add further folders
    folder = "images"
    suffix = datetime.now().strftime("%y%m%d_%H%M%S")
    return f"./{folder}/{prefix}-{suffix}.{ext}"


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
    """return wether there are columns for all major ions:
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


def add_meqpl_columns(data, parameters):
    for par in parameters:
        col = f"{par}_meqpl"
        fact = 1 / PARAMETER_DICT[par]["fmw"] * abs(PARAMETER_DICT[par]["valence"])
        data[col] = data[par] * fact
    return data


def is_chemical(par: str):
    return par in PARAMETER_DICT.keys()


def random_string(length):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))
