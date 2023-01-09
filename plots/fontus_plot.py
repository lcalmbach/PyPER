# from const import MP # not sure what it is...
import streamlit as st
import pandas as pd
import numpy as np
import xyzservices.providers as xyz
from bokeh.tile_providers import get_provider
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure
from bokeh.models import (
    Label,
    GMapOptions,
    HoverTool,
    Arrow,
    NormalHead,
    ColumnDataSource,
    LinearColorMapper,
)
from bokeh.models.annotations import Title
from zipfile import ZipFile
import os
from helper import get_random_filename, flash_text, random_string
from config import (
    TEMP_FOLDER,
    ALL_CATIONS,
    ALL_ANIONS,
    HORIZONTAL_ALIGNEMENT_OPTIONS,
    MAX_LEGEND_ITEMS,
    FONT_SIZES,
    IMAGE_FORMATS,
    AGGREGATION_FUNCTIONS,
)
from project import Project
import colors


class FontusPlot:
    def __init__(self, prj: Project, type: str):
        self.data = pd.DataFrame()
        self.project = prj
        self.type = type

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, prj):
        self._project = prj
        self.cfg = {
            "group-plot-by": None,
            "group-legend-by": None,
            "color": None,
            "marker-size": 8,
            "marker-fill-alpha": 0.8,
            "marker-line-color": "#303132",
            "color-palette": "Category20",
            "default-color": "#1f77b4",
            "color-number": 11,
            "marker-generator": colors.MARKER_GENERATORS[0],
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
            "plot-height": 800,
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
            # number of digits in tooltip concentration columns
            "tooltips_digits": 1,
            "tooltips_mion_units": "mg/L",
            # if set to False, a plot button appears and has to be pressed to render plot
            "auto-render": True,
            "prop-size-method": None,
            "prop-size-parameter": None,
            "prop-size-min-rad": 4,
            "prop-size-max-rad": 12,
            "prop-size-min-val": 0,
            "prop-size-max-val": 0,
            "legend-location": "top_right",
            "legend-visible": True,
            "legend-visible": True,
            "legend-border-line-width": 2,
            "legend-border-line-color": "grey",
            "legend-border-line-alpha": 0.5,
            "legend-background-fill-color": "white",
            "legend-background-fill-alpha": 0.3,
        }
        self.data = self.init_data(prj.data)
        self.images = []
        self.cfg["tooltips"] = self.init_tooltips(prj)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def tooltip_fields(self):
        result = [x for x in self.cfg["tooltips"] if self.cfg["tooltips"][x]]
        return result

    # -------------------------------------------------------------------------
    # Functions
    # -------------------------------------------------------------------------

    def init_tooltips(self, prj: Project):
        raise NotImplementedError

    def init_data(self, df):
        raise NotImplementedError

    def get_tooltips(self):
        tooltips = []
        formatter = {}
        for key, value in self.project.fields.iterrows():
            # for ions, the user can choose if he wants to see mg/L, meq/L or meq%
            if self.cfg["tooltips"][key]:
                column_is_ion = (
                    key in ALL_ANIONS[self.project.default_alkalinity_par] + ALL_CATIONS
                )
                par = key

                if value["type"] == "float":
                    format_string = f"{{%0.{value['digits']}f}}"
                elif value["type"] in ["date", "datetime"]:
                    format_string = "{%F}"
                else:
                    format_string = ""
                if column_is_ion:
                    tooltip = (
                        f"{value['label']}",
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

    def get_map_rectangle(self, df):
        x_min = df["x"].min()
        x_max = df["x"].max()
        y_min = df["y"].min()
        y_max = df["y"].max()
        return x_min, y_min, x_max, y_max

    def get_prop_size(self, df):
        def get_size(x):
            result = x / self.cfg["max_value"] * self.cfg["max_prop_size"]
            if result > self.cfg["max_prop_size"]:
                result = self.cfg["max_prop_size"]
            elif result < self.cfg["min_prop_size"]:
                result = self.cfg["min_prop_size"]
            return result

        df[cn.PROP_SIZE_COL] = 0
        df[cn.PROP_SIZE_COL] = list(
            map(get_size, list(df[st.session_state.config.value_col]))
        )
        return df

    def add_legend(self, p):
        p.legend.visible = self.cfg["legend-visible"]
        p.legend.location = self.cfg["legend-location"]

        # give title to legend
        p.legend.title = self.cfg["group-legend-by"]

        # customize legend appearance
        # p.legend.label_text_font = "times"
        # p.legend.label_text_font_style = "italic"
        # p.legend.label_text_color = "red"

        # customize border and background of legend
        p.legend.border_line_width = self.cfg["legend-border-line-width"]
        p.legend.border_line_color = self.cfg["legend-border-line-color"]
        p.legend.border_line_alpha = self.cfg["legend-border-line-alpha"]
        p.legend.background_fill_color = self.cfg["legend-background-fill-color"]
        p.legend.background_fill_alpha = self.cfg["legend-background-fill-alpha"]
        return p

    def add_markers(self, p, df):
        def add_marker_to_plot(p, _df, legend_label):
            p.scatter(
                x=self.cfg["x_col"],
                y=self.cfg["y_col"],
                size=self.cfg["marker-size"],
                color=m_color,
                fill_alpha=self.cfg["marker-fill-alpha"],
                line_color=self.cfg["marker-line-color"],
                source=_df,
                marker=m_type,
                legend_label=legend_label,
            )
            return p

        if self.cfg["group-legend-by"]:
            if self.cfg["prop-size-method"] is None:
                codes = self.project.codes[self.cfg["group-legend-by"]]
                id = 0
                for group in codes:
                    m_color, m_type = colors.color_generator(self.cfg, id)
                    filtered_df = df[df[self.cfg["group-legend-by"]] == group]
                    if len(filtered_df) > 0:
                        p = add_marker_to_plot(p, filtered_df, group)
                        id += 1

            elif self.cfg["prop-size-method"] == "color":
                color_mapper = LinearColorMapper(
                    palette=self.cfg["lin_palette"], low=0, high=self.cfg["max_value"]
                )
                p = add_marker_to_plot(p, df, "legend?")
            else:
                filtered_df = self.get_prop_size(df)
                p = add_marker_to_plot(p, filtered_df)
        # no group by field is selected
        else:
            m_color = self.cfg["default-color"]
            m_type = self.cfg["marker-types"][0]
            p = add_marker_to_plot(p, df, "All samples")
        return p

    def aggregate_data(self, data: pd.DataFrame) -> pd.DataFrame():
        """
        Reduces all samples to a single point for each station. If no parameter
        is selected, only unique long, lat are returned together with all
        tooltip fields aggregated by the selected aggregation methode (count, mean
        min, max, std)

        Args:
            data (pd.DataFrame): raw data with n rows per station

        Returns:
            pd.DataFrame: dataframe with 1 row per station and fields reduced to
                          long, lat, tooltips
        """

        self.cfg["tooltips"][self.cfg["group-legend-by"]] = True
        all_fields = [
            self.project.longitude_col,
            self.project.latitude_col,
        ] + self.tooltip_fields
        group_fields = [self.project.longitude_col, self.project.latitude_col] + [
            x for x in self.tooltip_fields if x in self.project.group_fields
        ]
        num_fields = list(set(all_fields).difference(group_fields))
        _df = data[all_fields]
        if num_fields == []:
            _df = _df.drop_duplicates()
        else:
            _df = (
                _df.groupby(group_fields)[num_fields]
                .agg(self.cfg["aggregation-func"])
                .reset_index()
            )
        return _df

    def get_plot(self, df):
        raise NotImplementedError

    def get_user_input(self):
        raise NotImplementedError

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
                st.download_button(
                    label="Download data as CSV",
                    data=df.to_csv(sep=";").encode("utf-8"),
                    file_name="fontus_piper_data.csv",
                    mime="text/csv",
                    key=f"save_button_{random_string(5)}",
                )

    def show_options(self):
        with st.sidebar.expander("⚙️Settings", expanded=True):
            par_options = [None] + self.project.group_fields
            id = par_options.index(self.cfg["group-legend-by"])
            self.cfg["group-legend-by"] = st.selectbox(
                "Group legend by", options=par_options, index=id
            )

            if self.type == "map":
                self.cfg["aggregation-func"] = st.selectbox(
                    "Aggregation function", options=AGGREGATION_FUNCTIONS, index=id
                )
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
        raise NotImplementedError
