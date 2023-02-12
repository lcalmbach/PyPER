# https://docs.bokeh.org/en/latest/docs/reference/palettes.html
import streamlit as st
import bokeh.palettes as plts

DISTINCT_COLOR_PALETTES = sorted(list(plts.small_palettes.keys()))

# not used yet
LINEAR_COLORS_PALETTES = [
    "Greys256",
    "Blues256",
    "Cividis256",
    "Viridis256",
    "Greens256",
    "Inferno256",
    "Purples256",
    "Reds256",
]
MARKER_GENERATORS = ["1) symbol, 2) color", "1) color, 2) symbol", "color+symbol"]


def large_palette(palette_name: str, invert: bool = False):
    if palette_name == "Greys256":
        lst = plts.Greys256
    elif palette_name == "Blues256":
        lst = plts.Blues256
    elif palette_name == "Cividis256":
        lst = plts.Cividis256
    elif palette_name == "Viridis256":
        return plts.Viridis256
    elif palette_name == "Greens256":
        lst = plts.Greens256
    elif palette_name == "Inferno256":
        lst = plts.Inferno256
    elif palette_name == "Purples256":
        lst = plts.Purples256
    elif palette_name == "Reds256":
        lst = plts.Reds256
    lst = list(lst)
    lst.reverse()
    return lst


def get_num_colors(palette_name: str) -> int:
    return len(plts.all_palettes[palette_name])


def get_colors(palette_name: str, color_num: int) -> list:
    """
    Looks up the colors for the given palettename and number of colors
    specified and returns the list of colors. the minimum number of colors in a palette
    is 3, if a number less then 3 is requested by the user, the function must
    reduce the number of the minimum number of colors palette

    Args:
        palette_name (str): valid palette name from bokeh.palettes
        color_num (int):    number of colors in palette depending on how many
                            colors are needed

    Returns:
        list: list of colors in specified palette
    """
    if color_num not in plts.all_palettes[palette_name].keys():
        color_num_list = list(plts.all_palettes[palette_name].keys())
        if color_num > color_num_list[-1]:
            color_num = len(color_num_list)
        else:
            clr_list = plts.all_palettes[palette_name][3]

    if color_num not in plts.all_palettes[palette_name].keys():
        clr_list = plts.all_palettes[palette_name][3]
        clr_list = clr_list[:color_num]
    else:
        clr_list = plts.all_palettes[palette_name][color_num]
    return clr_list


def get_palette_table(palette_name: str, num: int) -> str:
    """
    Returns a html palette table with num number of specified cells.
    table can be displayed using st.markdown(html_string,
    unsafe_allow_html=True)

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


# def get_large_palettes():
#    pal = [x for x in plts.all_palettes if '256' in x]
#    st.write(123)
##    pal.reverse()
#    return list(pal)


def user_input_palette(title, plt, num):
    id = DISTINCT_COLOR_PALETTES.index(plt)
    palette = st.selectbox(title, options=DISTINCT_COLOR_PALETTES, index=id)
    max_num = get_num_colors(palette)
    if num > max_num:
        num = max_num
    color_num = st.number_input(
        "Number of colors", min_value=2, max_value=max_num, value=num
    )
    st.markdown(get_palette_table(palette, color_num), unsafe_allow_html=True)
    return palette, color_num


def color_generator(cfg, i: int):
    all_colors = get_colors(cfg["color-palette"], cfg["color-number"])
    if MARKER_GENERATORS.index(cfg["marker-generator"]) == 0:  # symbol first then color
        color_id = i // len(cfg["marker-types"])
        if color_id >= cfg["color-number"]:
            color_id = 0
        color = all_colors[color_id]
        marker_type_id = i % len(cfg["marker-types"])
        marker_type = cfg["marker-types"][marker_type_id]
    elif (
        MARKER_GENERATORS.index(cfg["marker-generator"]) == 1
    ):  # color first then symbol
        marker_type_id = i // len(cfg["marker-types"])
        marker_type = cfg["marker-types"][marker_type_id]
        color_id = i % len(cfg["marker-types"])
        color = all_colors[color_id]
    else:
        serie_len = (
            len(cfg["marker-types"])
            if len(cfg["marker-types"]) < cfg["color-number"]
            else cfg["color-number"]
        )
        id = i % serie_len
        color = all_colors[id]
        marker_type = cfg["marker-types"][id]
    return color, marker_type
