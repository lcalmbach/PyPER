# from const import MP # not sure what it is...
import streamlit as st
import pandas as pd
import numpy as np
import xyzservices.providers as xyz
from bokeh.tile_providers import get_provider
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure
# from bokeh.models import (
    # Label,
    # GMapOptions,
    # HoverTool,
    # Arrow,
    # NormalHead,
    # ColumnDataSource,
    # LinearColorMapper,
# )
from bokeh.models.annotations import Title
from zipfile import ZipFile
import os
from helper import get_random_filename, flash_text, random_string
from config import TEMP_FOLDER, AggregationFunc
from project import Project, SystemFieldEnum
from plots.fontus_plot import FontusPlot


class Map(FontusPlot):
    def __init__(self, prj: Project):
        super().__init__(prj, type="map")
        self.cfg["x_col"] = "_x"
        self.cfg["y_col"] = "_y"
        self.cfg["aggregation-func"] = AggregationFunc.MEAN.value

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
        """
        Projection of lat/long to x/y

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
        tooltip fields aggregated by the selected aggregation method (count, mean
        min, max, std)

        Args:
            data (pd.DataFrame): raw data with n rows per station

        Returns:
            pd.DataFrame: dataframe with 1 row per station and fields reduced to
                          long, lat, tooltips
        """

        if self.cfg["group-legend-by"]:
            self.cfg["tooltips"][self.cfg["group-legend-by"]] = True
        if self.cfg["prop-marker-parameter"]:
            self.cfg["tooltips"][self.cfg["prop-marker-parameter"]] = True
        
        all_fields = [
            self.project.longitude_col,
            self.project.latitude_col,
        ] + self.tooltip_fields
        # todo: make sure that all_fields does not contain None
        all_fields = list(filter(None, all_fields))
        lat_long_list = [self.project.longitude_col, self.project.latitude_col]
        group_fields = lat_long_list + [
            x for x in self.tooltip_fields if x in self.project.group_fields
        ]
        group_fields = list(filter(None, group_fields))
        # includes fields selected in tooltips only
        group_fields = [x for x in group_fields if x in all_fields]
        num_fields = self.project.num_fields
        num_fields = list(filter(None, num_fields))
        num_fields = [x for x in num_fields if (x in all_fields) and not(x in lat_long_list)]

        _df = data[all_fields]
        if len(num_fields) == 2:
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

        
        p.add_tile(tile_provider)
        p = self.add_markers(p, plot_df)
        p = self.add_legend(p)
        return p

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
