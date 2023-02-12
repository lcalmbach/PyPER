import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import numpy as np
import pymannkendall as mk
from datetime import datetime

import config as cn
import altair as alt
from project import Project, SystemFieldEnum
from helper import show_table, get_domain, time_lin_reg

lang = {}
PREDICT_CASE_OPTIONS = [
    "None",
    "Predict time when specified value is reached",
    "Predict value for specified time",
]


def set_lang():
    global lang
    # lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


class MannKendall:
    def __init__(self, prj):
        self.project = prj
        self.data = prj.data
        self.group_by_options = [None] + self.project.group_fields
        self.parameter_options = [None] + self.project.num_fields
        self.cfg = {}
        self.cfg["show-sen-trend"] = False
        self.cfg["show-regression"] = True
        self.cfg["auto-run"] = True
        self.cfg["group-by-param"] = (
            None if len(self.group_by_options) == 1 else self.group_by_options[1]
        )
        self.cfg["parameter"] = "ca"
        self.cfg["alpha"] = 0.05
        self.cfg["show-time-series-plot"] = False
        self.cfg["min-points"] = 8
        self.cfg["hide-samples-with-unsufficient-points"] = True
        self.cfg["predict_case"] = 0
        self.cfg["auto-run"] = False
        self.cfg['y_domain'] = [0.0, 0.0]
        self.data = pd.DataFrame()
        self.selection_df = pd.DataFrame()

    def execute_trend_analysis(self):
        def mk_res2df(res):
            df = pd.DataFrame(
                data={
                    "par": [
                        "alpha",
                        "trend-result",
                        "p-value",
                        "z",
                        "Tau",
                        "s",
                        "slope",
                        "intercept",
                    ],
                    "value": [
                        self.cfg["alpha"],
                        res.trend,
                        res.p,
                        res.z,
                        res.Tau,
                        res.s,
                        res.slope,
                        res.intercept,
                    ],
                }
            )
            return df

        if self.cfg["group-by-param"]:
            group_par = self.cfg["group-by-param"]
            groups = list(self.selection_df[group_par])
            self.cfg["auto-run"] = False
            for group in groups:
                self.cfg["title"] = f"{group_par}: {group}"
                df_filtered = self.data[self.data[group_par] == group]
                if len(df_filtered) >= self.cfg["min-points"]:
                    values = list(df_filtered[self.cfg["parameter"]])
                    res = mk.original_test(values, alpha=self.cfg["alpha"])
                    lin_reg = time_lin_reg(
                        df_filtered,
                        self.project.sample_date_col,
                        self.cfg["parameter"],
                    )
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "trend"
                    ] = res.trend
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "p"
                    ] = res.p
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "tau"
                    ] = res.Tau
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "z"
                    ] = res.z
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "s"
                    ] = res.s
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group,
                        "sen_slope",
                    ] = res.slope
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group,
                        "sen_intercept",
                    ] = res.intercept
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group,
                        "regr_intercept",
                    ] = lin_reg.intercept
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group,
                        "regr_slope",
                    ] = lin_reg.slope
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group,
                        "regr_rvalue",
                    ] = lin_reg.rvalue
                else:
                    self.selection_df.loc[
                        self.selection_df[self.cfg["group-by-param"]] == group, "trend"
                    ] = "Unsufficient data"
        else:
            pass

    def get_group_by_options(self):
        group_fields = [None]
        if self.project.is_mapped(SystemFieldEnum.STATION_IDENTIFIER.value):
            group_fields = group_fields + [SystemFieldEnum.STATION_IDENTIFIER.value]
        group_fields = group_fields + self.project.group_fields
        st.write(group_fields)
        return group_fields

    def show_details(self, results):
        cols = {}
        settings = {
            "height": len(results) * cn.AGG_GRID_COL_HEIGHT,
            "selection_mode": "single",
            "fit_columns_on_grid_load": True,
        }

        group = results[results["parameter"] == self.cfg["group-by-param"]].iloc[0][
            "value"
        ]
        res = results[results["parameter"] == "trend"].iloc[0]["value"]
        sen_slope = results[results["parameter"] == "sen_slope"].iloc[0]["value"]
        sen_intercept = results[results["parameter"] == "sen_intercept"].iloc[0][
            "value"
        ]
        title = f"{self.cfg['group-by-param']}: {group}, trend: {res}"
        df = self.data[self.data[self.cfg["group-by-param"]] == group].sort_values(
            by=self.project.sample_date_col
        )
        st.markdown(f"**{title}**")
        columns = st.columns([1, 3])
        with columns[0]:
            show_table(results, cols, settings)

        with columns[1]:
            df["t0"] = df.iloc[0][self.project.sample_date_col]
            df["t_diff"] = df[self.project.sample_date_col] - df["t0"]
            df["t_diff"] = df["t_diff"] / pd.to_timedelta(1, unit="D")
            days = df.iloc[-1]["t_diff"]
            # sen slope is calculated dimensionless on the time-sorted values. therefore
            # the slope must be adjusted to reflect daily deltas
            if sen_slope != None:
                sen_slope = sen_slope / days * len(df)
                df["trend_line"] = float(sen_intercept) + df["t_diff"] * sen_slope
            else:
                df["trend_line"] = 0

            plot_cfg = {
                "show-sen-trend": self.cfg["show-sen-trend"],
                "show-regression": self.cfg["show-regression"],
            }
            self.show_time_series_plot(df, plot_cfg)
        with st.expander("View Values"):
            cols = {}
            settings = {
                "height": len(df) * cn.AGG_GRID_COL_HEIGHT,
                "max_height": 600,
                "selection_mode": "single",
                "fit_columns_on_grid_load": False,
            }
            fields = [self.project.sample_date_col, self.cfg["parameter"]]
            show_table(df[fields], cols, settings)
            st.download_button(
                label="Download Data as CSV",
                data=df[fields].to_csv(sep=";", index=False).encode("utf-8"),
                file_name="fontus_data.csv",
                mime="text/csv",
            )

        # self.cfg["prj_parameter"] = helper.get_parameter(self.cfg["prj_parameter"])
        # parameter = self.cfg["parameter"]
        # self.cfg["stations"] = helper.get_stations(self.cfg["stations"], "")
        # df = self.project.time_series(self.cfg["prj_parameter"], cfg["stations"])

    def show_time_series_plot(self, df: pd.DataFrame, cfg: dict):
        x_domain = [
            f"{df[self.project.sample_date_col].min().year}-01-01",
            f"{df[self.project.sample_date_col].max().year}-12-31",
        ]
        if self.cfg['y_domain'] != [0, 0]:
            y_domain = self.cfg['y_domain']
        else:
            y_domain = get_domain(df, self.cfg["parameter"])
        chart = (
            alt.Chart(df)
            .mark_line(width=20, point=alt.OverlayMarkDef(color="blue", opacity=0.6))
            .encode(
                x=alt.X(
                    f"{self.project.sample_date_col}:T",
                    # scale=alt.Scale(domain=x_domain),
                    axis=alt.Axis(title=""),
                ),
                y=alt.Y(f"{self.cfg['parameter']}:Q", scale=alt.Scale(domain=y_domain)),
                tooltip=[
                    f"{self.project.sample_date_col}:T",
                    f"{self.cfg['parameter']}:Q",
                ],
            )
        )
        regr_line = chart.transform_regression(
            f"{self.project.sample_date_col}", self.cfg["parameter"]
        ).mark_line(color="green")

        trend_line = (
            alt.Chart(df)
            .mark_line(width=20, strokeDash=[1, 1], color="magenta")
            .encode(
                x=alt.X(f"{self.project.sample_date_col}:T"), y=alt.Y("trend_line:Q")
            )
        )

        if cfg["show-regression"]:
            chart += regr_line
        if cfg["show-sen-trend"]:
            chart += trend_line

        chart = (chart).properties(width=800, height=300)
        st.altair_chart(chart)

    def get_user_input(self):
        with st.expander("Mann Kendall Test Properties", expanded=True):
            id = (
                self.group_by_options.index(self.cfg["group-by-param"])
                if self.cfg["group-by-param"] in self.group_by_options
                else 0
            )
            self.cfg["group-by-param"] = st.selectbox(
                "Group by Parameter", options=self.group_by_options, index=id
            )

            if self.cfg["parameter"] in self.parameter_options:
                id = self.parameter_options.index(self.cfg["parameter"])
            else:
                id = 0
            self.cfg["parameter"] = st.selectbox(
                label="Analysis Parameter",
                options=self.parameter_options,
                index=id
            )

            options = ["Detail", "Summary"]
            x = st.radio(label="Output", options=options)
            self.cfg["output"] = options.index(x)

            self.cfg["auto-run"] = st.checkbox(
                label="Auto Run Analysis", value=self.cfg["auto-run"]
            )
            if self.cfg["output"] == 0:
                self.cfg["show-sen-trend"] = st.checkbox(
                    label="Show Sen's Line", value=self.cfg["show-sen-trend"]
                )
                self.cfg["show-regression"] = st.checkbox(
                    label="Show Regression Line", value=self.cfg["show-regression"]
                )
            self.cfg["min-points"] = st.number_input(
                "Minimum Number of Points",
                min_value=int(4),
                max_value=int(1e6),
                value=self.cfg["min-points"],
            )
            self.cfg["hide-samples-with-unsufficient-points"] = st.checkbox(
                "Hide samples with unsufficient points",
                value=self.cfg["hide-samples-with-unsufficient-points"],
            )
            self.cfg["predict_case"] = st.selectbox(
                "Prediction type",
                options=PREDICT_CASE_OPTIONS,
                index=self.cfg["predict_case"],
            )
            st.markdown('---')
            st.markdown('Time series plot options')
            cols = st.columns([1, 1, 3])
            with cols[0]:
                self.cfg['y_domain'][0] = st.number_input(
                    "Y-Axis Start",
                    min_value=float(0),
                    max_value=float(1e9),
                    value=self.cfg['y_domain'][0],
                )
            with cols[1]:
                self.cfg['y_domain'][1] = st.number_input(
                    "Y-Axis End",
                    min_value=float(0),
                    max_value=float(1e9),
                    value=self.cfg['y_domain'][1],
                )



    def get_summary_table_data(self):
        """
        returns a data table including timestamp and value and a selection 
        table consisting of all group fields, station id and sample-date

        Returns:
            pd.DataFrame: data table
            pd.DataFrame: selection table used to select a station
        """
        if self.cfg["group-by-param"]:
            fields = [
                self.project.sample_date_col,
                self.cfg["parameter"],
                self.cfg["group-by-param"]
            ]
        else:
            fields = [
                self.project.sample_date_col,
                self.cfg["parameter"]
            ]
        data = self.project.data[fields].dropna(axis=0)
        if self.year_selection != (self.project.first_year, self.project.last_year):
            data = data[
                (data[self.project.sample_date_col].dt.year >= self.year_selection[0])
                & (
                    data[self.project.sample_date_col].dt.year
                    <= self.year_selection[1]
                )
            ]
        if self.cfg["group-by-param"]:
            grouped_df = (
                data.groupby(by=[self.cfg["group-by-param"]])
                .agg(["count", "min", "max"])
                .reset_index()
            )
            grouped_df.columns = [
                self.cfg["group-by-param"],
                "count",
                "start_date",
                "end_date",
                "cnt_par",
                f"min_{self.cfg['parameter']}",
                f"max_{self.cfg['parameter']}",
            ]
            # remove count of parameter
            grouped_df = grouped_df[
                [
                    self.cfg["group-by-param"],
                    "count",
                    "start_date",
                    "end_date",
                    f"min_{self.cfg['parameter']}",
                    f"max_{self.cfg['parameter']}",
                ]
            ]
            grouped_df["num_years"] = (
                grouped_df["end_date"] - grouped_df["start_date"]
            ) / np.timedelta64(1, "Y").astype(int)
            if self.cfg["hide-samples-with-unsufficient-points"]:
                grouped_df = grouped_df.query(f"count>={self.cfg['min-points']}")
        else:
            data["_group"] = "x"
            grouped_df = data.groupby(by=["_group"]).agg(["count", "min", "max"]).T

        return data, grouped_df

    def show_sidebar_settings(self):
        with st.sidebar.expander("Filter", expanded=True):
            self.year_selection = st.slider(
                "Date",
                min_value=self.project.first_year,
                max_value=self.project.last_year,
                value=(self.project.first_year, self.project.last_year),
            )

    def show(self):
        self.show_sidebar_settings()
        if (self.cfg["auto-run"]) or (len(self.data) == 0):
            ok = True
        else:
            ok = False
            ok = st.sidebar.button("Run analysis")
        if ok:
            self.data, self.selection_df = self.get_summary_table_data()
            self.execute_trend_analysis()

        par = self.cfg["parameter"]
        st.markdown(f"### Mann Kendall Analysis, Parameter = {par}")
        settings = {
            "selection_mode": "multiple",
            "fit_columns_on_grid_load": True,
            "height": 300
        }
        cols = [
            {"name": "p", "type": "number", "precision": 3, "hide": False},
            {"name": "z", "type": "float", "precision": 5, "hide": True},
            {"name": "s", "type": "float", "precision": 5, "hide": True},
            {"name": "tau", "type": "float", "precision": 5, "hide": True},
            {"name": "sen_slope", "type": "float", "precision": 5, "hide": True},
            {"name": "sen_intercept", "type": "float", "precision": 5, "hide": True},
            {"name": "regr_slope", "type": "float", "precision": 5, "hide": True},
            {"name": "regr_intercept", "type": "float", "precision": 5, "hide": True},
            {"name": "regr_rvalue", "type": "float", "precision": 5, "hide": True},
            {"name": "alpha", "type": "float", "precision": 5, "hide": True},
        ]
        sel_rows = show_table(self.selection_df, cols=cols, settings=settings)
        result_fields = [
            self.cfg["group-by-param"],
            "count",
            "trend",
            "p",
            "z",
            "s",
            "tau",
            "sen_slope",
            "sen_intercept",
            "regr_slope",
            "alpha",
            "regr_intercept",
            "regr_slope",
            "regr_rvalue",
        ]
        if len(sel_rows) > 0 & (not self.cfg["auto-run"]):
            for index, row in sel_rows.iterrows():
                results = pd.DataFrame(row).reset_index()
                results = results[results["index"].isin(result_fields)]
                results.columns = ["parameter", "value"]
                self.show_details(results)
