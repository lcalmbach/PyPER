import pandas as pd
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import (
    Label,
    HoverTool,
    Arrow,
    NormalHead,
)
from bokeh.models.annotations import Title
from bokeh.core.enums import MarkerType, LineDash
from zipfile import ZipFile
import os
from helper import get_random_filename, add_meqpl_columns, flash_text, random_string
from config import (
    PARAMETER_DICT,
    TEMP_FOLDER,
    ALL_CATIONS,
    ALL_ANIONS,
    HORIZONTAL_ALIGNEMENT_OPTIONS,
    MAX_LEGEND_ITEMS,
    FONT_SIZES,
    IMAGE_FORMATS,
    SIN60,
    COS60,
    TAN60,
)
from project import Project
import colors

gap = 20
figure_padding_left = 10
figure_padding_right = 10
figure_padding_top = 10
figure_padding_bottom = 20
marker_size = 10
tick_len = 2
grid_color = "darkgrey"
line_color = "black"
grid_line_pattern = "dashed"
grid_line_pattern = "dotted"
legend_location = "top_right"
arrow_length = 5
arrow_size = 5
MARKER_GENERATORS = ["1) symbol, 2) color", "1) color, 2) symbol", "color+symbol"]


class Piper:
    def __init__(self, prj: Project):
        self.data = pd.DataFrame()
        self.project = prj

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, prj):
        self._project = prj
        self.cfg = {
            "group-plot-by": None,
            "color": None,
            "marker-size": 8,
            "marker-fill-alpha": 0.8,
            "marker-line-color": "#303132",
            "color-palette": "Category20",
            "default-color": "#1f77b4",
            "color-number": 11,
            "marker-generator": MARKER_GENERATORS[0],
            "marker-colors": [],
            "marker-types": [
                "circle",
                "square",
                "triangle",
                "diamond",
                "inverted_triangle",
            ],
            "tooltips": {},
            "plot-width": 800,
            "plot-title": "",
            "plot-title-text-size": 1.0,
            "plot-title-align": "center",
            "plot-title-font": "arial",
            "image-format": "png",
            "show-grid": True,
            "show-tick-labels": True,
            "tick-label-font-size": 9,
            "axis-title-font-size": 12,
            # if true images will be saved automatically after each render
            "save-images": False,
            # if set to True, the plot data will be shown in a table below the plot
            "show-data": True,
            # unit for major ions in tooltips
            "tooltips_mion_units": "mg/L",
            # number of digits in tooltip concentration columns
            "tooltips_digits": 1,
            # if set to False, a plot button appears and has to be pressed to render plot
            "auto-render": True,
        }
        self.data = self.init_data(prj.data)
        self.images = []
        self.cfg["tooltips"] = self.init_tooltips(prj)

    def init_tooltips(self, prj: Project):
        tooltips = {}
        field_list = prj.fields_list
        for field in field_list:
            tooltips[field] = (
                True
                if field
                in [
                    "date",
                    "sample_date",
                    "station",
                    "ca",
                    "mg",
                    "k",
                    "na",
                    "cl",
                    prj.default_alkalinity_par,  # alk or hco3
                    "so4",
                ]
                else False
            )
        return tooltips

    def init_data(self, df):
        self.data = df
        cations = [x for x in self.data.columns if x in ALL_CATIONS]
        anions = [
            x
            for x in self.data.columns
            if x in ALL_ANIONS[self.project.default_alkalinity_par]
        ]
        self.data_ok = len(cations) >= 3 and len(cations) >= 3
        if self.data_ok:
            self.data = self.data[
                self.data["na"].notnull()
                & self.data["ca"].notnull()
                & self.data["mg"].notnull()
                & self.data["cl"].notnull()
                & self.data["so4"].notnull()
                & self.data[self.project.default_alkalinity_par].notnull()
            ]
            self.data.replace(to_replace=[None], value=0, inplace=True)
            self.data = add_meqpl_columns(self.data, cations + anions)
            meqpl_cations = [f"{item}_meqpl" for item in cations]
            meqpl_anions = [f"{item}_meqpl" for item in anions]
            self.data.loc[:, "sum_cations_meqpl"] = self.data[meqpl_cations].sum(axis=1)
            self.data.loc[:, "sum_anions_meqpl"] = self.data[meqpl_anions].sum(axis=1)
            for par in cations:
                self.data.loc[:, f"{par}_pct"] = (
                    self.data[f"{par}_meqpl"] / self.data["sum_cations_meqpl"] * 100
                )
            for par in anions:
                self.data[f"{par}_pct"] = (
                    self.data[f"{par}_meqpl"] / self.data["sum_anions_meqpl"] * 100
                )
            self.cfg["cation_cols"] = [f"{x}_pct" for x in cations]
            self.cfg["anion_cols"] = [f"{x}_pct" for x in anions]
            self.data.loc[:, "ion_balance_pct"] = (
                (self.data["sum_cations_meqpl"] - self.data["sum_anions_meqpl"])
                / (self.data["sum_cations_meqpl"] + self.data["sum_anions_meqpl"])
                * 100
            )

            return self.data
        else:
            st.write("data is not complete")
            return None

    def get_tooltips(self):
        tooltips = []
        formatter = {}
        for key, value in self.project.fields.iterrows():
            # for ions, the user can choose if he wants to see mg/L, meq/L or meq%
            if self.cfg["tooltips"][key]:
                column_is_ion = (
                    key in ALL_ANIONS[self.project.default_alkalinity_par] + ALL_CATIONS
                )
                if column_is_ion:
                    if self.cfg["tooltips_mion_units"] == "mg/L":
                        par = key
                    elif self.cfg["tooltips_mion_units"] == "meq/L":
                        par = f"{key}_meqpl"
                    else:
                        par = f"{key}_pct"
                else:
                    par = key

                if value["type"] == "float":
                    format_string = f"{{%0.{value['digits']}f}}"
                elif value["type"] in ["date", "datetime"]:
                    format_string = "{%F}"
                else:
                    format_string = ""
                if column_is_ion:
                    tooltip = (
                        f"{value['label']} [{self.cfg['tooltips_mion_units']}]",
                        f"@{par}{format_string}",
                    )
                else:
                    tooltip = (value["label"], f"@{par}{format_string}")
                tooltips.append(tooltip)

                if value["type"] == "float":
                    formatter[f"@{par}"] = "printf"
                elif value["type"] in ["date", "datetime"]:
                    formatter[f"@{par}"] = "datetime"
        return tooltips, formatter

    def get_tranformed_data(self, df: pd.DataFrame):
        def transform_to_xy(df, type):
            if type == "cations":
                ions_list = ["ca_pct", "na_pct", "mg_pct"]
                if "k_pct" in self.cfg["cation_cols"]:
                    _df = df.reset_index()[self.cfg["cation_cols"] + ["index"]]
                    _df["na_pct"] = _df["na_pct"] + _df["k_pct"]
                else:
                    _df = df.reset_index()[ions_list + ["index"]]
                pct_array = _df[ions_list + ["index"]].to_numpy()
                offset = 0
            else:
                ions_list = ["hco3_pct", "cl_pct", "so4_pct"]
                if "co3_pct" in self.cfg["anion_cols"]:
                    _df = df.reset_index()[self.cfg["anion_cols"] + ["index"]]
                    _df["hco3_pct"] = _df["hco3_pct"] + _df["co3_pct"]
                else:
                    _df = df.reset_index()[ions_list + ["index"]]
                pct_array = _df[ions_list + ["index"]].to_numpy()
                offset = 100 + gap
            df_xy = pd.DataFrame()
            index_col = pct_array.shape[1] - 1
            x = 0
            y = 0
            i = 0
            for row in pct_array:
                if row[0] == 100:
                    x = 0
                    y = 0
                elif row[1] == 100:
                    x = 100
                    y = 0
                elif row[2] == 100:
                    x = 50
                    y = 100 * SIN60
                else:
                    x = row[1] / (row[0] + row[1]) * 100
                    # find linear equation mx + q = y
                    if x != 50:
                        m = 100 / (50 - x)
                        q = -(m * x)
                        x = (row[2] - q) / m
                    y = SIN60 * row[2]
                df_xy = df_xy.append(
                    {
                        "index": row[index_col],
                        "_x": x + offset,
                        "_y": y,
                        "type": type[0:1],
                    },
                    ignore_index=True,
                )
                i += 1
            df_xy["index"] = df_xy["index"].astype(int)
            df_xy = df_xy.set_index("index").join(df)
            return df_xy

        def projected_point(anions: pd.DataFrame, cations: pd.DataFrame):
            # ax! = ax! + 110
            #
            # m! = TAN60
            # Q1! = cy! - m! * cx!
            # Q2! = ay! + m! * ax!
            # prx! = (Q2! - Q1!) / (2 * m!)
            # pry! = TAN60 * prx! + Q1!

            df_xy = pd.DataFrame()
            for i in range(0, len(anions)):
                m = TAN60
                q1 = cations.iloc[i]["_y"] - (m * cations.iloc[i]["_x"])
                q2 = anions.iloc[i]["_y"] + (m * anions.iloc[i]["_x"])

                prx = (q2 - q1) / (2 * m)
                pry = m * prx + q1
                df_xy = df_xy.append(
                    {
                        "index": anions.reset_index().iloc[i]["index"],
                        "_x": prx,
                        "_y": pry,
                        "type": "p",
                    },
                    ignore_index=True,
                )

            df_xy["index"] = df_xy["index"].astype(int)
            df_xy = df_xy.set_index("index").join(self.data)
            return df_xy

        cations_df = transform_to_xy(df, "cations")
        anions_df = transform_to_xy(df, "anions")
        projected_df = projected_point(anions_df, cations_df)
        df_xy = pd.concat([cations_df, anions_df, projected_df], ignore_index=True)
        return df_xy

    def draw_triangles(self):
        x1 = [0, 100, 50, 0]
        y1 = [0, 0, SIN60 * 100, 0]

        x2 = [100 + gap, 200 + gap, 150 + gap, 100 + gap]
        y2 = [0, 0, SIN60 * 100, 0]

        x4 = [100 + gap / 2, 50 + gap / 2, 100 + gap / 2, 150 + gap / 2, 100 + gap / 2]
        y4 = [
            SIN60 * gap,
            SIN60 * (100 + gap),
            SIN60 * (200 + gap),
            SIN60 * (100 + gap),
            SIN60 * gap,
        ]
        self.plot.axis.visible = False
        self.plot.grid.visible = False

        self.plot.line(x1, y1, line_width=1, color=line_color)
        self.plot.line(x2, y2, line_width=1, color=line_color)
        self.plot.line(x4, y4, line_width=1, color=line_color)

    def draw_axis(self):
        def draw_xaxis_base(offset: bool):
            y = [0, -tick_len * SIN60]
            for i in range(1, 5):
                delta = (100 + gap) if offset else 0
                if offset:
                    x = [i * 20 + delta, i * 20 - tick_len * COS60 + delta]
                else:
                    x = [i * 20 + delta, i * 20 + tick_len * COS60 + delta]
                self.plot.line(x, y, line_width=1, color=line_color)
                text = str(i * 20) if offset else str(100 - i * 20)
                tick_label = Label(
                    x=x[1] - 2,
                    y=y[1] - 6,
                    text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                    text=text,
                    render_mode="css",
                )
                self.plot.add_layout(tick_label)

        def draw_triangle_left(offset: bool):
            delta = (100 + gap) if offset else 0
            for i in range(1, 5):
                x_tick = [delta + i * 10, delta + i * 10 - tick_len]
                y_tick = [i * 20 * SIN60, i * 20 * SIN60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                if not offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] - 5
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                        text=str(i * 20),
                        render_mode="css",
                    )
                    self.plot.add_layout(tick_label)

        def draw_triangle_right(offset: bool):
            delta = (100 + gap) if offset else 0
            for i in range(1, 5):
                x_tick = [delta + 100 - i * 10, delta + 100 - i * 10 + tick_len]
                y_tick = [i * 20 * SIN60, i * 20 * SIN60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                if offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] + 1
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                        text=str(i * 20),
                        render_mode="css",
                    )
                    self.plot.add_layout(tick_label)

        def draw_diamond_ul():
            for i in range(1, 5):
                x_tick = [
                    50 + gap / 2 + i * 10,
                    50 + gap / 2 + i * 10 - tick_len * COS60,
                ]
                y_tick = [
                    (100 + gap + i * 20) * SIN60,
                    (100 + gap + i * 20) * SIN60 + tick_len * SIN60,
                ]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                y = y_tick[1] - 2
                x = x_tick[1] - 5
                tick_label = Label(
                    x=x,
                    y=y,
                    text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                    text=str(i * 20),
                    render_mode="css",
                )
                self.plot.add_layout(tick_label)

        def draw_diamond_ur():
            for i in range(1, 5):
                x_tick = [
                    100 + gap / 2 + i * 10,
                    100 + gap / 2 + i * 10 + tick_len * COS60,
                ]
                y_tick = [
                    (200 + gap - i * 20) * SIN60,
                    (200 + gap - i * 20) * SIN60 + tick_len * SIN60,
                ]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                y = y_tick[1] - 2
                x = x_tick[1] + 1
                tick_label = Label(
                    x=x,
                    y=y,
                    text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                    text=str(100 - i * 20),
                    render_mode="css",
                )
                self.plot.add_layout(tick_label)

        def draw_grids():
            def draw_triangle_grids(offset: bool):
                delta = (100 + gap) if offset else 0
                for i in range(1, 5):
                    # left-right
                    x = [i * 10 + delta, 100 - i * 10 + delta]
                    y = [i * 20 * SIN60, i * 20 * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                    # horizontal
                    x = [i * 20 + delta, 50 + i * 10 + delta]
                    y = [0, (100 - i * 20) * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                    # right-left
                    x = [i * 20 + delta, i * 10 + delta]
                    y = [0, i * 20 * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )

            def draw_diamond_grid():
                for i in range(1, 5):
                    # diamond left-right
                    x = [50 + gap / 2 + i * 10, 100 + gap / 2 + i * 10]
                    y = [(100 + gap + i * 20) * SIN60, (gap + i * 20) * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                    # diamond right-left
                    x = [100 + gap / 2 + i * 10, 50 + gap / 2 + i * 10]
                    y = [(200 + gap - i * 20) * SIN60, (100 + gap - i * 20) * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                    # diamond horizontal top
                    x = [50 + gap / 2 + i * 10, 100 + gap / 2 + 50 - i * 10]
                    y = [(100 + gap + i * 20) * SIN60, (100 + gap + i * 20) * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                    # diamond horizontal bottom
                    x = [100 + gap / 2 + i * 10, 100 + gap / 2 - i * 10]
                    y = [(gap + i * 20) * SIN60, (gap + i * 20) * SIN60]
                    self.plot.line(
                        x,
                        y,
                        line_width=1,
                        color=grid_color,
                        line_dash=grid_line_pattern,
                    )
                # middle line
                x = [50 + gap / 2, 100 + gap + 50 - gap / 2]
                y = [(100 + gap) * SIN60, (100 + gap) * SIN60]
                self.plot.line(
                    x, y, line_width=1, color=grid_color, line_dash=grid_line_pattern
                )

            def draw_axis_titles():
                def draw_ca_title():
                    x = 50 - 3
                    y = 0 - 3 - self.cfg["axis-title-font-size"]
                    xa = [x - 2, x - 2 - arrow_size]
                    ya = [y + 2.5, y + arrow_size]
                    title = "Ca++"

                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=arrow_size),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[0],
                        )
                    )

                def draw_cl_title():
                    x = 100 + gap + 50 - 3
                    y = 0 - 3 - self.cfg["axis-title-font-size"]
                    xa = [x + 7, x + 11]
                    ya = [y + 2.5, y + 2]
                    title = "Cl-"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[0],
                        )
                    )

                def draw_mg_title():
                    x = 12
                    y = 44 - self.cfg["axis-title-font-size"] + 3
                    # self.plot.circle(x=x,y=y)
                    xa = [x + 9 * COS60, x + 9 * COS60 + 4 * COS60]
                    ya = [y + 14 * SIN60, y + 14 * SIN60 + 4 * SIN60]

                    title = "Mg++"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=60.5,  # not sure why 60 gives the wrong angle
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                def draw_SO4_title():
                    x = 200 + gap - 25 - 13 * COS60 + 14
                    y = 50 * SIN60 - self.cfg["axis-title-font-size"] + 15 * SIN60
                    # self.plot.circle(x=x,y=y)
                    xa = [x + 2 * COS60, x + 2 * COS60 - 4 * COS60]
                    ya = [y + 2 * SIN60, y + 2 * SIN60 + 4 * SIN60]

                    title = "SO4--"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=-60.5,  # not sure why 60 gives the wrong angle
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                def draw_cl_so4_title():
                    x = 50 + gap / 2 + 20 - 10
                    y = (100 + gap + 40) * SIN60

                    xa = [
                        x + 23 * COS60 - 2 * COS60,
                        x + 25 * COS60 - 2 * COS60 + (arrow_length * COS60),
                    ]
                    ya = [
                        y + 23 * SIN60 + 2 * SIN60,
                        y + 25 * SIN60 + 2 * SIN60 + (arrow_length * SIN60),
                    ]

                    title = "Cl- + SO4--"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=60,  # not sure why 60 gives the wrong angle
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                def draw_ca_mg_title():
                    x = 100 + gap + 50 - 33
                    y = (100 + gap + 70) * SIN60

                    xa = [
                        x + 30 * COS60 + 3 * COS60,
                        x + 30 * COS60 + 3 * COS60 + (arrow_length * COS60),
                    ]
                    ya = [
                        y - 30 * SIN60 + 3 * SIN60,
                        y - 30 * SIN60 + 3 * SIN60 - (arrow_length * SIN60),
                    ]

                    title = "Ca++ + Mg++"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=-60,
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                def draw_HCO3_CO3_title():
                    x = 100 + gap / 2 + 23
                    y = gap + 20

                    xa = [x - 3, x - 3 - (arrow_length * COS60)]
                    ya = [y, y - (arrow_length * SIN60)]

                    title = "HCO3- + CO3--"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=60,
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                def draw_Na_K_title():
                    x = 100 + gap / 2 - 30 - 9
                    y = (80 - 3) * SIN60

                    xa = [
                        x + (19 + 6) * COS60,
                        x + (19 + 6) * COS60 + (arrow_length * COS60),
                    ]
                    ya = [y - 19 * SIN60, y - 19 * SIN60 - (arrow_length * SIN60)]

                    title = "Na+ + K+"
                    tick_label = Label(
                        x=x,
                        y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title,
                        text_font_style="bold",
                        angle=-60,
                        angle_units="deg",
                    )
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(
                        Arrow(
                            end=NormalHead(size=5),
                            line_color=line_color,
                            x_start=xa[0],
                            y_start=ya[0],
                            x_end=xa[1],
                            y_end=ya[1],
                        ),
                    )

                draw_ca_title()
                draw_cl_title()
                draw_mg_title()
                draw_SO4_title()
                draw_cl_so4_title()
                draw_ca_mg_title()
                draw_HCO3_CO3_title()
                draw_Na_K_title()

            def draw_main_labels(titles: list, offset: bool):
                delta = 100 + gap if offset else 0
                # Ca/Alk
                if not offset:
                    x = 0 - self.cfg["axis-title-font-size"] * 0.6 + delta
                else:
                    x = delta
                y = 0 - self.cfg["axis-title-font-size"] * 0.8
                tick_label = Label(
                    x=x,
                    y=y,
                    text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[0],
                    text_font_style="bold",
                )
                self.plot.add_layout(tick_label)

                # Na+K/Cl: todo: find out how the calculate the length of the text
                if not offset:
                    x = 100 - 6 - len(titles[1]) + delta
                else:
                    x = 100 + delta
                y = 0 - self.cfg["axis-title-font-size"] * 0.8
                tick_label = Label(
                    x=x,
                    y=y,
                    text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[1],
                    text_font_style="bold",
                )
                self.plot.add_layout(tick_label)

                # Mg/SO4
                x = 50 + delta
                y = 100 * SIN60 + 2
                tick_label = Label(
                    x=x,
                    y=y,
                    text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[2],
                    text_font_style="bold",
                )
                self.plot.add_layout(tick_label)

            if self.cfg["show-grid"]:
                draw_triangle_grids(offset=False)
                draw_triangle_grids(offset=True)
                draw_diamond_grid()
            draw_axis_titles()
            self.plot.legend.click_policy = "mute"

        if self.cfg["show-tick-labels"]:
            draw_xaxis_base(offset=False)
            draw_xaxis_base(offset=True)
            draw_triangle_left(offset=False)
            draw_triangle_left(offset=True)
            draw_triangle_right(offset=False)
            draw_triangle_right(offset=True)
            draw_diamond_ul()
            draw_diamond_ur()

        draw_grids()

    def draw_markers(self, df):
        def color_generator(i: int):
            all_colors = colors.get_colors(
                self.cfg["color-palette"], self.cfg["color-number"]
            )
            if (
                MARKER_GENERATORS.index(self.cfg["marker-generator"]) == 0
            ):  # symbol first then color
                color_id = i // len(self.cfg["marker-types"])
                color = all_colors[color_id]
                marker_type_id = i % len(self.cfg["marker-types"])
                marker_type = self.cfg["marker-types"][marker_type_id]
            elif (
                MARKER_GENERATORS.index(self.cfg["marker-generator"]) == 1
            ):  # color first then symbol
                marker_type_id = i // len(self.cfg["marker-types"])
                marker_type = self.cfg["marker-types"][marker_type_id]
                color_id = i % len(self.cfg["marker-types"])
                color = all_colors[color_id]
            else:
                serie_len = (
                    len(self.cfg["marker-types"])
                    if len(self.cfg["marker-types"]) < len(self.cfg["marker-types"])
                    else len(self.cfg["marker-types"])
                )
                id = i % serie_len
                color = all_colors[id]
                marker_type = self.cfg["marker-types"][id]
            return color, marker_type

        def draw_symbol(
            df: pd.DataFrame, marker_color: str, marker_type: str, label: str
        ):
            if type(label) != str:
                label = str(label)
            if marker_type == "asterisk":
                self.plot.asterisk(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "circle":
                self.plot.circle(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "circle_cross":
                self.plot.circle_cross(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "circle_dot":
                self.plot.circle_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "circle_x":
                self.plot.circle_x(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "circle_y":
                self.plot.circle_y(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "cross":
                self.plot.cross(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "dash":
                self.plot.dash(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "diamond":
                self.plot.diamond(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "diamond_cross":
                self.plot.diamond_cross(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "diamond_dot":
                self.plot.diamond_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "dot":
                self.plot.dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "hex":
                self.plot.hex(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "hex_dot":
                self.plot.hex_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "inverted_triangle":
                self.plot.inverted_triangle(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "plus":
                self.plot.plus(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "square":
                self.plot.square(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "square_cross":
                self.plot.square_cross(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "square_dot":
                self.plot.square_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "square_pin":
                self.plot.square_pin(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "square_x":
                self.plot.square_x(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "star":
                self.plot.star(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "star_dot":
                self.plot.star_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "triangle":
                self.plot.triangle(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "triangle_dot":
                self.plot.triangle_dot(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "x":
                self.plot.x(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )
            elif marker_type == "y":
                self.plot.y(
                    "_x",
                    "_y",
                    legend_label=label,
                    size=self.cfg["marker-size"],
                    color=marker_color,
                    line_color=self.cfg["marker-line-color"],
                    alpha=self.cfg["marker-fill-alpha"],
                    source=df,
                )

        if self.cfg["color"] is None:
            draw_symbol(
                df,
                self.cfg["default-color"],
                self.cfg["marker-types"][0],
                "",
            )
            self.plot.legend.visible = False
        else:
            items = list(df[self.cfg["color"]].dropna().unique())
            if len(items) > MAX_LEGEND_ITEMS:
                warning = f"Plot has {len(items)} items, only the first {MAX_LEGEND_ITEMS} will be shown. Use filters to further reduce the number of legend-items"
                flash_text(warning, "warning")
                items = items[:MAX_LEGEND_ITEMS]
            i = 0
            for item in items:
                color, marker_type = color_generator(i)
                filtered_df = df[df[self.cfg["color"]] == item]
                draw_symbol(filtered_df, color, marker_type, item)
                i += 1
            self.plot.legend.location = legend_location

    def get_user_input(self):
        if st.session_state["project"] == self.project:
            self.init_data(self.project.data)
        else:
            self.project = st.session_state["project"]
        with st.expander("Plot Properties", expanded=True):
            # title
            group_by_options = [None] + self.project.group_fields()
            self.cfg["plot-title"] = st.text_input(
                "Plot Title", value=self.cfg["plot-title"]
            )
            self.cfg["plot-title-text-size"] = st.number_input(
                "Plot Title Font Size",
                min_value=0.1,
                max_value=5.0,
                value=self.cfg["plot-title-text-size"],
            )
            id = HORIZONTAL_ALIGNEMENT_OPTIONS.index(self.cfg["plot-title-align"])
            self.cfg["plot-title-align"] = st.selectbox(
                "Plot Title Alignment", options=HORIZONTAL_ALIGNEMENT_OPTIONS, index=id
            )
            id = group_by_options.index(self.cfg["group-plot-by"])
            self.cfg["group-plot-by"] = st.selectbox(
                "Group Plot By", options=group_by_options, index=id
            )
            id = group_by_options.index(self.cfg["color"])
            self.cfg["color"] = st.selectbox(
                "Group Legend By", options=group_by_options, index=id
            )
            self.cfg["plot-width"] = st.number_input(
                "Plot Width (Points)",
                min_value=100,
                max_value=2000,
                step=50,
                value=self.cfg["plot-width"],
            )
            self.cfg["show-grid"] = st.checkbox(
                "Show Grids", value=self.cfg["show-grid"]
            )
            self.cfg["show-tick-labels"] = st.checkbox(
                "Show Tick Labels", value=self.cfg["show-tick-labels"]
            )
            if self.cfg["show-tick-labels"]:
                id = FONT_SIZES.index(self.cfg["tick-label-font-size"])
                self.cfg["tick-label-font-size"] = st.selectbox(
                    "Tick Label Font Size", options=FONT_SIZES, index=id
                )
            id = FONT_SIZES.index(self.cfg["axis-title-font-size"])
            self.cfg["axis-title-font-size"] = st.selectbox(
                "Axis Title Label Font Size", options=FONT_SIZES, index=id
            )
            id = IMAGE_FORMATS.index(self.cfg["image-format"])
            self.cfg["image-format"] = st.selectbox(
                "Image Output Format", options=IMAGE_FORMATS, index=id
            )
        with st.expander("Marker properties", expanded=True):
            # https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors
            self.cfg["marker-size"] = st.number_input(
                "Marker Size (Points)",
                min_value=1,
                max_value=50,
                step=1,
                value=int(self.cfg["marker-size"]),
            )
            (
                self.cfg["color-palette"],
                self.cfg["color-number"],
            ) = colors.user_input_palette(
                "Marker Color Palette",
                self.cfg["color-palette"],
                self.cfg["color-number"],
            )

            color_list = colors.get_colors(
                self.cfg["color-palette"], self.cfg["color-number"]
            )
            id = (
                color_list.index(self.cfg["default-color"])
                if self.cfg["default-color"] in color_list
                else color_list[0]
            )
            self.cfg["default-color"] = st.selectbox(
                "Default Color",
                options=color_list,
                index=id,
            )

            id = MARKER_GENERATORS.index(self.cfg["marker-generator"])
            self.cfg["marker-generator"] = st.selectbox(
                "Marker Generator Algorithm", options=MARKER_GENERATORS, index=id
            )

            self.cfg["marker-fill-alpha"] = st.number_input(
                "Marker Fill Opacity",
                min_value=0.0,
                max_value=1.0,
                step=0.1,
                value=self.cfg["marker-fill-alpha"],
            )
            self.cfg["marker-types"] = st.multiselect(
                "Marker types",
                options=list(MarkerType),
                default=self.cfg["marker-types"],
            )
            st.markdown("Tooltips")
            if self.cfg["tooltips"] != self.project.fields_list:
                self.cfg["tooltips"] = self.init_tooltips(self.project)
            for key, row in self.project.fields.iterrows():
                self.cfg["tooltips"][key] = st.checkbox(
                    f"Show {row['label']}",
                    value=self.cfg["tooltips"][key],
                    key=key + "cb",
                )
            cols = st.columns([2, 1, 4])
            with cols[0]:
                unit_options = ["mg/L", "meq/L", "meq%"]
                id = unit_options.index(self.cfg["tooltips_mion_units"])
                self.cfg["tooltips_mion_units"] = st.selectbox(
                    "Unit for Major Ions:", unit_options, id
                )
            with cols[1]:
                self.cfg["tooltips_digits"] = st.number_input(
                    "Digits for Concentration Units:", self.cfg["tooltips_digits"]
                )

    def get_plot(self, df):
        self.plot = figure(
            width=int(self.cfg["plot-width"]),
            height=int(self.cfg["plot-width"] * SIN60),
            y_range=(
                -figure_padding_bottom,
                int((200 + gap + figure_padding_top) * SIN60),
            ),
            x_range=(-figure_padding_left, 200 + gap + figure_padding_right),
        )
        tooltips, formatters = self.get_tooltips()
        self.plot.add_tools(
            HoverTool(
                tooltips=tooltips,
                formatters=formatters,
            ),
        )
        if self.cfg["plot-title"] != "":
            title = Title()
            placeholder = f"{{{self.cfg['group-plot-by']}}}"
            if placeholder in self.cfg["plot-title"]:
                value = str(df.iloc[0][self.cfg["group-plot-by"]])
                title.text = self.cfg["plot-title"].replace(placeholder, value)
            else:
                title.text = self.cfg["plot-title"]
            title.text_font_size = f"{self.cfg['plot-title-text-size']}em"
            title.align = self.cfg["plot-title-align"]
            self.plot.title = title

        self.draw_triangles()
        self.draw_axis()
        data_transformed = self.get_tranformed_data(df)
        self.draw_markers(data_transformed)
        self.plot.background_fill_color = None
        self.plot.border_fill_color = None
        return self.plot

    def create_image_file(self, p):
        # os.environ["PATH"] += os.pathsep + os.getcwd()
        # if st.button("Save png file", key=f'save_{random_string(5)}'):
        filename = get_random_filename("piper", TEMP_FOLDER, self.cfg["image-format"])
        p.toolbar_location = None
        p.outline_line_color = None
        if self.cfg["image-format"] == "png":
            export_png(p, filename=filename)
        else:
            p.output_backend = "svg"
            export_svgs(p, filename=filename)
        self.images.append(filename)

    def show_download_button(self):
        """
        Shows a download button that will store the files included in
        the self.images list. if there is more than 1 file, all files
        a zipped into 1 downloadable file.
        """
        if len(self.images) == 1:
            filename = self.images[0]
        elif len(self.images) > 1:
            prefix = f"piper-{self.cfg['group-plot-by']}"
            filename = get_random_filename(prefix, TEMP_FOLDER, "zip")
            zip_file = ZipFile(filename, "w")
            for file in self.images:
                zip_file.write(file, file)
            zip_file.close()

        with open(filename, "rb") as file:
            btn = st.download_button(
                label="Download image",
                data=file,
                file_name=os.path.basename(filename),
                mime="image/png",
            )

    def show_data(self, df: pd.DataFrame):
        """
        Shows the data used in the current plot. Below the table a download
        button is shown which allows to save the data in a csv file.

        Args:
            df (pd.DataFrame): data used in current plot
        """

        if self.cfg["show-data"]:
            with st.expander("Data", expanded=False):
                st.markdown(f"{len(df)} records")
                st.write(df)
                st.download_button(
                    label="Download data as CSV",
                    data=df.to_csv(sep=";").encode("utf-8"),
                    file_name="fontus_piper_data.csv",
                    mime="text/csv",
                    key=f"save_button_{random_string(5)}",
                )

    def show_options(self):
        with st.sidebar.expander("⚙️Settings", expanded=True):
            self.cfg["save-images"] = st.checkbox(
                "Save images", value=self.cfg["save-images"]
            )
            self.cfg["show-data"] = st.checkbox(
                "Show Data", value=self.cfg["show-data"]
            )
            self.cfg["auto-render"] = st.checkbox(
                "Auto Render Plots", value=self.cfg["auto-render"]
            )

    def delete_old_images(self):
        """
        Removes the images created in the previous run and empties
        the self.images list.
        """
        if self.images:
            for file in self.images:
                if os.path.isfile():
                    os.remove(file)
            self.images = []

    def show_plot(self):
        """
        Shows one Piper plot if group plots by is None, otherwise a plot is shown for each
        distinct value in the column used as the group plot by parameter. Each plot can be
        saved to file if the save images option is selected. Before each run, the
        existing images of the last run are removed.
        """

        # delete the previously created image so images do not pile up on disk
        self.delete_old_images()
        if self.cfg["auto-render"]:
            run_ok = True
        else:
            run_ok = st.sidebar.button("Plot")
        if run_ok:
            if self.cfg["group-plot-by"]:
                for item in self.project.codes[self.cfg["group-plot-by"]]:
                    df_filtered = self.data[
                        self.data[self.cfg["group-plot-by"]] == item
                    ]
                    if len(df_filtered) > 0:
                        p = self.get_plot(df_filtered)
                        st.bokeh_chart(p)
                        self.show_data(self.data)
                        if self.cfg["save-images"]:
                            self.create_image_file(p)
            else:
                p = self.get_plot(self.data)
                st.bokeh_chart(p)
                self.show_data(self.data)
                if self.cfg["save-images"]:
                    self.create_image_file(p)
            if self.cfg["save-images"] & len(self.images) > 0:
                with st.sidebar:
                    self.show_download_button()
