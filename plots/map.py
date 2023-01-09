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
from project import Project, LONGITUDE, LATITUDE
import colors
from plots.fontus_plot import FontusPlot


class Map(FontusPlot):
    def __init__(self, prj: Project):
        super().__init__(prj, type="map")
        self.cfg["x_col"] = "_x"
        self.cfg["y_col"] = "_y"

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
        tooltips = {}
        field_list = prj.fields_list
        for field in field_list:
            tooltips[field] = field in self.project.group_fields

        return tooltips

    def init_data(self, df):
        self.data = df

    def wgs84_to_web_mercator_df(
        self, df: pd.DataFrame, lon: str, lat: str
    ) -> pd.DataFrame:
        """Projection of lat/long to x/y

        Args:
            df (pd.DataFrame): input dataframe
            lon (str): longitude column name
            lat (str): latitude  column name

        Returns:
            pd.DataFrame: output dataframe holding new x/y columns
        """

        k = 6378137
        df[self.cfg["x_col"]] = df[lon] * (k * np.pi / 180.0)
        df[self.cfg["y_col"]] = np.log(np.tan((90 + df[lat]) * np.pi / 360.0)) * k

        return df

    def get_map_rectangle(self, df):
        x_min = df[self.cfg["x_col"]].min()
        x_max = df[self.cfg["x_col"]].max()
        y_min = df[self.cfg["y_col"]].min()
        y_max = df[self.cfg["y_col"]].max()
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
        # todo: make sure that all_fields does not contain None
        if None in all_fields:
            all_fields.remove(None)
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
        def get_title() -> Title:
            """
            Transforms the settings and returns a bokeh plot title object.

            Returns:
                Title: formatted bokeh title object
            """

            title = Title()
            placeholder = f"{{{self.cfg['group-plot-by']}}}"
            if placeholder in self.cfg["plot-title"]:
                value = str(df.iloc[0][self.cfg["group-plot-by"]])
                title.text = self.cfg["plot-title"].replace(placeholder, value)
            else:
                title.text = self.cfg["plot-title"]
            title.text_font_size = f"{self.cfg['plot-title-text-size']}em"
            title.align = self.cfg["plot-title-align"]

        tooltips, formatters = self.get_tooltips()
        plot_df = self.aggregate_data(self.data)
        plot_df = self.wgs84_to_web_mercator_df(
            plot_df, self.project.longitude_col, self.project.latitude_col
        )
        tile_provider = get_provider(xyz.OpenStreetMap.Mapnik)
        x_min, y_min, x_max, y_max = self.get_map_rectangle(plot_df)

        p = figure(
            x_range=(x_min, x_max),
            y_range=(y_min, y_max),
            x_axis_type="mercator",
            y_axis_type="mercator",
            width=int(self.cfg["plot-width"]),
            height=int(self.cfg["plot-height"]),
            tooltips=tooltips,
        )
        if self.cfg["plot-title"] != "":
            p.title = get_title()

        p.add_tools(
            HoverTool(
                tooltips=tooltips,
                formatters=formatters,
            ),
        )
        p.add_tile(tile_provider)
        p = self.add_markers(p, plot_df)
        p = self.add_legend(p)
        return p

    def get_user_input(self):
        data = self.project.filter_data()
        if st.session_state["project"] == self.project:
            self.init_data(data)
        else:
            self.project = st.session_state["project"]

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
                "Plot Title Alignment", options=HORIZONTAL_ALIGNEMENT_OPTIONS, index=id
            )
            id = group_by_options.index(self.cfg["group-plot-by"])
            self.cfg["group-plot-by"] = st.selectbox(
                "Group Plot By", options=group_by_options, index=id
            )
            id = group_by_options.index(self.cfg["color"])
            self.cfg["color"] = st.selectbox(
                "Group Legend by", options=group_by_options, index=id
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
                "Marker Generator Algorithm", options=colors.MARKER_GENERATORS, index=id
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

        with st.expander("**Tooltips**", expanded=True):
            if self.cfg["tooltips"] != self.project.fields_list:
                self.cfg["tooltips"] = self.init_tooltips(self.project)
            for key, row in self.project.fields.iterrows():
                self.cfg["tooltips"][key] = st.checkbox(
                    f"Show {row['label']}",
                    value=self.cfg["tooltips"][key],
                    key=key + "cb",
                )
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
            lblc_options = [None, "black", "grey", "darkgrey", "silver"]
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
                label="Border-Line Opacity",
                min_value=0.0,
                max_value=1.0,
                value=float(self.cfg["legend-background-fill-alpha"]),
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
                st.write(df)
                st.download_button(
                    label="Download data as CSV",
                    data=df.to_csv(sep=";").encode("utf-8"),
                    file_name="fontus_piper_data.csv",
                    mime="text/csv",
                    key=f"save_button_{random_string(5)}",
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
        Shows one map plot if group plots by is None, otherwise a plot is shown for each
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
                    df_aggregated = self.aggregate_data(df_filtered)
                    if len(df_aggregated) > 0:
                        p = self.get_plot(df_aggregated)
                        st.bokeh_chart(p)
                        self.show_data(df_aggregated)
                        if self.cfg["save-images"]:
                            self.create_image_file(p)
            else:
                df_aggregated = self.aggregate_data(self.data)
                p = self.get_plot(df_aggregated)
                st.bokeh_chart(p)
                self.show_data(self.data)
                if self.cfg["save-images"]:
                    self.create_image_file(p)
            if self.cfg["save-images"] & len(self.images) > 0:
                with st.sidebar:
                    self.show_download_button()

    # --------------------------

    def get_locations_map_cfg(self, cfg, df):
        with st.sidebar.expander(f"⚙️ {lang['settings']}"):
            id = (
                list(MarkerType).index(cfg["marker"])
                if (cfg["marker"] in MarkerType)
                else 0
            )
            cfg["marker"] = st.selectbox(
                lang["marker"], options=list(MarkerType), index=id
            )
            cfg["marker_color"] = st.color_picker(
                lang["marker_color"], value=cfg["marker_color"]
            )
            cfg["marker-size"] = st.number_input(
                lang["marker-size"], value=cfg["marker-size"]
            )
            cols = st.columns(2)
            with cols[0]:
                cfg["plot-width"] = st.number_input(
                    lang["plot-width"],
                    min_value=100,
                    max_value=2000,
                    value=cfg["plot-width"],
                )
            with cols[1]:
                cfg["plot-height"] = st.number_input(
                    lang["plot-height"],
                    min_value=100,
                    max_value=2000,
                    value=cfg["plot-height"],
                )
        return cfg

    def get_parameter_map_cfg(self, cfg, df):
        with st.sidebar.expander(f"⚙️ {lang['settings']}"):
            lst_options = [lang["color"], lang["size"]]
            cfg["prop-size-method"] = st.radio(
                label=lang["prop_color_size"], options=lst_options
            ).lower()
            stat_functions_dict = {
                "mean": lang["mean"],
                "min": lang["min"],
                "max": lang["max"],
            }
            cfg["aggregation"] = st.radio(
                label=lang["aggregation"],
                options=list(stat_functions_dict.keys()),
                format_func=lambda x: stat_functions_dict[x],
                help=lang["aggregation_station_help"],
            ).lower()
            max_val = df[cn.VALUE_NUM_COL].mean() + df[cn.VALUE_NUM_COL].std() * 2
            cfg["max_value"] = st.number_input(label=lang["max_value"], value=max_val)
            cols = st.columns(2)
            with cols[0]:
                cfg["width"] = st.number_input("Width (px)", cfg["plot-width"])
            with cols[1]:
                cfg["height"] = st.number_input("Height (px)", cfg["plot-height"])

            if cfg["prop-size-method"] == lang["size"].lower():
                cfg["max_prop_size"] = st.number_input(
                    label=lang["max_radius"], value=cfg["max_prop_size"]
                )
                cfg["min_prop_size"] = st.number_input(
                    label=lang["min_radius"], value=cfg["min_prop_size"]
                )
            else:
                cfg["lin_palette"] = st.selectbox(
                    label=lang["min_radius"], options=helper.bokeh_palettes((256))
                )
                cfg["marker-size"] = st.number_input(
                    label=lang["marker-size"],
                    min_value=1,
                    max_value=50,
                    value=int(cfg["marker-size"]),
                )
            cfg["marker-fill-alpha"] = st.number_input(
                label=lang["marker-fill-alpha"],
                min_value=0.1,
                max_value=1.0,
                step=0.1,
                value=float(cfg["marker-fill-alpha"]),
            )
        return cfg

    """
    def show_parameters_map(self):
        cfg = st.session_state.user.read_config(cn.MAP_ID, "default")
        cfg["parameter"] = helper.get_parameter(
            cfg["parameter"], label="Parameter", filter=""
        )
        # here its broken
        df = st.session_state.project.get_observations([cfg["parameter"]], [])
        filter_fields = ["station", "date", "value"]
        # df = show_filter(df, filter_fields, cfg)
        # df = pd.merge(df, st.session_state.project.stations_df, on=cn.STATION_IDENTIFIER_COL)
        cfg = get_parameter_map_cfg(cfg, df)
        map = Map(df, cfg)
        p = map.get_plot()
        dic = {"min": lang["min"], "max": lang["max"], "mean": lang["mean"]}
        st.markdown(
            f"**{cfg['group-legend-by']}, {dic[cfg['aggregation']]} value for each station.**"
        )
        st.bokeh_chart(p)
        # helper.show_save_file_button(p, 'key1')
        st.session_state.user.save_config(cn.MAP_ID, "default", cfg)
    """

    def show_menu():
        set_lang()
        menu_options = lang["menu_options"]
        menu_action = st.sidebar.selectbox(label=lang["options"], options=menu_options)

        if menu_action == menu_options[0]:
            show_locations_map()
        elif menu_action == menu_options[1]:
            show_parameters_map()
