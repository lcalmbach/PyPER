import math

SEPARATOR_OPTIONS = [';', ',', '\t']
ENCODING_OPTIONS = ['utf8', 'cp1252']
DATA_NUM_FIELDS = {'ca', 'mg','na','k','cl','so4','hco3','alk'}

MARKERS = ['circle','square','triangle','diamond','inverted_triangle','hex','asterisk','circle_cross','circle_dot',
            'circle_x','circle_y','cross','dash','diamond_cross','diamond_dot','dot','hex_dot','plus','square_cross',
            'square_dot','square_pin','square_x','star','star_dot','triangle_dot','triangle_pin','x','y']

sin60 = math.sin(math.radians(60))
cos60 = math.cos(math.radians(60))
sin30 = math.sin(math.radians(30))
cos30 = math.cos(math.radians(30))
tan60 = math.tan(math.radians(60))

ALL_CATIONS = ('ca', 'mg', 'na', 'k')
ALL_ANIONS = ('so4', 'cl', 'hco3', 'co3', 'alk')

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
    CALCIUM_ID ,
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
    CALCIUM_ID ,
    MAGNESIUM_ID,
    SODIUM_ID, 
    POTASSIUM_ID, 
]

PARAMETER_DICT = {
        'ca': {'formula':'Ca++', 'name': 'Calcium', 'fmw': 40.078, 'valence': 2},
        'mg': {'formula':'Mg++', 'name': 'Magnesium', 'fmw': 24.305, 'valence': 2},
        'na': {'formula':'Na+', 'name': 'Sodium', 'fmw': 22.990, 'valence': 2},
        'k': {'formula':'K+', 'name': 'Potassium', 'fmw': 39.098, 'valence': 2},
        'so4': {'formula':'SO4++', 'name': 'Sulfate', 'fmw': 96, 'valence': -2},
        'cl': {'formula':'Cl-', 'name': 'Calcium', 'fmw': 35.45, 'valence': -1},
        'hco3': {'formula':'HCO3-', 'name': 'Calcium', 'fmw': 	61.0168, 'valence': -1},
        'co3': {'formula':'CO3--', 'name': 'Calcium', 'fmw': 	60.008, 'valence': -2},
        'alk': {'formula':'Alk', 'name': 'Alk', 'fmw': 50, 'valence': -1},
    }

MAX_LEGEND_ITEMS = 20
STATION_IDENTIFIER_COL = 'stationid'
LATITUDE_COL = 'latitude'
LONGITUDE_COL = 'longitude'
PLOTS = ['Piper']

# texts
ABOUT_TEXT = """## Fontus
This App allows to generate beautiful Piper plots based on your uploaded data. Your may also explore the app using the built in demo data. If you wish to upload your data, proceed as follows:

1. goto the `Load Data` tab and select the `Upload dataset` option.
2. format your data to the one row per sample format, each row must contain at least the following columns: station, Ca, Mg, Na, Hco3 (or Alk), So4, Cl. In addition you may include the columns K and CO3 whci will be added to the sodium and bicorbonate endpoints.
3. Make sure the right encoding and seperatur character are specified.
4. Drag the file into the ddrop file area or click on the `Browse files` button and select a file using the file explorer.

Note that no uploaded is stored on file. However we encourage all users not to upload senstive information.
"""