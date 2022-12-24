import streamlit as st
import pandas as pd
from io import StringIO

from config import *


class Dataset():
    def __init__(self):
        self.column_map = {'ca': None,'mg': None,'na': None,'k': None,
                      'hco3': None,'co3': None,'alk': None,'so4': None,'cl': None,
                      'latitude': None, 'longitude': None,
                      'ph': None, 'wtemp': None, 
                      'date': None}
        self.codes = {}
        self.datasource = 0
        self.sep = ';'
        self.encoding = 'utf8'
        self.data = pd.read_csv('./data/demo.csv', sep=self.sep)
        self.normalize_column_headers()


    def normalize_column_headers(self):
        self.data.columns = [x.lower() for x in self.data.columns]
        for col in self.data.columns:
            if col in self.column_map:
                self.column_map[col] = col
            if col in ['sample_date', 'date']:
                self.data[col] = pd.to_datetime(self.data[col])
            if self.data[col].dtype == 'object':
                self.data[col] = self.data[col].astype(str)


    def show_upload(self):
        self.sep = st.selectbox('Seperator character',options=SEPARATOR_OPTIONS)
        self.encoding = st.selectbox('Encoding',options=ENCODING_OPTIONS)
        uploaded_file = st.file_uploader("Upload csv file")
        if uploaded_file is not None:
            self.data = pd.read_csv(uploaded_file, sep=self.sep, encoding=self.encoding)
            self.normalize_column_headers()
    
    
    def show_mapped_columns(self):
        with st.expander('Column mapping', expanded=True):
            cols = st.columns(2)
            all_fields = [None] + list(self.data.columns)
            with cols[0]:
                self.latitude_col = st.selectbox('latitude column', options=all_fields)
                self.longitude_col = st.selectbox('Longitude column', options=all_fields)
            with cols[1]:
                self.sampling_date_col = st.selectbox('Sampling date column', options=all_fields)
        if 'alk' in self.data.columns:
            self.alk_unit = st.selectbox('Longitude column', options=['mg/L CaCO3', 'meq/L'])


    def build_code_lists(self):
        for col in [x for x in self.data.columns if self.data[x].dtype in ['object','text']]:
            self.codes[col] = list(self.data[col].unique())


    def filter_data(self):
        filter = {}
        with st.sidebar.expander('🔎Filter', expanded=True):
            for code, list in self.codes.items():
                filter[code] = st.multiselect(code, options=list)
                if filter[code]:
                    self.data = self.data[self.data[code].isin(filter[code])]
        return self.data


    def get_user_input(self):
        data_options = ['Demo data','Upload dataset']
        self.datasource = st.radio('Data', options=data_options,index=self.datasource)
        self.datasource = data_options.index(self.datasource)
        if self.datasource > 0:
            self.show_upload()
        self.show_mapped_columns()
        self.build_code_lists()
        self.data = self.filter_data()
        with st.expander('Preview data', expanded=True):
            st.write(f"{len(self.data)} records")
            st.write(self.data)
            st.download_button(label="Download data as CSV",
                data=self.data.to_csv(sep=';').encode('utf-8'),
                file_name='fontus_data.csv',
                mime='text/csv',
)
        st.session_state['dataset'] = self




