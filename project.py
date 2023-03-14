import streamlit as st
import pandas as pd
import os
import json

from phreeqc_simulation import PhreeqcSimulation

from config import (
    SEPARATOR_OPTIONS,
    ENCODING_OPTIONS,
    TYPES,
    MONTH_TO_SEASON,
    SEASON_DICT,
    HEMISPHERE_DICT,
    DEFAULT_CARBONATE_PARAMETERS_DICT,
    ND_FACTOR,
    CalculatorsEnum,
    PARAMETERS_FILE,
    TYPE_CONVERSION_DICT,
    PHREEQC_DATABASE_PATH,
    ConcentrationUnits,
    ExtendedEnum,
    PHREEQC_UNIT_OPTIONS,
    UPLOAD_INSTRUCTIONS,
    DOCUMENTATION_LINK,
)
from helper import ExtendedEnum, show_table, sort_dict_by_value


class PARAMETER_TYPES(ExtendedEnum):
    OBSERVATION = "obs"
    STATION = "station"
    SAMPLE = "sample"


class UnitGroupEnum(ExtendedEnum):
    # dates
    CONCENTRATION = "conc"
    LENGTH = "length"


# system fields are used to identify columns used for specific calculations
class SystemFieldEnum(ExtendedEnum):
    # dates
    SAMPLE_DATE = "sample_date"
    ANALYSIS_DATE = "analysis_date"
    # strings
    STATION_IDENTIFIER = "station_id"
    SAMPLE_IDENTIFIER = "sample_id"
    # numeric fields
    NUM_FIELD = "numeric_parameter"
    WATER_TEMPERATURE = "wa_temp"
    PH = "ph"
    COND = "cond"
    TDS = "tds"
    LONGITUDE = "longitude"
    LATITUDE = "latitude"
    DENSITY = "density"
    # parameters
    CALCIUM = "ca"
    MAGNESIUM = "mg"
    SODIUM = "na"
    POTASSIUM = "k"
    CHLORID = "cl"
    SULFATE = "so4"
    BICARBONATE = "hco3"
    CARBONATE = "co3"
    ALKALINITY = "alk"
    FLUORIDE = "f"
    OXYGEN = "o2"

    YEAR = "year"
    MONTH = "month"
    SEASON = "season"


# List of all implemetented analyses
class AnalysisEnum(ExtendedEnum):
    PIPER = "piper"
    MAP = "map"
    MKTREND = "mktrend"
    STATS = "stats"


