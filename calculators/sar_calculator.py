import math
import pandas as pd

import streamlit as st
from st_aggrid import AgGrid
from chempy import Substance
from project import Project, SystemFieldEnum

from phreeqc_simulation import PhreeqcSimulation
lang = {}


def set_lang():
    global lang
    # lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)


class IrrigationWaterQuality:
    """todo: calculate adjusted SAR using bicarbonate"""

    def __init__(self, prj: Project):
        self.title = "Irrigation Water Quality"
        self.project = prj
        self.phr_sim = PhreeqcSimulation(prj)
        self.input_options = ["Select sample from dataset", "Enter data manually"]
        self.has_required_input = self.get_has_required_input()
        self.input = (
            self.input_options[0] if self.has_required_input else self.input_options[1]
        )
        self.select_table_fields = self.get_select_table_fields()

    def get_has_required_input(self) -> bool:
        """Verifies if dataset includes required parameters

        Returns:
            bool: true if data includes ca, mg, na
        """

        ok = self.project.is_mapped(SystemFieldEnum.CALCIUM.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.MAGNESIUM.value)
        ok = ok & self.project.is_mapped(SystemFieldEnum.SODIUM.value)
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

        fields = fields + [
            SystemFieldEnum.CALCIUM.value,
            SystemFieldEnum.MAGNESIUM.value,
            SystemFieldEnum.SODIUM.value,
            SystemFieldEnum.PH.value,
            SystemFieldEnum.COND.value,
            SystemFieldEnum.WATER_TEMPERATURE.value,
        ]
        if self.project.is_mapped(SystemFieldEnum.BICARBONATE.value):
            fields.append(SystemFieldEnum.BICARBONATE.value)
        if self.project.is_mapped(SystemFieldEnum.ALKALINITY.value):
            fields.append(SystemFieldEnum.ALKALINITY.value)
        return fields

    def get_rsc_interpretation_df(self):
        """from JW Lloyd, p250

        Returns:
            [type]: [description]
        """
        df = pd.DataFrame(
            {
                "RSC (meq/L)": ["<1.25", "1.25-2.5", ">2.5"],
                "Classification": [
                    "Suitable",
                    "Marginal",
                    "Not suitable",
                ],
            }
        )
        return df

    def get_sar_interpretation_df(self) -> pd.DataFrame:
        """
        from http://turf.okstate.edu/water-quality/sar-calculator

        Returns:
            [type]: [description]
        """
        df = pd.DataFrame(
            {
                "SAR": ["<1", "1-2", "2-4", "4-8", "8-15", ">15"],
                "Classification": [
                    "Excellent",
                    "Good",
                    "Fair",
                    "Poor",
                    "Very Poor",
                    "Unacceptable",
                ],
                "Management Considerations": [
                    "None",
                    "Little concern, add pelletized gypsum periodically",
                    "Aerify soil, sand topdress, apply pelletized gypsum, monitor soil salinity",
                    "Aerify soil, sand topdress, apply pelletized gypsum, leach soil regularly, monitor soil salinity closely",
                    "Requires special attention; consult water quality specialist",
                    "Do not use",
                ],
            }
        )
        return df

    def get_sar_classification(self, result: float) -> str:
        """
        Returns a irrigation suitability classification for a numeric sar 
        result.
        classification from http://turf.okstate.edu/water-quality/sar-calculator

        Args:
            result (float): calculated rsc value

        Returns:
            str: calculated sar value
        """

        if result < 1:
            return "Excellent"
        elif result >= 1 and result < 2:
            return "Good"
        elif result >= 2 and result < 4:
            return "Fair"
        elif result >= 4 and result < 8:
            return "Poor"
        elif result >= 8 and result < 15:
            return "Very Poor"
        elif result >= 15:
            return "Unacceptable"

    def get_rsc_classification(self, result: float) -> str:
        """
        Returns a irrigation suitability classification for a numeric rsc result.
        classification from http://turf.okstate.edu/water-quality/sar-calculator

        Args:
            result (float): calculated rsc value

        Returns:
            str: _description_
        """

        if result < 1.25:
            return "Suitable"
        elif result >= 1.25 and result < 2.5:
            return "Marginal"
        else:
            return 'Not suitable'

    def show_sar_result(self, result: dict):
        cols = st.columns(2)
        with cols[0]:
            st.text_input("SAR", f"{result['sar']:.2f}")
            st.text_input("Classification", self.get_sar_classification(result['sar']))
            df = self.get_sar_interpretation_df()
            with st.expander("Classification (SAR)"):
                AgGrid(df, height=240)
                st.markdown(
                    "[reference](http://turf.okstate.edu/water-quality/sar-calculator)"
                )
        if 'adj_sar' in result:
            with cols[1]:
                st.text_input(f"adj.SAR (pHc = {result['phc']:.2f})", f"{result['adj_sar']:.1f}")
                st.text_input("Classification (adj)", self.get_sar_classification(result['adj_sar']))

    def show_rsc_result(self, result):
        cols = st.columns(2)
        with cols[0]:
            st.text_input("RSC", f"{result:.1f}")
            st.text_input("Classification", self.get_rsc_classification(result))
            df = self.get_rsc_interpretation_df()
            with st.expander("Classification (RSC)"):
                AgGrid(df, height=240)


    def show(self):
        st.markdown(f"**{self.title}**")
        # only let the user choose, if all elements are present, otherwise 
        # manual input is default
        if self.has_required_input:
            self.input = st.radio("Data source", options=self.input_options)

        if self.input_options.index(self.input) == 0:
            self.show_records()
        elif self.input_options.index(self.input) == 1:
            self.show_form()

    def show_records(self):
        sel_row = self.project.select_records_in_table(self.select_table_fields)
        if len(sel_row) > 0:
            na, ca, mg, alk, hco3, co3 = 0, 0, 0, 0, 0, 0
            solution_dict = dict(
                self.project.data.loc[sel_row['index']].iloc[0]
            )
            defaults = {'units': 'mg/L', 'pH': '7 calcite 0'}
            sol = self.phr_sim.get_solution_from_dict(
                input_dict=solution_dict,
                default_dict=defaults
            )
            solution = self.phr_sim.add_solution_from_dict(sol)
            na = solution_dict[SystemFieldEnum.SODIUM.value]
            ca = solution_dict[SystemFieldEnum.CALCIUM.value]
            mg = solution_dict[SystemFieldEnum.MAGNESIUM.value]

            alk = solution_dict[SystemFieldEnum.ALKALINITY.value]
            if self.project.is_mapped(SystemFieldEnum.BICARBONATE.value):
                hco3 = solution_dict[SystemFieldEnum.BICARBONATE.value]
            if self.project.is_mapped(SystemFieldEnum.CARBONATE.value):
                co3 = solution_dict[SystemFieldEnum.CARBONATE.value]

            if na > 0 and ca > 0 and mg > 0:
                na_meq = na / Substance.from_formula("Na").mass
                ca_meq = ca / Substance.from_formula("Ca").mass * 2
                mg_meq = mg / Substance.from_formula("Mg").mass * 2
                hco3_meq = hco3 / Substance.from_formula("HCO3").mass
                co3_meq = co3 / Substance.from_formula("HCO3").mass
                alk_meq = alk / 50.04
                result = {
                    'sar': na_meq / math.sqrt(0.5 * (ca_meq + mg_meq)),
                    'adj_sar': (na_meq / math.sqrt(0.5 * (ca_meq + mg_meq))) * (1 + (8.4 - solution.pH)),
                    'phc': solution.pH
                }
                self.show_sar_result(result)
            else:
                st.warning(
                    "Please enter concentrations for calcium, magnesium and sodium"
                )
            result = None
            if na > 0 and ca > 0 and mg > 0 and alk > 0:
                result = alk_meq - (ca_meq + mg_meq)
            elif na > 0 and ca > 0 and mg > 0 and hco3_meq + co3_meq > 0:
                result = (hco3_meq + co3_meq) - (ca_meq + mg_meq)
            if result:
                self.show_rsc_result(result)


    def show_form(self):
        cols = st.columns(2)
        with cols[0]:
            with st.form("my_form"):
                status = "ready"
                # ec = st.number_input("EC (μS/cm", value=0)
                ca = st.number_input("Ca++ mg/L")
                mg = st.number_input("Mg++ mg/L")
                na = st.number_input("Na+ mg/L")
                hco3 = st.number_input("HCO3- mg/L")
                co3 = st.number_input("CO3-- mg/L")
                alk = st.number_input("Alkalinity mg/L CaCO3")
                submitted = st.form_submit_button("Calculate")
                if submitted:
                    if na > 0 and ca > 0 and mg > 0:
                        sol = {
                            'units': 'mg/L',
                            'temp': 15,
                            'pH': '7 Calcite 0',
                            'Na': na,
                            'Ca': ca,
                            'Mg': mg,
                        }
                        na_meq = na / Substance.from_formula("Na").mass
                        ca_meq = ca / Substance.from_formula("Ca").mass * 2
                        mg_meq = mg / Substance.from_formula("Mg").mass * 2
                        sar = na_meq / math.sqrt(0.5 * (ca_meq + mg_meq))

                        if alk > 0:
                            sol['Alkalinity'] = alk
                        else:
                            sol['C(4)'] = hco3
                        if alk + hco3 > 0:
                            solution = self.phr_sim.add_solution_from_dict(sol)
                            result = {
                                    'sar': sar,
                                    'adj_sar': sar * (1 + (8.4 - solution.pH)),
                                    'phc': solution.pH,
                            }
                        else:
                            result = {'sar': sar}

                        status = "done"
                    else:
                        status = "insufficient"

        if status == "done":
            self.show_sar_result(result)
        elif status == "insufficient":
            st.warning("Please enter concentrations for calcium, magnesium and sodium")
