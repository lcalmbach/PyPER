import streamlit as st
import pandas as pd

from config import (
    SEPARATOR_OPTIONS,
    ENCODING_OPTIONS,
    PARAMETER_DICT,
    TYPES,
    MONTH_TO_SEASON,
    SEASON_DICT,
    HEMISPHERE_DICT,
)
from helper import is_chemical

SYSTEM_FIELDS = [
    "sample_date",
    "longitude",
    "latitude",
    "group_field",
    "numeric_parameter",
]


class Project:
    def __init__(self):
        self.column_map = {
            "ca": None,
            "mg": None,
            "na": None,
            "k": None,
            "hco3": None,
            "co3": None,
            "alk": None,
            "so4": None,
            "cl": None,
            "latitude": None,
            "longitude": None,
            "ph": None,
            "wtemp": None,
            "date": None,
        }
        self.codes = {}
        self.datasource = 0
        self.sep = ";"
        self.encoding = "utf8"
        self.data = pd.read_csv("./data/demo.csv", sep=self.sep)
        self.normalize_column_headers()
        self.fields = self.get_fields()
        self.generate_year = False
        self.generate_month = False
        self.generate_season = False
        self.hemisphere = 'n'

    @property 
    def fields_list(self):
        return sorted(list(self.fields.reset_index()['index']))

    def get_fields(self):
        fields = {}
        for item in self.data.columns:
            if item in ["date", "sample_date"]:
                fields[item] = {
                    "label": "Sampling Date",
                    "type": "datetime",
                    "digits": 0,
                    "map": "sample_date",
                }
            elif item in ("longitude", "long"):
                fields[item] = {
                    "label": "Longitude",
                    "type": "float",
                    "digits": 4,
                    "map": "longitude",
                }
            elif item in ("latitude", "lat"):
                fields[item] = {
                    "label": "Latitude",
                    "type": "float",
                    "digits": 4,
                    "map": "latitude",
                }
            elif is_chemical(item):
                par = PARAMETER_DICT[item]
                fields[item] = {
                    "label": par["formula"],
                    "type": "float",
                    "digits": 1,
                    "map": item,
                }
            elif self.data[item].dtype == float:
                fields[item] = {
                    "label": item.title(),
                    "type": "float",
                    "digits": 4,
                    "map": "numeric_parameter",
                }
            else:
                fields[item] = {
                    "label": item.title(),
                    "type": "str",
                    "digits": 0,
                    "map": "group_field",
                }
        fields = pd.DataFrame(fields).T
        return fields

    def is_mapped(self, sys_name: str) -> bool:
        """
        Checks whether a system parameter has been mapped and returns
        true/false.

        Args:
            sys_name (str): system parameter such as sample_parameter,
                            latitude, longitude

        Returns:
            bool: true if specified parameter is a column in the file
        """

        # todo
        df = self.fields[self.fields["map"] == sys_name]
        return len(df) == 1

    def normalize_column_headers(self):
        self.data.columns = [x.lower() for x in self.data.columns]
        for col in self.data.columns:
            if col in self.column_map:
                self.column_map[col] = col
            if col in ["sample_date", "date"]:
                self.data[col] = pd.to_datetime(self.data[col])
            if self.data[col].dtype == "object":
                self.data[col] = self.data[col].astype(str)

    def show_upload(self):
        self.sep = st.selectbox("Seperator character", options=SEPARATOR_OPTIONS)
        self.encoding = st.selectbox("Encoding", options=ENCODING_OPTIONS)
        uploaded_file = st.file_uploader("Upload csv file")
        if uploaded_file is not None:
            self.data = pd.read_csv(uploaded_file, sep=self.sep, encoding=self.encoding)
            self.normalize_column_headers()
            self.fields = self.get_fields()

    def group_fields(self) -> list:
        """
        Generates a list of all fields mapped as group_field. These fields will be
        available for grouping in plots and as filters in the navigation sidebar.

        Returns:
            list: list of group fields
        """
        result = self.fields[self.fields["map"] == "group_field"].reset_index()
        result = list(result["index"])
        return result

    def build_code_lists(self):
        for field in self.group_fields():
            self.codes[field] = sorted(list(self.data[field].unique()))

    def filter_data(self):
        filter = {}
        with st.sidebar.expander("🔎Filter", expanded=True):
            for code, list in self.codes.items():
                filter[code] = st.multiselect(code, options=list)
                if filter[code]:
                    self.data = self.data[self.data[code].isin(filter[code])]
        return self.data

    def sys_col_name(self, sys_field_name: str) -> str:
        """
        Searches for the field for a given system field (latitude, date etc.) and
        returns the column name.

        Args:
            sys_field_name (str): sys field such as latitude, date, longitude or
                                  chemical parameter

        Returns:
            str: column name
        """
        df = self.fields.reset_index()
        result = df[df["map"] == sys_field_name]
        return result.iloc[0]["index"]

    def add_field(self, data: dict):
        df = pd.DataFrame.from_dict(data).set_index('col')
        self.fields = pd.concat([self.fields, df])

    def generate_time_columns(self):
        """
        Generates year, month, season-string column based on the sample
        date field depending on the the users input.
        """

        if self.generate_year:
            self.data["year"] = self.data[self.sys_col_name("sample_date")].dt.year
            self.add_field(
                {
                    "col": ["year"],
                    "label": ["Year"],
                    "type": ["int"],
                    "digits": [0],
                    "map": ["group_field"],
                })
        if self.generate_month:
            self.data["month"] = self.data[self.sys_col_name("sample_date")].dt.month
            self.add_field(
                {
                    "col": ['month'],
                    "label": ["Month"],
                    "type": ["int"],
                    "digits": [0],
                    "map": ["group_field"],
                })
        if self.generate_season:
            self.data['season'] = self.data['month'].apply(lambda x: (MONTH_TO_SEASON[x-1]))
            self.data['season_expr'] = self.data['season'].apply(lambda x: (SEASON_DICT[self.hemisphere][x]))
            self.add_field(
                {
                    "col": ['season'],
                    "label": ["Season"],
                    "type": ["str"],
                    "digits": [0],
                    "map": ["group_field"],
                })

    def get_user_input(self):
        data_options = ["Demo data", "Upload dataset"]
        self.datasource = st.radio(
            label="Data", options=data_options, index=self.datasource
        )
        self.datasource = data_options.index(self.datasource)
        if self.datasource > 0:
            self.show_upload()
        with st.expander("Preview data", expanded=True):
            st.markdown(f"{len(self.data)} records")
            st.write(self.data)
            st.download_button(
                label="Download data as CSV",
                data=self.data.to_csv(sep=";").encode("utf-8"),
                file_name="fontus_data.csv",
                mime="text/csv",
            )

        with st.expander("Fields", expanded=True):
            cols = st.columns([2, 2, 1, 2, 2, 2])
            with cols[0]:
                st.markdown("Column name")
                for col in list(self.fields.reset_index()["index"]):
                    st.text_input(
                        label=" ",
                        value=col,
                        label_visibility="collapsed",
                        disabled=True,
                        key=col + "0",
                    )
            with cols[1]:
                st.markdown("Label")
                for col in list(self.fields.reset_index()["index"]):
                    self.fields.loc[col, "label"] = st.text_input(
                        label=" ",
                        value=self.fields.loc[col, "label"],
                        label_visibility="collapsed",
                        key=col + "1",
                    )
            with cols[2]:
                st.markdown("Digits")
                for col in list(self.fields.reset_index()["index"]):
                    self.fields.loc[col, "digits"] = st.number_input(
                        label=" ",
                        value=self.fields.loc[col, "digits"],
                        label_visibility="collapsed",
                        key=col + "2",
                    )
            with cols[3]:
                st.markdown("Map")
                map_fields = SYSTEM_FIELDS + list(PARAMETER_DICT.keys())
                for col in list(self.fields.reset_index()["index"]):
                    id = map_fields.index(col) + 1 if col in map_fields else 0
                    self.fields.loc[col, "map"] = st.selectbox(
                        label=" ",
                        options=[None] + map_fields,
                        index=id,
                        label_visibility="collapsed",
                        key=col + "3",
                    )
            with cols[4]:
                st.markdown("Type")
                for col in list(self.fields.reset_index()["index"]):
                    id = (
                        TYPES.index(self.fields.loc[col, "type"]) + 1
                        if self.fields.loc[col, "type"] in TYPES
                        else 0
                    )
                    self.fields.loc[col, "type"] = st.selectbox(
                        label=" ",
                        options=[None] + TYPES,
                        index=id,
                        label_visibility="collapsed",
                        key=col + "4",
                    )

            if self.is_mapped("sample_date"):
                st.markdown("Generate time aggregation columns")
                cols = st.columns([1, 1, 1, 4])
                with cols[0]:
                    self.generate_year = st.checkbox(
                        label="Year column", value=self.generate_year
                    )
                with cols[1]:
                    self.generate_month = st.checkbox(
                        label="Month column", value=self.generate_month
                    )
                with cols[2]:
                    self.generate_season = st.checkbox(
                        label="Season column", value=self.generate_season
                    )
                if self.generate_year or self.generate_month or self.generate_season:
                    self.generate_time_columns()
                if self.generate_season:
                    cols = st.columns([2,5])
                    with cols[0]:
                        id = list(HEMISPHERE_DICT.keys()).index(self.hemisphere)
                        self.hemisphere = st.selectbox('Hemisphere',
                                    options=list(HEMISPHERE_DICT.keys()),
                                    format_func=lambda x: HEMISPHERE_DICT[x],
                                    index=id)
        self.build_code_lists()
        self.data = self.filter_data()
        st.session_state["project"] = self
