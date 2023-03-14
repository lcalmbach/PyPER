import math
from enum import Enum
from helper import ExtendedEnum

# app and GUI
TEMP_FOLDER = "./temp/"
SEPARATOR_OPTIONS = [";", ",", r"\t"]
ENCODING_OPTIONS = ["utf8", "cp1252"]
TYPES = ["str", "datetime", "float", "int", "bool"]
MAX_LEGEND_ITEMS = 20
IMAGE_FORMATS = ["png", "svg"]
AGG_GRID_COL_HEIGHT = 30
ALL_PLOTS = ["Piper", "Map", "Time Series"]
ND_FACTOR = 0.5
PHREEQC_UNIT_OPTIONS = ["mmol/L", "mg/L", "ppm"]

TYPE_CONVERSION_DICT = {
    "datetime64[ns]": "date",
    "object": "str",
    "float64": "float",
    "int64": "int",
}


class AggregationFunc(Enum):
    MEAN = "mean"
    MIN = "min"
    MAX = "max"
    STD = "std"
    COUNT = "count"


AGGREGATION_FUNCTIONS = [ef.value for ef in AggregationFunc]

# bokeh plot options
MARKERS = [
    "circle",
    "square",
    "triangle",
    "diamond",
    "inverted_triangle",
    "hex",
    "asterisk",
    "circle_cross",
    "circle_dot",
    "circle_x",
    "circle_y",
    "cross",
    "dash",
    "diamond_cross",
    "diamond_dot",
    "dot",
    "hex_dot",
    "plus",
    "square_cross",
    "square_dot",
    "square_pin",
    "square_x",
    "star",
    "star_dot",
    "triangle_dot",
    "triangle_pin",
    "x",
    "y",
]

# Parameters
SIN60 = math.sin(math.radians(60))
COS60 = math.cos(math.radians(60))
SIN30 = math.sin(math.radians(30))
COS30 = math.cos(math.radians(30))
TAN60 = math.tan(math.radians(60))

ALL_CATIONS = ("ca", "mg", "na", "k")
ALL_ANIONS = {"hco3": ("so4", "cl", "hco3", "co3"), "alk": ("so4", "cl", "alk")}
DEFAULT_CARBONATE_PARAMETERS_DICT = {"hco3": "HCO3- + CO3--", "alk": "Alkalinity"}


class ConcentrationUnits(ExtendedEnum):
    MGPL = "mg/L"
    UGPL = "µg/L"
    NGPL = "ng/L"
    MOLPL = "mol/L"
    MMOLPL = "mmol/L"
    UMOLPL = "µmol/L"
    MEQPL = "meq/L"
    MGPKG = "mg/kg"
    UGPKG = "µg/kg"
    GPKG = "g/kg"


class SysParameterEnumObselote(ExtendedEnum):
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


class CalculatorsEnum(ExtendedEnum):
    FORMULA_WEIGHT_CONVERSION = "Formula Weight Conversion"
    FORMULA_WEIGHT_CALCULATION = "Formula Weight Calculation"
    IWQ = "Irrigation Water Quality"
    SATURATION_INDEX = "Saturation Index"


PARAMETERS_FILE = "./data/parameters.csv"
PHREEQC_DATABASE_PATH = "./database"

# STATION_IDENTIFIER_COL = "stationid"
# LATITUDE_COL = "latitude"
# LONGITUDE_COL = "longitude"
# PLOTS = ["Piper"]
# from: https://stackoverflow.com/questions/44124436/python-datetime-to-season
MONTH_TO_SEASON = [month % 12 // 3 + 1 for month in range(1, 13)]
SEASON_DICT = {
    "n": {1: "winter", 2: "spring", 3: "summer", 4: "fall"},
    "s": {1: "summer", 2: "fall", 3: "winter", 4: "spring"},
}

HEMISPHERE_DICT = {"n": "Northern Hemisphere", "s": "Southern Hemisphere"}
HORIZONTAL_ALIGNEMENT_OPTIONS = ["left", "center", "right"]
VERTICAL_ALIGNEMENT_OPTIONS = ["top", "middle", "bottom"]
FONT_SIZES = [
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    22,
    24,
    26,
    18,
    30,
    32,
]

DOCUMENTATION_LINK = "https://lcalmbach.github.io/fontus-help/"

# texts
ABOUT_TEXT = """## Fontus
#### Discover your Water Quality Data!
Welcome to Fontus, the comprehensive web application designed to help you explore and analyze water quality data with ease. Fontus is powered by the USGS geochemical model [PHREEQC](https://www.usgs.gov/software/phreeqc-version-3), providing you with accurate and reliable calculations to support your analysis. With Fontus, you can create visual representations of your data with [Piper](https://en.wikipedia.org/wiki/Piper_diagram) plots and maps, perform numerical analysis with the Mann Kendall trend method, and access a variety of calculators for formula weight conversion, saturation index, and water quality indices such as SAR. Whether you are a professional in the field or just starting out, Fontus provides you with the tools and resources you need to understand and analyze your water quality data. Test drive the app with the integrated demo dataset, or upload your own data for a more personalized experience. With an extensive help section, Fontus is here to guide you every step of the way. Start exploring today!

Fontus is constantly evolving to meet the needs of its users. If you are a water quality professional or student, this app is here to support you with its comprehensive data analysis tools. And, if there is sufficient interest, the app will be extended with even more plot types and analysis methods. The developers of Fontus are always looking for ways to improve the app and make it even more useful to you. So, if you have suggestions or encounter any issues, don't hesitate to reach out to the [author](mailto:{}) with your feedback. Your input will help make Fontus the best it can be for you and the entire water quality community.
"""

UPLOAD_INSTRUCTIONS = """To upload and analyze your own dataset proceed as follows:
- Prepare a comma-separated data file having the following format: comma-, tab- or semicolon-separated, each row represents a sample, and each column represents a parameter ([See example file](https://raw.githubusercontent.com/lcalmbach/fontus/master/data/demo.csv)).
- Select the `Upload Dataset` option in the radio button selection below.
- Enter the separator character, Enconding, and number of rows above the header line to be skipped.
- Drag and drop the file into the `Upload csv-file` field.
- If you need more guidance, click [here]({}).
"""