class Project:
    """
    The project class implements all functions to import, manage and access
    a dataset.
    """

    def __init__(self):
        # constant parameters for all datasets
        self.system_parameters_df = self.get_system_parameters()
        dict2 = dict(
            zip(self.system_parameters_df.index, self.system_parameters_df["label"])
        )

        self.system_fields_dict = {None: "Not mapped"}
        self.system_fields_dict.update(dict2)
        self.system_fields_dict = sort_dict_by_value(self.system_fields_dict)
        self.parameter_type_list = sorted(
            list(self.system_parameters_df["type"].unique())
        )
        self.chem_parameter_dict = self.get_chem_parameter_dict()
        self.init_demo_dataset()

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def fields_list(self) -> list:
        """Returns a sorted list of all column names for the uploaded dataset

        Returns:
            list: list of fieldnames
        """
        return sorted(list(self.fields.reset_index()["index"]))

    @property
    def first_year(self) -> int:
        """
        Returns the first year of a sample in the dataset, mapped sample date
        column is required.

        Returns:
            int: year of first sample
        """
        if self.sample_date_col:
            return self.data[self.sample_date_col].min().year
        else:
            return 0

    @property
    def last_year(self):
        """
        Returns the last year of a sample in the dataset, mapped sample date
        column is required.

        Returns:
            int: year of first sample
        """
        if self.sample_date_col:
            return self.data[self.sample_date_col].max().year
        else:
            return 0

    @property
    def num_fields(self) -> list:
        """
        Returns a list of numeric fields having the field type float or int.

        Returns:
            list: list of fieldnames
        """
        df = self.fields[self.fields["field_type"].isin(["float", "int"])]
        result = list(df.reset_index()["index"])
        return result

    @property
    def sample_date_col(self) -> str:
        """
        Returns the field which is mapped to the sample_date system-parameter

        Returns:
            str: name in dataset for sample date column
        """
        key = SystemFieldEnum.SAMPLE_DATE.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def sample_identifier_col(self) -> str:
        """
        Returns the column name mapped to the sample-identifier
        system-parameter.

        Returns:
            str: sample identifier column name in dataset
        """
        key = SystemFieldEnum.SAMPLE_IDENTIFIER.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def ph_col(self) -> str:
        """
        Returns the column name mapped to the pH system-parameter

        Returns:
            str: ph column name in dataset
        """
        key = SystemFieldEnum.PH.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    def wa_temp_col(self) -> str:
        """
        Returns the column name mapped to the sample water temperature
        system-parameter

        Returns:
            str: water temperature column name in dataset
        """
        key = SystemFieldEnum.WATER_TEMPERATURE.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def latitude_col(self) -> str:
        """
        Returns the column name mapped to the latitude
        system-parameter

        Returns:
            str: latitude column name in dataset
        """
        key = SystemFieldEnum.LATITUDE.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def longitude_col(self) -> str:
        """
        Returns the column name mapped to the longitude
        system-parameter

        Returns:
            str: longitude column name in dataset
        """
        key = SystemFieldEnum.LONGITUDE.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def stationid_col(self) -> str:
        """
        Returns the station identifier column name

        Returns:
            str: station identifier column name
        """
        key = SystemFieldEnum.STATION_IDENTIFIER.value
        if key in self.system_parameters_dict.keys():
            return self.system_parameters_dict[key]

    @property
    def group_fields(self) -> list:
        """
        Generates a list of all fields mapped as group_field. These fields
        will be available for grouping in plots and as filters in the
        navigation sidebar.

        Returns:
            list: list of group fields
        """
        result = self.fields[
            (
                self.fields["map"].isin(
                    [
                        SystemFieldEnum.STATION_IDENTIFIER.value,
                        SystemFieldEnum.YEAR.value,
                        SystemFieldEnum.MONTH.value,
                        SystemFieldEnum.SEASON.value,
                    ]
                )
            )
            | (self.fields["lookup"])
        ].reset_index()
        if len(result) > 0:
            result = list(result["index"])
        else:
            result = []
        return result

    # -------------------------------------------------------------------------
    # functions
    # -------------------------------------------------------------------------

    def init_demo_dataset(self):
        """
        Initializes the demo dataset. This function is called when initializing
        the project and when the user select the demo dataset as the datasource
        """
        self.datasource = "Demo data"
        self.source_file = "demo.csv"
        self.sep = ";"
        self.encoding = "utf8"
        self.skip_rows = 0
        self.has_nd_data = False
        self.data = pd.read_csv("./data/demo.csv", sep=self.sep)
        # fields holds an field object for every column in the datasset
        # system_parameters_dict: key = system parameter, value = mapped
        #                        column name
        self.fields = self.get_fields()
        self.system_parameters_dict = self.get_system_parameters_dict()

        self.normalize_column_headers()
        self.generate_year = False
        self.generate_month = False
        self.generate_season = False
        self.hemisphere = "n"
        self.default_alkalinity_par = "alk"
        self.data_is_valid = True
        self.analysis_list = []
        self.calculator_list = CalculatorsEnum.list()
        self.codes = self.get_code_lists()

        # includes all information about all analyis (plots, num analyisis and
        # calculators)
        self.analysis_dict = self.get_analysis_dict()
        # includes key and label for plots, meant to fill the plots menu
        self.plot_options_dict = self.get_select_options_dict(analysis_type="plot")
        # idem for analysis
        self.analysis_options_dict = self.get_select_options_dict(
            analysis_type="analysis"
        )
        # idem for calculators
        self.calculator_options_dict = self.get_select_options_dict(
            analysis_type="calculator"
        )

        # columns
        self._sample_date_col = None
        self._sample_identifier_col = None
        self._ph_col = None
        self._wa_temp_col = None

        self.cfg = {}
        self.cfg["phreeqc_database"] = "phreeqc.dat"
        self.cfg["phreeqc_default_unit"] = "mg/L"
        self.phreeqc_databases = self.get_phreeqc_databases()
        self.cfg["phreeqc_map"] = self.get_phreeqc_map()

    def get_chem_parameter_dict(self) -> dict:
        """
        Generates a dict for all chemical having a formula weight. It will be
        used for unit conversions.

        Returns:
            dict: dict with key=parameter name, value= {fmw, valence}
        """
        result = {}
        df = self.system_parameters_df
        df = df[df["formula_weight"] > 0]
        for index, row in df.iterrows():
            result[index] = {"fmw": row["formula_weight"], "valence": row["valence"]}
        return result

    def get_system_parameters(self) -> pd.DataFrame:
        """
        Reads the file ./data/parameters.csv into a dataframe. the fields
        "auto_match_names" contains fieldsnames, that will be recognized and
        matched to system parameters. it is converted from a text to a list

        Returns:
            pd.DataFrame: system parameters.
        """
        df = pd.read_csv(PARAMETERS_FILE, sep=";")
        df["auto_match_names"] = [json.loads(x) for x in list(df["auto_match_names"])]
        return df.set_index("key")

    def get_phreeqc_databases(self) -> list:
        """
        Returns a list of databases found in the the folder ./database.

        Returns:
            list: list of thermosynamic databases
        """
        path = PHREEQC_DATABASE_PATH
        files = [
            file
            for file in os.listdir(path)
            if os.path.isfile(os.path.join(path, file))
        ]
        return sorted(files)

    def get_phreeqc_map(self) -> dict:
        """
        Returns a dict of key 0 master species, value = column name in dataset

        Returns:
            dict: master-species to column name dict
        """
        phreeqc_map = {}
        phr = PhreeqcSimulation(self)
        default_map = {
            "temp": SystemFieldEnum.WATER_TEMPERATURE.value,
            "pH": SystemFieldEnum.PH.value,
            "O(0)": SystemFieldEnum.OXYGEN.value,
            "Ca": SystemFieldEnum.CALCIUM.value,
            "Mg": SystemFieldEnum.MAGNESIUM.value,
            "Na": SystemFieldEnum.SODIUM.value,
            "K": SystemFieldEnum.POTASSIUM.value,
            "Cl": SystemFieldEnum.CHLORID.value,
            "Alkalinity": SystemFieldEnum.ALKALINITY.value,
            "S(6)": SystemFieldEnum.SULFATE.value,
            "F": SystemFieldEnum.FLUORIDE.value,
        }
        for master_species in ["temp", "pH"] + phr.master_species:
            if master_species in default_map:
                phreeqc_map[master_species] = default_map[master_species]
            else:
                phreeqc_map[master_species] = None
        return phreeqc_map

    # not needed anymore
    def get_column_map_obsolete(self) -> dict:
        """
        Returns a dict with all mappable system parameters

        Returns:
            dict: mapping dict with all system parameters, all maps are
            initialized as None
        """

        sf = SystemFieldEnum.list()
        pars = SystemFieldEnum.list()

        result = {x: None for x in sf + pars}
        return result

    def get_analysis_dict(self):
        # set self.default_alkalinity_par if not mapped manually
        #
        result = {
            AnalysisEnum.PIPER.value: {
                "type": "plot",
                "label": "Piper",
                "required_par": [
                    SystemFieldEnum.CALCIUM.value,
                    SystemFieldEnum.MAGNESIUM.value,
                    SystemFieldEnum.SODIUM.value,
                    SystemFieldEnum.CHLORID.value,
                    SystemFieldEnum.SULFATE.value,
                    self.default_alkalinity_par,
                ],
            },
            AnalysisEnum.MAP.value: {
                "type": "plot",
                "label": "Map",
                "required_par": [
                    SystemFieldEnum.LONGITUDE.value,
                    SystemFieldEnum.LATITUDE.value,
                ],
            },
            AnalysisEnum.MKTREND.value: {
                "type": "analysis",
                "label": "Mann Kendall Trend",
                "required_par": [
                    SystemFieldEnum.SAMPLE_DATE.value,
                ],
            },
        }
        for item in result:
            ok = True
            # if required parameters are specified, check if these parameter
            # have been mapped
            if "required_par" in result[item]:
                ok_list = [self.is_mapped(x) for x in result[item]["required_par"]]
                ok = all(ok_list)
            result[item]["has_data"] = ok
        return result

    def get_select_options_dict(self, analysis_type: str) -> list:
        lst = {
            x: self.analysis_dict[x]["label"]
            for x in self.analysis_dict
            if (self.analysis_dict[x]["type"] == analysis_type)
            & (self.analysis_dict[x]["has_data"])
        }
        return lst

    def match_parameter(self, item):
        _df = self.system_parameters_df
        for index, row in _df.iterrows():
            if item in row["auto_match_names"]:
                return index

    def update_field(self, field_name: str, sys_par_name: str):
        self.fields[field_name] = {
            "label": self.system_parameters_df.loc[sys_par_name]["label"],
            "type": self.system_parameters_df.loc[sys_par_name]["type"],
            "unit": self.system_parameters_df.loc[sys_par_name]["default_unit"],
            "map": sys_par_name,
            "phreeqc_ms": self.system_parameters_df.loc[sys_par_name]["phreeqc_ms"],
            "field_type": self.system_parameters_df.loc[sys_par_name]["field_type"],
            "lookup": self.system_parameters_df.loc[sys_par_name]["lookup"],
        }

    def get_fields(self):
        fields = {}
        self.data.columns = [x.lower() for x in self.data.columns]
        for col in self.data.columns:
            match = self.match_parameter(col)
            if match:
                fields[col] = {
                    "label": self.system_parameters_df.loc[match]["label"],
                    "type": self.system_parameters_df.loc[match]["type"],
                    "unit": self.system_parameters_df.loc[match]["default_unit"],
                    "map": match,
                    "phreeqc_ms": self.system_parameters_df.loc[match]["phreeqc_ms"],
                    "field_type": self.system_parameters_df.loc[match]["field_type"],
                    "lookup": self.system_parameters_df.loc[match]["lookup"],
                }
            else:

                column_data_type = TYPE_CONVERSION_DICT[str(self.data[col].dtype)]
                fields[col] = {
                    "label": col,
                    "type": PARAMETER_TYPES.OBSERVATION
                    if column_data_type in ("int64", "float", "float64")
                    else PARAMETER_TYPES.STATION,
                    "unit": None,
                    "map": None,
                    "phreeqc_ms": None,
                    "field_type": column_data_type,
                    "lookup": (column_data_type == "str"),
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

        if sys_name in self.system_parameters_dict.keys():
            return True
        else:
            return False

    def mapped_col_name(self, sys_name: str) -> str:
        # todo
        df = self.fields[self.fields["map"] == sys_name]
        return df.reset_index()["index"]

    def normalize_column_headers(self):
        self.data.columns = [x.lower() for x in self.data.columns]
        for col in self.data.columns:
            if col in [SystemFieldEnum.SAMPLE_DATE.value, "date"]:
                self.data[col] = pd.to_datetime(self.data[col], errors="coerce")
            if self.data[col].dtype == "object":
                self.data[col] = self.data[col].astype(str)

    def convert_nd_data_to_numeric(self, _df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns a dataframe where for each column including non detect values,
        the ND values are converted to 0.5 * detection limit and a second
        column is added with a boolean indicating if a value is a non detect.
        Only columns

        Args:
            _df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: _description_
        """
        for field_name in self.fields_list:
            if (
                (self.fields.loc[field_name, "field_type"] == "float")
                and (self.data[field_name].dtypes != "float64")
                and len(_df[_df[field_name].str.contains("<")]) > 0
            ):
                nd_field = f"{field_name}_nd_"
                _df[nd_field] = False
                _df.loc[_df[field_name].str.contains("<"), nd_field] = True
                _df.loc[_df[field_name].str.contains("<"), field_name] = _df[
                    field_name
                ].str.replace("<", "")
                _df[field_name] = _df[field_name].astype(float, errors="ignore")
                _df.loc[_df[nd_field], field_name] = _df[field_name] * ND_FACTOR
        return _df

    def get_system_parameters_dict(self):
        _df = self.fields[self.fields["map"].notnull()].reset_index()
        result = dict(zip(list(_df["map"]), list(_df["index"])))
        return result

    def refresh_master_data(self):
        """
        Refreshes the metadata and code lists for the current dataset after
        initialisation or loading new data.
        """
        # refresh the system parameters dict as mapping may have changed
        self.system_parameters_dict = self.get_system_parameters_dict()
        self.codes = self.get_code_lists()
        self.analysis_dict = self.get_analysis_dict()

        self.plot_options_dict = self.get_select_options_dict(analysis_type="plot")
        self.analysis_options_dict = self.get_select_options_dict(
            analysis_type="analysis"
        )
        if self.has_nd_data:
            self.data = self.convert_nd_data_to_numeric(self.data)

    def show_upload(self):
        """
        Displays an upload field. If the user uploads a file, the content is
        read and verified. If the file contains the required columns for at
        least 1 analysis method, the new data is assigend to the current
        dataset.
        """

        cols = st.columns(3)
        with cols[0]:
            self.sep = st.selectbox("Separator character", options=SEPARATOR_OPTIONS)
            self.has_nd_data = st.checkbox("Has ND values", value=self.has_nd_data)
        with cols[1]:
            self.encoding = st.selectbox("Encoding", options=ENCODING_OPTIONS)
        with cols[2]:
            self.skip_rows = st.number_input(
                "Skip rows", min_value=0, max_value=50, value=self.skip_rows
            )

        uploaded_file = st.file_uploader("Upload csv file")
        if uploaded_file is not None:
            warning = ""
            # try:
            _df = pd.read_csv(
                uploaded_file,
                sep=self.sep,
                encoding=self.encoding,
                skiprows=self.skip_rows,
            )
            self.data = _df
            st.write(_df)
            self.source_file = uploaded_file.name
            self.normalize_column_headers()
            self.fields = self.get_fields()
            self.system_parameters_dict = self.get_system_parameters_dict()
            self.refresh_master_data()
            # except Exception as ex:
            #    warning = "The uploaded data does not seem to be a CSV file."
            if warning > "":
                warning += """ Check the documentation for the required format or download the demo dataset and format your data accordingly"""
                st.warning(warning)
            else:
                st.success("✅ file was uploaded and verified")

    def get_code_lists(self) -> dict:
        """
        Returns a dictionary for all fields marked as group by where the column name
        is the key and the sorted list of unique values in the this column is the value
        """
        result = {}
        for field in self.group_fields:
            result[field] = sorted(list(self.data[field].unique()))
        return result

    def filter_data(self):
        """
        Filters the self.data dataset according to the filters set in the filters
        section of the sidebar.
        """

        filter = {}
        filtered_df = self.data
        with st.sidebar.expander("🔎Filter", expanded=True):
            if self.codes != {}:
                for code, list in self.codes.items():
                    filter[code] = st.multiselect(label=code.title(), options=list)
                    if filter[code]:
                        filtered_df = filtered_df[filtered_df[code].isin(filter[code])]
        return filtered_df

    def sys_col_name(self, sys_field_name: str) -> str:
        """
        Searches for the field for a given system field (latitude, date etc.)
        and returns the column name.

        Args:
            sys_field_name (str): sys field such as latitude, date, longitude
            or chemical parameter

        Returns:
            str: column name
        """
        df = self.fields.reset_index()
        result = df[df["map"] == sys_field_name]
        return result.iloc[0]["index"]

    def add_field(self, data: dict):
        df = pd.DataFrame.from_dict(data).set_index("col")
        self.fields = pd.concat([self.fields, df])

    def generate_time_columns(self):
        """
        Generates year, month, season-string column based on the sample
        date field depending on the the users input.
        """

        if self.generate_year and "year" not in self.fields_list:
            self.data["year"] = self.data[
                self.sys_col_name(SystemFieldEnum.SAMPLE_DATE.value)
            ].dt.year
            self.add_field(
                {
                    "col": ["year"],
                    "label": ["Year"],
                    "field_type": ["int"],
                    "type": [PARAMETER_TYPES.SAMPLE.value],
                    "map": [SystemFieldEnum.YEAR.value],
                    "lookup": [True],
                }
            )
        if self.generate_month and "month" not in self.fields_list:
            self.data["month"] = self.data[
                self.sys_col_name(SystemFieldEnum.SAMPLE_DATE.value)
            ].dt.month
            self.add_field(
                {
                    "col": ["month"],
                    "label": ["Month"],
                    "field_type": ["int"],
                    "type": [PARAMETER_TYPES.SAMPLE.value],
                    "map": [SystemFieldEnum.MONTH.value],
                    "lookup": [True],
                }
            )
        if self.generate_season and "season" not in self.fields_list:
            self.data["season"] = self.data["month"].apply(
                lambda x: (MONTH_TO_SEASON[x - 1])
            )
            self.data["season_expr"] = self.data["season"].apply(
                lambda x: (SEASON_DICT[self.hemisphere][x])
            )
            self.add_field(
                {
                    "col": ["season"],
                    "label": ["Season"],
                    "field_type": ["str"],
                    "type": [PARAMETER_TYPES.SAMPLE.value],
                    "map": [SystemFieldEnum.SEASON.value],
                    "lookup": [True],
                }
            )

    def get_user_input(self):
        """
        Allows the user to add metadata to each column found in the dataset:
        Column: column name, cannot be changed
        Label: display label for plots and tables
        Group: to which entity does parameter belong
        SystemField: map to an existing system field so the system such as pH, tempo, calcium etc.
        DataType: int, str, float, bool
        LookupCode: whether this is categorical data shown in filters as a selectbox
        """

        def get_key(index, row):
            st.text_input(
                label="index",
                value=index,
                label_visibility="collapsed",
                disabled=True,
                key=index + "0",
            )

        def get_label(index, row):
            self.fields.loc[index, "label"] = st.text_input(
                label=index,
                value=self.fields.loc[index, "label"],
                label_visibility="collapsed",
                key=index + "1",
            )

        def get_group(index, row):
            id = (
                self.parameter_type_list.index(self.fields.loc[index, "type"])
                if self.fields.loc[index, "type"] in self.parameter_type_list
                else 0
            )
            self.fields.loc[index, "type"] = st.selectbox(
                label=index,
                options=self.parameter_type_list,
                label_visibility="collapsed",
                index=id,
                key=index + "2",
            )

        def get_SystemField(index, row):
            keys = list(self.system_fields_dict.keys())
            id = (
                keys.index(self.fields.loc[index, "map"])
                if self.fields.loc[index, "map"] in keys
                else 0
            )
            old_value = self.fields.loc[index, "map"]
            self.fields.loc[index, "map"] = st.selectbox(
                label=index,
                options=keys,
                format_func=lambda x: self.system_fields_dict[x],
                index=id,
                label_visibility="collapsed",
                key=index + "3",
            )
            # if value changed, overwrite all available information for the
            # specified parameter
            if (self.fields.loc[index, "map"] != old_value) & (id > 0):
                self.update_field(index, self.fields.loc[index, "map"])

        def get_data_type(index, row):
            id = (
                TYPES.index(self.fields.loc[index, "field_type"]) + 1
                if self.fields.loc[index, "field_type"] in TYPES
                else 0
            )
            self.fields.loc[index, "field_type"] = st.selectbox(
                label=index,
                options=[None] + TYPES,
                index=id,
                label_visibility="collapsed",
                key=index + "4",
            )

        def get_unit(index, row):
            # field type is string or date: no unit input required: empty
            if self.fields.loc[index, "field_type"] in ["str", "datetime", None]:
                pass
            # field is mapped and has formula weight: concentration: unit selectbox is shown

            elif self.fields.loc[index, "map"] is not None:
                key = self.fields.loc[index, "map"]
                # parameter has formula weight > concentration
                if key in self.chem_parameter_dict:
                    id = (
                        ConcentrationUnits.list().index(self.fields.loc[index, "unit"])
                        + 1
                        if self.fields.loc[index, "field_type"] in TYPES
                        else 0
                    )
                    self.fields.loc[index, "unit"] = st.selectbox(
                        label=index,
                        options=[None] + ConcentrationUnits.list(),
                        index=id,
                        label_visibility="collapsed",
                        key=index + "5",
                    )
                else:
                    self.fields.loc[index, "unit"] = st.text_input(
                        label=index,
                        label_visibility="collapsed",
                        value=self.fields.loc[index, "unit"],
                        key=index + "6",
                    )
            else:
                self.fields.loc[index, "unit"] = st.text_input(
                    label=index,
                    label_visibility="collapsed",
                    value=self.fields.loc[index, "unit"],
                    key=index + "6",
                )

        def get_lookup_code(index, row):
            if self.fields.loc[index, "field_type"] == "str":
                self.fields.loc[index, "lookup"] = st.checkbox(
                    label=index,
                    label_visibility="collapsed",
                    value=self.fields.loc[index, "lookup"],
                    key=index + "7",
                )

        parameter_field_cols = [
            {"index": 0, "title": "Column", "func": get_key},
            {"index": 1, "title": "Label", "func": get_label},
            {"index": 2, "title": "Group", "func": get_group},
            {"index": 3, "title": "System Field", "func": get_SystemField},
            {"index": 4, "title": "Data Type", "func": get_data_type},
            {"index": 5, "title": "Unit", "func": get_unit},
            {"index": 6, "title": "Lookup Code", "func": get_lookup_code},
        ]
        with st.expander("Instructions for uploading your own data"):
            st.markdown(UPLOAD_INSTRUCTIONS.format(DOCUMENTATION_LINK + "data/data/"))
        data_options = ["Demo data", "Upload Datasetf"]
        id = data_options.index(self.datasource)
        self.datasource = st.radio(label="Datasource", options=data_options, index=id)
        if data_options.index(self.datasource) == 1:
            self.show_upload()
        elif id == 1:
            # index = 0 (demo data) and id was set to 1 (uploaded) before:
            # user changed back to the demo dataset
            self.init_demo_dataset()

        with st.expander("Preview Data File", expanded=True):
            st.markdown(f"{len(self.data)} records")
            st.dataframe(self.data)
            st.download_button(
                label="Download Data as CSV",
                data=self.data.to_csv(sep=";").encode("utf-8"),
                file_name="fontus_data.csv",
                mime="text/csv",
            )
        with st.expander("Fields", expanded=False):
            cols = st.columns([2, 2, 1.5, 2, 1, 1, 1])
            all_fields = list(self.fields.reset_index()["index"])
            # show title row
            for item in parameter_field_cols:
                with cols[item["index"]]:
                    st.markdown(item["title"])

            # show fields
            for index, row in self.fields.iterrows():
                cols = st.columns([2, 2, 1.5, 2, 1, 1, 1])
                for field in parameter_field_cols:
                    with cols[field["index"]]:
                        field["func"](index, row)

            if self.is_mapped(SystemFieldEnum.SAMPLE_DATE.value):
                st.markdown("Generate Time Aggregation Columns")
                cols = st.columns([1, 1, 1, 4])
                with cols[0]:
                    self.generate_year = st.checkbox(
                        label="Year column", value=self.generate_year
                    )
                with cols[1]:
                    self.generate_month = st.checkbox(
                        label="Month Column", value=self.generate_month
                    )
                with cols[2]:
                    self.generate_season = st.checkbox(
                        label="Season Column", value=self.generate_season
                    )

        if self.is_mapped("alk") & self.is_mapped("hco3"):
            help_text = """If data includes alkalinity AND HCO3-/CO3--, please specify which parameter is to be used 
            as the carbonate parameter for plots and calculations"""
            id = list(DEFAULT_CARBONATE_PARAMETERS_DICT.keys()).index(
                self.default_alkalinity_par
            )
            self.default_alkalinity_par = st.selectbox(
                "Default carbonate parameter",
                options=list(DEFAULT_CARBONATE_PARAMETERS_DICT.keys()),
                format_func=lambda x: DEFAULT_CARBONATE_PARAMETERS_DICT[x],
                index=id,
                help=help_text,
            )
        with st.expander("PHREEQC Master Species Mapping", expanded=False):
            cols = st.columns(3)
            phr = PhreeqcSimulation(self)
            with cols[0]:
                id = self.phreeqc_databases.index(self.cfg["phreeqc_database"])
                self.cfg["phreeqc_database"] = st.selectbox(
                    label="PHREEQC thermodynamic database",
                    options=self.phreeqc_databases,
                    index=id,
                )
            st.markdown("---")
            with cols[1]:
                id = PHREEQC_UNIT_OPTIONS.index(self.cfg["phreeqc_default_unit"])
                self.cfg["phreeqc_default_unit"] = st.selectbox(
                    label="PHREEQC Default Unit", options=PHREEQC_UNIT_OPTIONS, index=id
                )

            cols = st.columns([1, 2, 1, 2, 1, 2])
            for i in (0, 2, 4):
                with cols[i]:
                    st.markdown("Master Species")
            for i in (1, 3, 5):
                with cols[i]:
                    st.markdown("Project Parameter")
            i = 0
            fld_list = [None] + self.fields_list
            phr_master_species = ["temp", "pH"] + phr.master_species
            for master_species in phr_master_species:
                col = i % (len(cols) / 2)
                with cols[int(col * 2)]:
                    st.text_input(
                        label="",
                        value=master_species,
                        label_visibility="collapsed",
                        disabled=True,
                    )
                with cols[int(col * 2) + 1]:
                    if self.cfg["phreeqc_map"][master_species] in fld_list:
                        id = fld_list.index(self.cfg["phreeqc_map"][master_species])
                    else:
                        id = 0
                    self.cfg["phreeqc_map"][master_species] = st.selectbox(
                        master_species,
                        options=fld_list,
                        index=id,
                        label_visibility="collapsed",
                    )
                i += 1

        if st.button("Apply"):
            self.data = self.convert_nd_data_to_numeric(self.data)
            self.refresh_master_data()
            if self.generate_year or self.generate_month or self.generate_season:
                self.generate_time_columns()
            if self.generate_season:
                cols = st.columns([2, 5])
                with cols[0]:
                    id = list(HEMISPHERE_DICT.keys()).index(self.hemisphere)
                    self.hemisphere = st.selectbox(
                        "Hemisphere",
                        options=list(HEMISPHERE_DICT.keys()),
                        format_func=lambda x: HEMISPHERE_DICT[x],
                        index=id,
                    )
        st.session_state["project"] = self

    def add_pct_columns(self, df: pd.DataFrame, par_dict: dict, pmd) -> pd.DataFrame:
        """
        converts mg/L concentrations to meq/L, meq% to be used in the piper diagram
        and the ion balance.

        Args:
            df (pd.DataFrame):  dataframe in the sample per row format with
                                all major ions columns
            par_dict(dict):     dict holding formula weights

        Returns:
            pd.DataFrame: same dataframe with added columns xx_meqpl,
            xx_meqpct for each major ion
        """
        df = self.calc_meql(df, par_dict, pmd)
        df = self.calc_pct(df)
        df = self.alculate_electroneutrality(df)
        return df

    def major_ions_complete(self, df: pd.DataFrame) -> bool:
        """
        Return wether there are columns for all major ions:
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

    def add_meqpl_columns(self, data: pd.DataFrame, parameters: list):
        """
        Returns a grid with meq converted columns for each item in a
        list of column names. columns must be valid chemcial parameters
        defined in PARAMETERS_DICT, which contains the formula weight and
        valence.

        Args:
            data (pd.DataFrame): grid input to which the converted columns
                                 should be added
            parameters (list):   list of parameter names, included in the input
                                table

        Returns:
            pd.DataFrame: input grid with added converted columns.
        """
        for par in parameters:
            if par in data.columns:
                col = f"{par}_meqpl"
                fact = (
                    1
                    / self.chem_parameter_dict[par]["fmw"]
                    * abs(self.chem_parameter_dict[par]["valence"])
                )
                data.loc[:, col] = data[par] * fact
        return data

    def is_chemical(self, par: str) -> bool:
        """
        A parameter name is a chemical, if it is included in the parameter
        dict.

        Args:
            par (str): column name

        Returns:
            bool: True if the expression is a valid parameter key
        """
        return par in self.chem_parameter_dict.keys()

    def select_records_in_table(self, fields: list = [], height: int = 200):
        """
        Displays a grid with all samples

        Args:
            fields (list, optional): columns from self.data to be shown.
                                     Defaults to [].

        Returns:
            dict: selected row
        """

        if fields == []:
            fields = self.data.reset_index().columns
        else:
            fields = ["index"] + fields

        df = self.data.reset_index()[fields]
        settings = {
            "selection_mode": "single",
            "fit_columns_on_grid_load": True,
            "height": height,
        }
        cols = [{"name": "index", "type": "int", "hide": True}]
        sel_row = show_table(df, cols=cols, settings=settings)
        return sel_row
