import math
import pandas as pd
import numpy as np
import streamlit as st
from st_aggrid import AgGrid
from chempy import Substance
from chempy.util import periodic

from helper import sort_dict_by_value, flash_text, show_table


def get_atomic_number_dict():
    result = pd.DataFrame({
            'number': periodic.symbols,
            'atomic_number': range(1, len(periodic.symbols)+1),
            'fwm': periodic.relative_atomic_masses,
            'names': periodic.names
        }
    )
    result = [{periodic.symbols.index(x)+1: x} for x in periodic.symbols]
    return result


ATOMIC_NUMBER_DICT = get_atomic_number_dict()

def get_fmw(formula: str):
    substance = Substance.from_formula(formula)
    return substance.mass

def show_periodic_system():
    df = pd.DataFrame({'Name': periodic.names, 'Symbol': periodic.symbols, 'Mass (g/Mol)': periodic.relative_atomic_masses}).reset_index()
    df['Name'] = [f'<a href="https://en.wikipedia.org/wiki/{x}">{x}</a>' for x in periodic.names]
    df['index'] = df['index'] + 1
    df = df.rename(columns={'index': 'Atomic Number (Z)'})
    with st.expander('Periodic System'):
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

def is_valid_formula(formula: str):
    ok, err_text = False, ''
    if '·' in formula:
        err_text = "'·' is not a valid character, please use '.' as a seperator in hydrous minerals."
    elif ':' in formula:
        err_text = "':' is not a valid character, please use '.' as a seperator in hydrous minerals."
    else:
        try:
            substance = Substance.from_formula(formula)
            ok = True
        except :
            err_text = 'This does not seem to be a valid formula.'
    return ok, err_text


class FormulaWeightCalculator:
    def __init__(self, prj):
        self.project = prj
        self.cfg = {}
        self.title = "Formula Weight Calculation"
        self.minerals_df = pd.read_csv(
            "./data/minerals.csv", sep=";"
        )  # .set_index('mineral')
        min_dict = dict(
            zip(list(self.minerals_df["formula"]), list(self.minerals_df["mineral"]))
        )
        self.minerals_dict = sort_dict_by_value(min_dict)

    def show(self):
        """
        Takes a mineral name or a formula as input and calculates and displays 
        the resulting formula weight and the elemental composition of the 
        chemical compound.
        """
        st.markdown(f"**{self.title}**")
        input_options = ["Mineral name", "Formula"]
        input = st.radio("Input from", options=input_options)
        if input_options.index(input) == 0:
            formula = st.selectbox(
                label="Mineral",
                options=self.minerals_dict.keys(),
                format_func=lambda x: f"{self.minerals_dict[x]} ({x})",
            )
        else:
            formula = st.text_input("Formula")

        ok, err_text = is_valid_formula(formula)
        if ok:
            total_weight = get_fmw(formula)
            st.text_input("Formula Mass (g)", f"{total_weight: .2f}")
            composition = Substance.from_formula(formula).composition
            st.markdown("Elemental Composition")
            df = pd.DataFrame({
                'Atomic_number': composition.keys(),
                'Mols': composition.values()}
            )
            df['Name'] = [periodic.names[x - 1] for x in df['Atomic_number']]
            df['Symbol'] = [periodic.symbols[x - 1] for x in df['Atomic_number']]
            df['Formula mass'] = [
                periodic.relative_atomic_masses[x - 1] for x in df['Atomic_number']
            ]
            df['Total mass'] = df['Formula mass'] * df['Mols']
            df['Mass%'] = df['Total mass'] / total_weight
            df['Mass%'] = df['Mass%'].apply('{:,.2%}'.format)
            ordered_fields = ['Name', 'Atomic_number', 'Symbol',
                'Formula mass', 'Mols', 'Total mass', 'Mass%']
            df = df[ordered_fields]
            st.write(df)
        else:
            st.warning(err_text)
        show_periodic_system()


class FormulaWeightConversion:
    def __init__(self, prj):
        self.project = prj
        self.cfg = {}
        self.title = "Formula Weight Conversion"
        self.cfg["formula_in"] = "N"
        self.cfg["formula_out"] = "NO3"
        self.cfg["master_element"] = "N"

    def get_fmw(self, formula: str):
        substance = Substance.from_formula(formula)
        return substance.mass

    def show(self):
        def show_result():
            text = f"Conversion {self.cfg['formula_in']} -> {self.cfg['formula_out']}:"
            st.markdown(text)
            cols = st.columns(2)
            with cols[0]:
                st.text_input(
                    f"Formula weight input ({self.cfg['master_element']} as {self.cfg['formula_in']})",
                    Substance.from_formula(self.cfg["formula_in"]).mass,
                )
                st.text_input("factor", factor)
            with cols[1]:
                st.text_input(
                    f"Formula weight output ({self.cfg['master_element']} as {self.cfg['formula_out']})",
                    Substance.from_formula(self.cfg["formula_out"]).mass,
                )
                st.text_input("Result", result)

        st.markdown(f"**{self.title}**")
        with st.form("my_form"):
            factor = 0
            result = ""
            factor = ""
            status = "ready"

            self.cfg["input_concentration"] = st.number_input(
                "Input concentration (mg/L)"
            )
            id = periodic.symbols.index(self.cfg["master_element"])
            self.cfg["master_element"] = st.selectbox(
                "Master element", options=periodic.symbols, index=id
            )
            self.cfg["formula_in"] = st.text_input(
                "Chemical formula for concentration input", "N"
            )
            self.cfg["formula_out"] = st.text_input(
                "Chemical formula for concentration output", "NO3"
            )
            submitted = st.form_submit_button("Convert")
            if submitted:
                if (self.cfg["formula_in"] > "") & (self.cfg["formula_out"] > ""):
                    message = ""
                    master_element_key = (
                        periodic.symbols.index(self.cfg["master_element"]) + 1
                    )
                    substance_in = Substance.from_formula(self.cfg["formula_in"])
                    substance_out = Substance.from_formula(self.cfg["formula_out"])

                    comp_in = substance_in.composition
                    comp_out = substance_out.composition
                    if (
                        master_element_key in comp_in and master_element_key in comp_out
                    ) == False:
                        message = "Master element must be included in input and output formula, please enter valid compositions"
                        status = "insufficient"
                    if message == "":
                        moles_of_master_element_in = comp_in[master_element_key]
                        moles_of_master_element_out = comp_out[master_element_key]
                        fmw_in = self.get_fmw(self.cfg["formula_in"])
                        fmw_out = self.get_fmw(self.cfg["formula_out"])
                        factor = (fmw_out / fmw_in) * (
                            moles_of_master_element_in / moles_of_master_element_out
                        )
                        result = self.cfg["input_concentration"] * factor
                        status = "done"
                else:
                    status = "insufficient"
                    message = "Please enter formula for input and output"
        if status == "done":
            show_result()
        elif status == "insufficient":
            flash_text(message, "warning")
