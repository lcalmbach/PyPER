import math

# app and GUI
TEMP_FOLDER = './temp/'
SEPARATOR_OPTIONS = [";", ",", "\t"]
ENCODING_OPTIONS = ["utf8", "cp1252"]
TYPES = ["str", "datetime", "float", "int", "bool"]
MAX_LEGEND_ITEMS = 20
IMAGE_FORMATS = ["png", "svg"]

# DATA_NUM_FIELDS = {"ca", "mg", "na", "k", "cl", "so4", "hco3", "alk"}


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
ALL_ANIONS = {
        'hco3': ("so4", "cl", "hco3", "co3"),
        'alk': ("so4", "cl", "alk")
}
DEFAULT_CARBONATE_PARAMETERS_DICT = {'hco3': 'HCO3- + CO3--', 'alk': 'Alkalinity'}

CALCIUM_ID = 4
MAGNESIUM_ID = 7
SODIUM_ID = 5
POTASSIUM_ID = 6
SULFATE_ID = 9
CHLORID_ID = 8
ALKALINITY_ID = 10
BICARBONATE_ID = 11
CARBONATE_ID = 12



MAJOR_IONS = [
    CALCIUM_ID,
    MAGNESIUM_ID,
    SODIUM_ID,
    POTASSIUM_ID,
    SULFATE_ID,
    CHLORID_ID,
    ALKALINITY_ID,
    BICARBONATE_ID,
    CARBONATE_ID,
]

MAJOR_ANIONS = [
    SULFATE_ID,
    CHLORID_ID,
    ALKALINITY_ID,
    BICARBONATE_ID,
    CARBONATE_ID,
]

MAJOR_CATIONS = [
    CALCIUM_ID,
    MAGNESIUM_ID,
    SODIUM_ID,
    POTASSIUM_ID,
]

PARAMETER_DICT = {
    "ca": {
        "formula": "Ca++",
        "name": "Calcium",
        "fmw": 40.078,
        "valence": 2,
        "unit": "mg/L",
    },
    "mg": {
        "formula": "Mg++",
        "name": "Magnesium",
        "fmw": 24.305,
        "valence": 2,
        "unit": "mg/L",
    },
    "na": {
        "formula": "Na+",
        "name": "Sodium",
        "fmw": 22.990,
        "valence": 1,
        "unit": "mg/L",
    },
    "k": {
        "formula": "K+",
        "name": "Potassium",
        "fmw": 39.098,
        "valence": 1,
        "unit": "mg/L",
    },
    "so4": {
        "formula": "SO4++",
        "name": "Sulfate",
        "fmw": 96,
        "valence": -2,
        "unit": "mg/L",
    },
    "cl": {
        "formula": "Cl-",
        "name": "Calcium",
        "fmw": 35.45,
        "valence": -1,
        "unit": "mg/L",
    },
    "hco3": {
        "formula": "HCO3-",
        "name": "Calcium",
        "fmw": 61.0168,
        "valence": -1,
        "unit": "mg/L",
    },
    "co3": {
        "formula": "CO3--",
        "name": "Calcium",
        "fmw": 60.008,
        "valence": -2,
        "unit": "mg/L",
    },
    "alk": {
        "formula": "Alk",
        "name": "Alk",
        "fmw": 50,
        "valence": -1,
        "unit": "mg/L"
    },
}


STATION_IDENTIFIER_COL = "stationid"
LATITUDE_COL = "latitude"
LONGITUDE_COL = "longitude"
PLOTS = ["Piper"]
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


# texts
ABOUT_TEXT = """## Fontus
#### Discover your water quality data!
Fontus is member of the open-source-software family. It allows the user to generate beautiful [Piper diagrams](https://en.wikipedia.org/wiki/Piper_diagram) based on uploaded water quality data. The user may also explore the app using the built-in demo data. The app is intelligent and detects fields in your data, that can be used for plot legends, plot grouping or as filters. To upload your data, proceed as follows:

1. Activate the `Load Data` tab and select the `Upload dataset` option.
2. Format your data to the 'one row per sample' format. Each row must contain the following columns: station, Ca, Mg, Na, HCO3 (or Alk), So4, Cl. In addition, you may include columns K and CO3, which will be added to the sodium and bicarbonate endpoints.
3. Make sure the correct encoding and separator characters are specified.
4. Drag the file into the drop file area or click the `Browse files` button and select a file using the file explorer.
5. Verify and adjust the plot settings on the `Plot Settings tab.
6. See your Piper plot on the `Show Plot` tab.

Note that no uploaded data is stored on the server. However, we encourage all users not to upload sensitive information.

This app will be extended with additional plot types and analysis methods commonly applied in water quality studies if there is sufficient interest in such a tool. Therefore, do not hesitate to contact the [author](mailto:{}) with suggestions or encountered issues.
"""
