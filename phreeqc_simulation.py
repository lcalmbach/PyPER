from re import L
import pandas as pd
import numpy as np
from phreeqpython import PhreeqPython
from pathlib import Path
import os
import streamlit as st
import math

KEYWORDS = [
    "SOLUTION_MASTER_SPECIES",
    "SOLUTION_SPECIES",
    "PHASES",
    "EXCHANGE_MASTER_SPECIES",
    "EXCHANGE_SPECIES",
    "SURFACE_MASTER_SPECIES",
    "SURFACE_SPECIES",
]


class PhreeqcSimulation:
    def __init__(self, prj):
        self.project = prj
        (
            self.phreeqc_parameter_fields,
            self.phreeqc_parameter_dict,
        ) = self.get_phreeqc_parameter_fields()
        dir = Path(os.path.dirname(__file__) + "/database")
        self.sim = PhreeqPython(
            database=self.project.cfg["phreeqc_database"], database_directory=dir
        )
        self.database_file = os.path.join(dir, self.project.cfg["phreeqc_database"])
        self.solution_identifiers = []
        self.master_species = []
        self.phases = []
        self.init_codelists()

    def get_phreeqc_parameter_fields(self):
        df = self.project.fields
        df = df[df["phreeqc_ms"].notnull()].reset_index()
        phr_dict = dict(zip(list(df["index"]), list(df["phreeqc_ms"])))
        return list(df["index"]), phr_dict

    def init_codelists(self):
        def extract_phases(lno: int):
            for line in lines[lno + 1 :]:
                x = str.strip(line)
                if len(x) == 0:
                    pass
                elif x in KEYWORDS:
                    self.phases.sort()
                    return lno
                elif (
                    (ord(x[0]) >= ord("A")) & (ord(x[0]) <= ord("Z")) & ("=" not in x)
                ) | (x[0] == "("):
                    self.phases.append(x.split("\t")[0])
                lno += 1

        def extract_master_species(lno: int):
            stop_word = "SOLUTION_SPECIES"
            for line in lines[lno + 1 :]:
                x = str.strip(line)
                if len(x) == 0:
                    pass
                elif stop_word in x:
                    return lno
                elif x[0] != "#":
                    self.master_species.append(x.split("\t")[0])
                lno += 1

        with open(self.database_file, "r") as thermdb:
            lines = thermdb.readlines()
        i = 0
        for line in lines:
            if line.strip() == "SOLUTION_MASTER_SPECIES":
                lineno = extract_master_species(i)
                break
            i += 1
        i = 0
        for line in lines:
            if line.strip() == "PHASES":
                lineno = extract_phases(i)
                break
            i += 1

    def add_solution_from_dict(self, inp_solution):
        solution = self.sim.add_solution(inp_solution)
        return solution

    def add_solution(self, df: pd.DataFrame, identifiers: dict):
        input = dict(zip(df["solution_master_species"], df["value_numeric"]))
        solution = self.sim.add_solution(input)
        self.solution_identifiers.append(identifiers)
        return solution.phases

    def get_saturation_indices(self, sol: dict, phases: list):
        solution = self.sim.add_solution(sol)
        df = pd.DataFrame({"phase": [], "si": []})
        if phases == []:
            for phase in solution.phases:
                df = pd.concat(
                    [df, pd.DataFrame({"phase": [phase], "si": [solution.si(phase)]})],
                    axis=0,
                )
        for phase in phases:
            df = pd.concat(
                [df, pd.DataFrame({"phase": [phase], "si": [solution.si(phase)]})],
                axis=0,
            )
        return df.reset_index(), solution.sc

    def get_solution_num(self):
        return len(self.sim.get_solution_list())

    def get_solution(self, index):
        sol = self.sim.get_solution[index]
        return sol.composition

    def get_phase_df(self):
        # import numpy as np
        # nan = np.nan
        rows = []
        for i in range(0, len(self.sim.get_solution_list())):
            self.solution_identifiers[i].update(self.sim.get_solution(i).phases)
            rows.append(self.solution_identifiers[i])
        df = pd.DataFrame.from_dict(rows, orient="columns")
        return df

    def get_solution_from_dict(self, input_dict: dict, default_dict: dict) -> dict:
        solution_dict = default_dict
        for key, value in input_dict.items():
            # if the key is a fields that is mapped to a phreeqc parameter and the field is not
            # yet defined in the dict (e.g. by the default settings)
            # fix: make values numeric in grid first!

            if key in self.phreeqc_parameter_fields:
                if (
                    self.phreeqc_parameter_dict[key] not in solution_dict.keys()
                ) and not (np.isnan(value)):
                    ms = self.phreeqc_parameter_dict[key]
                    solution_dict[ms] = value
        return solution_dict
