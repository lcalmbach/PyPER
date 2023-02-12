import streamlit as st
import pandas as pd
import numpy as np
import xyzservices.providers as xyz
from bokeh.tile_providers import get_provider
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
)
from bokeh.models.annotations import Title
from bokeh.core.enums import MarkerType, LegendLocation
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

PROP_MARKER_METHODS = [None, "Marker-Size", "Marker-Color"]


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
            "aggregation-func": None,
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
            "prop-marker-method": None,
            "prop-marker-parameter": None,
            "prop-marker-min-size": 4,
            "prop-marker-max-size": 12,
            "prop-marker-min-val": 0,
            "prop-marker-max-val": 0,
            "prop-marker-palette": 0,
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

    @property
    def aggregation_functions(self):
        """
        Returns a list of aggregation functions. For maps, the agg function
        is mandatory other plots need a None first entry which is the default

        Returns:
            _type_: _description_
        """
        if self.type == "Map":
            return AGGREGATION_FUNCTIONS
        else:
            return [None] + AGGREGATION_FUNCTIONS

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
        def add_prop_size_column(_df: pd.DataFrame):
            """
            fill the columns _size_ with the size in points calculalet according to the
            settings of the proportional marker settings. For the piper plot, only the size
            of markers in the projection area is changed, the markers for the cations and antions
            triangle stays the original size

            Args:
                _df (pd.DataFrame): _description_

            Returns:
                _type_: _description_
            """
            par = self.cfg["prop-marker-parameter"]
            key = "_size_"
            _df[key] = self.cfg["marker-size"]
            if self.type == "piper":
                _df.loc[
                    (_df["_type"] == "p")
                    & (_df[par] < self.cfg["prop-marker-min-val"]),
                    key,
                ] = self.cfg["prop-marker-min-size"]
                _df.loc[
                    (_df["_type"] == "p")
                    & (_df[par] > self.cfg["prop-marker-max-val"]),
                    key,
                ] = self.cfg["prop-marker-max-size"]
                _df.loc[
                    (_df["_type"] == "p")
                    & (_df[par] >= self.cfg["prop-marker-min-val"])
                    & (_df[par] <= self.cfg["prop-marker-max-val"]),
                    key,
                ] = (
                    df[par]
                    / self.cfg["prop-marker-max-val"]
                    * self.cfg["prop-marker-max-size"]
                )
                _df[key] = _df[key]
            else:
                _df.loc[(_df[par] < self.cfg["prop-marker-min-val"]), key] = self.cfg[
                    "prop-marker-min-size"
                ]
                _df.loc[(_df[par] > self.cfg["prop-marker-max-val"]), key] = self.cfg[
                    "prop-marker-max-size"
                ]
                _df.loc[
                    (_df[par] >= self.cfg["prop-marker-min-val"])
                    & (_df[par] <= self.cfg["prop-marker-max-val"]),
                    key,
                ] = (
                    df[par]
                    / self.cfg["prop-marker-max-val"]
                    * self.cfg["prop-marker-max-size"]
                )
                _df[key] = _df[key]

            return _df

        def add_prop_color_column(_df):
            par = self.cfg["prop-marker-parameter"]
            key = "_color_"
            idkey = "_clrid_"
            color_list = colors.large_palette(
                palette_name=self.cfg["prop-marker-palette"]
            )
            _df[key] = None
            _df["_clrid_"] = None
            _df.loc[(_df[par] < self.cfg["prop-marker-min-val"]), idkey] = 0
            _df.loc[(_df[par] > self.cfg["prop-marker-max-val"]), idkey] = 255
            _df.loc[
                (_df[par] >= self.cfg["prop-marker-min-val"])
                & (_df[par] <= self.cfg["prop-marker-max-val"]),
                idkey,
            ] = (
                _df[par] / self.cfg["prop-marker-max-val"] * 255
            )
            _df[idkey] = _df[idkey].fillna(-99)

            _df[idkey] = _df[idkey].astype(int)
            _df.loc[_df[idkey] >= 0, key] = _df.loc[_df[idkey] >= 0, idkey].apply(
                lambda x: color_list[x]
            )
            _df.drop(columns=[idkey], axis=1, inplace=True)
            return _df

        def add_prop_color_legend(fig):
            color_list = colors.large_palette(
                palette_name=self.cfg["prop-marker-palette"]
            )

            # Create an empty data source
            source = ColumnDataSource(
                {self.cfg["x_col"]: [-1], self.cfg["y_col"]: [-1]}
            )
            # min marker
            fig.scatter(
                color=color_list[0],
                fill_alpha=self.cfg["marker-fill-alpha"],
                line_color=self.cfg["marker-line-color"],
                source=source,
                marker=m_type,
                legend_label=f"<= {self.cfg['prop-marker-min-val']}",
            )
            # max marker
            fig.scatter(
                color=color_list[255],
                fill_alpha=self.cfg["marker-fill-alpha"],
                line_color=self.cfg["marker-line-color"],
                source=source,
                marker=m_type,
                legend_label=f">= {self.cfg['prop-marker-max-val']}",
            )
            return fig

        def add_marker_to_plot(p, _df, legend_label):
            p.scatter(
                x=self.cfg["x_col"],
                y=self.cfg["y_col"],
                size="_size_" if "_size_" in _df.columns else self.cfg["marker-size"],
                color="_color_" if "_color_" in _df.columns else m_color,
                fill_alpha=self.cfg["marker-fill-alpha"],
                line_color=self.cfg["marker-line-color"],
                source=_df,
                marker=m_type,
                legend_label=legend_label,
            )
            return p
        
        # todo 
        if self.cfg["prop-marker-method"] != None:
            par = self.cfg["prop-marker-parameter"]
            df = df[~pd.isna(df[par])]
        m_color = self.cfg["default-color"]
        m_type = self.cfg["marker-types"][0]
        if self.cfg["group-legend-by"]:
            # marker size or color not porportinal to a numeric parameter
            codes = self.project.codes[self.cfg["group-legend-by"]]
            if self.cfg["prop-marker-method"] is None:
                id = 0
                for group in codes:
                    m_color, m_type = colors.color_generator(self.cfg, id)
                    filtered_df = df[df[self.cfg["group-legend-by"]] == group]
                    if len(filtered_df) > 0:
                        p = add_marker_to_plot(p, filtered_df, group)
                        id += 1
            # marker size proportional to num parameter
            else:
                id = 0
                for group in codes:
                    m_color, m_type = colors.color_generator(self.cfg, id)
                    filtered_df = df[df[self.cfg["group-legend-by"]] == group]
                    if self.cfg["prop-marker-method"] == PROP_MARKER_METHODS[1]:
                        filtered_df = add_prop_size_column(filtered_df)
                    else:
                        filtered_df = add_prop_color_column(filtered_df)
                    if len(filtered_df) > 0:
                        p = add_marker_to_plot(p, filtered_df, group)
                        id += 1
        # no group by field is selected
        else:
            if self.cfg["prop-marker-method"] is None:
                p = add_marker_to_plot(p, df, "All samples")
            elif self.cfg["prop-marker-method"] == PROP_MARKER_METHODS[1]:
                df = add_prop_size_column(df)
                p = add_marker_to_plot(p, df, "All samples")
            else:
                df = add_prop_color_column(df)
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
        data = self.project.filter_data()
        if st.session_state["project"] == self.project:
            self.init_data(data)
        else:
            self.project = st.session_state["project"]

        cols = st.columns(2)
        with cols[0]:
            with st.expander("**Plot**", expanded=True):
                # title
                group_by_options = [None] + self.project.group_fields
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
                    "Plot Title Alignment",
                    options=HORIZONTAL_ALIGNEMENT_OPTIONS,
                    index=id,
                )
                id = group_by_options.index(self.cfg["group-plot-by"])
                self.cfg["group-plot-by"] = st.selectbox(
                    "Group Plot By", options=group_by_options, index=id
                )
                self.cfg["plot-width"] = st.number_input(
                    "Plot Width (Points)",
                    min_value=100,
                    max_value=2000,
                    step=50,
                    value=self.cfg["plot-width"],
                )
                self.cfg["plot-height"] = st.number_input(
                    "Plot Height (Points)",
                    min_value=100,
                    max_value=2000,
                    step=50,
                    value=self.cfg["plot-height"],
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
        with cols[1]:
            with st.expander("**Markers**", expanded=True):
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
                id = (
                    color_list.index(self.cfg["default-color"])
                    if self.cfg["default-color"] in color_list
                    else 0
                )
                self.cfg["default-color"] = st.selectbox(
                    "Default Color",
                    options=color_list,
                    index=id,
                )

                id = colors.MARKER_GENERATORS.index(self.cfg["marker-generator"])
                self.cfg["marker-generator"] = st.selectbox(
                    "Marker Generator Algorithm",
                    options=colors.MARKER_GENERATORS,
                    index=id,
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
        cols = st.columns(2)
        with cols[0]:
            with st.expander("**Tooltips**", expanded=True):
                if self.cfg["tooltips"] != self.project.fields_list:
                    self.cfg["tooltips"] = self.init_tooltips(self.project)
                for key, row in self.project.fields.iterrows():
                    self.cfg["tooltips"][key] = st.checkbox(
                        f"Show {row['label']}",
                        value=self.cfg["tooltips"][key],
                        key=key + "cb",
                    )
        with cols[1]:
            with st.expander("**Legend**", expanded=True):
                self.cfg["legend-visible"] = st.checkbox(
                    label="Show Legend", value=self.cfg["legend-visible"]
                )
                id = list(LegendLocation).index(self.cfg["legend-location"])
                self.cfg["legend-location"] = st.selectbox(
                    label="Legend Location", options=list(LegendLocation), index=id
                )
                self.cfg["legend-border-line-width"] = st.number_input(
                    label="Border-Line width (Points)",
                    min_value=1,
                    max_value=20,
                    value=self.cfg["legend-border-line-width"],
                )
                lblc_options = ["white", "black", "grey", "darkgrey", "silver"]
                id = lblc_options.index(self.cfg["legend-border-line-color"])
                self.cfg["legend-border-line-color"] = st.selectbox(
                    label="Border-Line Color",
                    options=lblc_options,
                    index=id,
                )
                self.cfg["legend-border-line-alpha"] = st.number_input(
                    label="Border-Line Opacity",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(self.cfg["legend-border-line-alpha"]),
                )
                lbfc_options = ["white", "grey", "silver"]
                id = lbfc_options.index(self.cfg["legend-border-line-color"])
                self.cfg["legend-background-fill-color"] = st.selectbox(
                    label="Background Fill Color",
                    options=lbfc_options,
                    index=id,
                )
                self.cfg["legend-background-fill-alpha"] = st.number_input(
                    label="Background Fill Opacity",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(self.cfg["legend-background-fill-alpha"]),
                )
            with st.expander("**Proportional Marker Size or Color**", expanded=True):
                id = PROP_MARKER_METHODS.index(self.cfg["prop-marker-method"])
                self.cfg["prop-marker-method"] = st.selectbox(
                    label="Method", options=PROP_MARKER_METHODS, index=id
                )
                if self.cfg["prop-marker-method"] is not None:
                    par_options = self.project.num_fields
                    id = (
                        par_options.index(self.cfg["prop-marker-parameter"])
                        if self.cfg["prop-marker-parameter"] in par_options
                        else 0
                    )
                    self.cfg["prop-marker-parameter"] = st.selectbox(
                        label="Parameter", options=par_options, index=id
                    )
                    self.cfg["prop-marker-min-val"] = st.number_input(
                        label="Minimum Value",
                        min_value=-1.0e6,
                        max_value=1.0e6,
                        value=float(self.cfg["prop-marker-min-val"]),
                        help="Values smaller than min value will be presented with the minimum radius size",
                    )
                    self.cfg["prop-marker-max-val"] = st.number_input(
                        label="Maximum Value",
                        min_value=-1.0e6,
                        max_value=1.0e6,
                        value=float(self.cfg["prop-marker-max-val"]),
                        help="Values greater than max value will be presented with the maximum radius size",
                    )
                    if (
                        self.cfg["prop-marker-max-val"]
                        < self.cfg["prop-marker-min-val"]
                    ):
                        (
                            self.cfg["prop-marker-max-val"],
                            self.cfg["prop-marker-min-val"],
                        ) = (
                            self.cfg["prop-marker-min-val"],
                            self.cfg["prop-marker-max-val"],
                        )

                if PROP_MARKER_METHODS.index(self.cfg["prop-marker-method"]) == 1:
                    self.cfg["prop-marker-min-size"] = st.number_input(
                        label="Radius Minimum Size (Points)",
                        min_value=1,
                        max_value=50,
                        value=int(self.cfg["prop-marker-min-size"]),
                    )
                    self.cfg["prop-marker-max-size"] = st.number_input(
                        label="Radius Maximum Size (Points)",
                        min_value=1,
                        max_value=50,
                        value=int(self.cfg["prop-marker-max-size"]),
                    )

                elif PROP_MARKER_METHODS.index(self.cfg["prop-marker-method"]) == 2:
                    pal_options = colors.LINEAR_COLORS_PALETTES
                    id = (
                        par_options.index(self.cfg["prop-marker-palette"])
                        if self.cfg["prop-marker-palette"] in pal_options
                        else 0
                    )
                    self.cfg["prop-marker-palette"] = st.selectbox(
                        label="Prop Marker Palette", options=pal_options, index=id
                    )

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
                label="Group Legend by", options=par_options, index=id
            )
            id = (
                self.aggregation_functions.index(self.cfg["aggregation-func"])
                if self.cfg["aggregation-func"] in self.aggregation_functions
                else 0
            )
            self.cfg["aggregation-func"] = st.selectbox(
                label="Aggregation Function",
                options=self.aggregation_functions,
                index=id,
            )
            self.cfg["save-images"] = st.checkbox(
                label="Save Images", value=self.cfg["save-images"]
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
