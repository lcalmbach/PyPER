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
        'ca': {'formula':'Ca++', 'name': 'Calcium', 'fmw': 40.078, 'valence': 2, 'unit': 'mg/L'},
        'mg': {'formula':'Mg++', 'name': 'Magnesium', 'fmw': 24.305, 'valence': 2, 'unit': 'mg/L'},
        'na': {'formula':'Na+', 'name': 'Sodium', 'fmw': 22.990, 'valence': 1, 'unit': 'mg/L'},
        'k': {'formula':'K+', 'name': 'Potassium', 'fmw': 39.098, 'valence': 1, 'unit': 'mg/L'},
        'so4': {'formula':'SO4++', 'name': 'Sulfate', 'fmw': 96, 'valence': -2, 'unit': 'mg/L'},
        'cl': {'formula':'Cl-', 'name': 'Calcium', 'fmw': 35.45, 'valence': -1, 'unit': 'mg/L'},
        'hco3': {'formula':'HCO3-', 'name': 'Calcium', 'fmw': 	61.0168, 'valence': -1, 'unit': 'mg/L'},
        'co3': {'formula':'CO3--', 'name': 'Calcium', 'fmw': 	60.008, 'valence': -2, 'unit': 'mg/L'},
        'alk': {'formula':'Alk', 'name': 'Alk', 'fmw': 50, 'valence': -1, 'unit': 'mg/L'},
    }

MAX_LEGEND_ITEMS = 20
STATION_IDENTIFIER_COL = 'stationid'
LATITUDE_COL = 'latitude'
LONGITUDE_COL = 'longitude'
PLOTS = ['Piper']

HORIZONTAL_ALIGNEMENT_OPTIONS = ['left', 'center', 'right']
VERTICAL_ALIGNEMENT_OPTIONS = ['top', 'middle', 'bottom']



# texts
ABOUT_TEXT = """## Fontus
This App allows to generate beautiful Piper plots based on your uploaded data. You may also explore the app using the built-in demo data. If you wish to upload your own data, proceed as follows:

1. Activate the `Load Data` tab and select the `Upload dataset` option.
2. Format your data to the one row per sample format, each row must contain at least the following columns: station, Ca, Mg, Na, Hco3 (or Alk), So4, Cl. In addition you may include the columns K and CO3 whci will be added to the sodium and bicorbonate endpoints.
3. Make sure the right encoding and seperator character are specified.
4. Drag the file into the drop file area or click on the `Browse files` button and select a file using the file explorer.
5. Verify and adjust the plot settinsg on the `Plot Settings`tab.
6. See your Piper plot on the `Show Plot` tab.

Note that no uploaded data is stored on the server. However, we encourage all users not to upload senstive information. 
"""
