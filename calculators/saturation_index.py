import math
import pandas as pd
import streamlit as st
from chempy import Substance
from chempy.util import periodic

from helper import show_table
from project import Project, SystemFieldEnum
from phreeqc_simulation import PhreeqcSimulation

UNIT_OPTIONS = ["mmol/L", "mg/L", "ppm"]
BASE_PARAMETERS_UNITS = {"pH": "", "temp": "°C", "density": "kg/m3"}


class SaturationIndex:
    """
    Calculator allows to calculate the saturation index of a given solution
    for one of several minerals.
    """

    def __init__(self, prj: Project):
        self.project: Project = prj
        self.cfg = {}
        self.input_options = ["Select sample from dataset", "Enter data manually"]
        self.title = "PHREEQC Simulation"
        self.has_required_input = self.get_has_required_input()
        self.input = (
            self.input_options[0] if self.has_required_input else self.input_options[1]
        )
        self.phreeqc = PhreeqcSimulation(self.project)
        self.minerals_options = self.phreeqc.phases
        self.phreeqc_map = self.get_phreeqc_map()
        self.select_table_fields = self.get_select_table_fields()

    def get_phreeqc_map(self) -> dict:
        """
        Filters the project.phreeqc to dataset map for all master species 
        present in the dataset.

        Returns:
            dict: filtered dict
        """
        return {k:v for (k,v) in self.project.cfg["phreeqc_map"].items() if v != None}

    def get_has_required_input(self) -> bool:
        """Verifies if dataset includes required parameters

        Returns:
            bool: true if data includes ca, mg, na
        """

        ok = self.project.is_mapped(SystemFieldEnum.CALCIUM.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.MAGNESIUM.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.SODIUM.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.CHLORID.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.SULFATE.value)
        return ok

    def get_select_table_fields(self) -> list:
        """Generates the list of parameters to be shown to the user to select from
        The list contains fields marked as group fields, then sample date, sample id
        ca, mg, na, hco3 if present, alk if present.

        Returns:
            list: field list reduced to required fields
        """
        fields = self.project.group_fields
        if self.project.is_mapped(SystemFieldEnum.SAMPLE_DATE.value):
            fields.append(self.project.sample_date_col)
        if self.project.is_mapped(SystemFieldEnum.SAMPLE_IDENTIFIER.value):
            fields.append(self.project.sample_identifier_col)

        fields = fields + list(self.phreeqc_map.values())
        return fields

    def show_result(self, solution: dict):
        """
        Displays the solution dict input in a form and a multiselectbox
        to select minerals for which the SI is to be calculated. For manual
        input the dict is empty and must be filled by the user. For selection
        from the grid, the dict is filled with values for the selected samples.

        Args:
            solution (dict): master species value dict for solution for which 
                             SI is to be calculated.
        """
        si = pd.DataFrame()
        with st.expander("Solution Input", expanded=True):
            cols = st.columns(3)
            rows = len(solution) // 3
            row, col = 0, 0
            # todo: cleaner way for default values
            solution['pH'] = 7.0 if solution['pH'] == None else solution['pH']
            solution['temp'] = 15.0 if solution['temp'] == None else solution['temp']

            for key, val in solution.items():
                with cols[col]:
                    if key == "units":
                        solution[key] = st.selectbox(key, options=UNIT_OPTIONS, index=1)
                    elif key in BASE_PARAMETERS_UNITS:
                        solution[key] = st.number_input(
                            f"{key} ({BASE_PARAMETERS_UNITS[key]})",
                            value=float(val)
                        )
                    else:
                        solution[key] = st.number_input(
                            f"{key} ({solution['units']})",
                            value=float(val),
                            format="%.6f",
                        )
                    row += 1
                    if (row == rows) & (col < len(cols) - 1):
                        row = 0
                        col += 1
            sel_phases = st.multiselect(
                label="Calculate Saturation Index (SI) for Minerals",
                options=self.phreeqc.phases,
                help="If no minerals are selected, all available saturation indices will be shown."
            )
            if st.button("Calculate"):
                si, cond = self.phreeqc.get_saturation_indices(
                    solution,
                    sel_phases
                )

        if len(si) > 0:
            with st.expander("PHREEQC output", expanded=True):
                cols = st.columns(2)
                with cols[0]:
                    st.markdown(f"Conductivity (µS/cm): {cond :.4f}")
                    cols = [
                        {"name": "index", "type": "int", "precision": 0, "hide": True},
                        {"name": "si", "type": "float", "precision": 4, "hide": False},
                    ]
                    settings = {"selection_mode": None}
                    show_table(df=si, cols=cols, settings=settings)


    def init_solution(self, row):
        phr_sim = PhreeqcSimulation(self.project)
        if len(row) > 0:
            sol = {"units": UNIT_OPTIONS[1], "density": 1.000}
            for master_species in ['pH', 'temp'] + phr_sim.master_species:
                if master_species in self. phreeqc_map:
                    col_name = self. phreeqc_map[master_species]
                    sol[master_species] = row.iloc[0][col_name]
        else:
            sol = {"units": UNIT_OPTIONS[1], "density": 1.000, 'pH': 7, 'temp': 15}
            for master_species in phr_sim.master_species:
                if master_species in self. phreeqc_map:
                    sol[master_species] = 0
        return sol

    def show_records(self, fields: list = []):
        if fields == []:
            fields = self.select_table_fields
        df = self.project.data[fields]
        settings = {"selection_mode": "single", "fit_columns_on_grid_load": True, 'height': 200}
        cols = []
        sel_row = show_table(df, cols=cols, settings=settings)
        return sel_row

    def show(self):
        st.markdown(f"**{self.title}**")

        # only let the user choose, if all elements are present, otherwise manual
        # input is default
        if self.has_required_input:
            self.input = st.radio("Data source", options=self.input_options)
        # self.minerals = st.selectbox(label='Minerals', options=self.minerals_options)
        if self.input_options.index(self.input) == 0:
            st.markdown("Select a Sample:")
            sel_row = self.show_records()
            solution = self.init_solution(sel_row)
        else:
            solution = self.init_solution(pd.DataFrame())
        self.show_result(solution)
