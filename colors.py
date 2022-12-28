# https://docs.bokeh.org/en/latest/docs/reference/palettes.html
import streamlit as st
import bokeh.palettes as plts

DISTINCT_COLOR_PALETTES = sorted(list(plts.small_palettes.keys()))

# not used yet
LINEAR_COLORS_PALETTES = [
    "Blues256",
    "Cividis256",
    "Greens256",
    "Inferno256",
    "Purples256",
    "Reds256",
]


def get_num_colors(palette_name: str) -> int:
    return len(plts.all_palettes[palette_name])


def get_colors(palette_name: str, color_num: int) -> list:
    """
    Looks up the colors for the given palettename and number of colors
    specified and returns the list of colors.

    Args:
        palette_name (str): valid palette name from bokeh.palettes
        color_num (int):    number of colors in palette depending on how many
                            colors are needed

    Returns:
        list: list of colors in specified palette
    """

    if color_num > get_num_colors(palette_name):
        color_num = get_num_colors(palette_name)
    return plts.all_palettes[palette_name][color_num]


def get_palette_table(palette_name: str, num: int) -> str:
    """
    Returns a html palette table with num number of specified cells.
    table can be displayed using st.markdown(html_string, unsafe_allow_html=True)

    Args:
        palette_name (str): item from DISTINCT_COLOR_PALETTES
        num (int):          number of colors to be used

    Returns:
        str: html string for table
    """
    tbl = "<table border=1><tr>"
    for color in get_colors(palette_name, num):
        tbl += f'<td style="background-color:{color};"</td>'
    tbl += "</tr>"
    return tbl


def user_input_palette(title, plt, num):
    id = DISTINCT_COLOR_PALETTES.index(plt)
    palette = st.selectbox(title, options=DISTINCT_COLOR_PALETTES, index=id)
    max_num = get_num_colors(palette)
    if num > max_num:
        num = max_num
    color_num = st.number_input(
        "Number of colors", min_value=2, max_value=max_num, value=num
    )
    cols = st.columns(2)
    with cols[0]:
        st.markdown(get_palette_table(palette, color_num), unsafe_allow_html=True)
    with cols[1]:
        st.markdown(get_colors(palette, color_num))
    return palette, color_num
