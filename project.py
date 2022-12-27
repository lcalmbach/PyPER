import streamlit as st
import pandas as pd
from io import StringIO

from config import *
from helper import is_chemical


class Project():
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
        self.fields_list= list(self.data.columns)
        self.fields = self.get_fields()
        self.SYSTEM_FIELDS = ['sample_date', 'longitude', 'latitude', 'group_field', 'chemical_parameter', 'numeric_parameter']
    

    def get_fields(self):
        fields = {}
        for item in self.fields_list:
            if item in ['date','sample_date']:
                fields[item] = {'label': 'Sampling Date', 'type': 'date', 'digits': 0, 'map': 'sample_date'}
            elif item in ('longitude', 'long'):
                fields[item] =  {'label': 'Longitude', 'type': 'float', 'digits': 4, 'map': 'longitude'}
            elif item in ('latitude', 'lat'):
                fields[item] = {'label': 'Latitude', 'type': 'float', 'digits': 4, 'map': 'latitude'}
            elif is_chemical(item):
                par = PARAMETER_DICT[item]
                fields[item] = {'label': par['formula'], 'type': 'float', 'digits': 1, 'map': 'chemical_parameter'}
            else:
                fields[item] = {'label': item.title(), 'type': 'str', 'digits': 0, 'map': 'group_field'}
        return fields


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
            self.fields_list= list(self.data.columns)
            self.fields = self.get_fields()


    def group_fields(self)->list:
        result = []
        for key, value in self.fields.items():
            if value['map'] == 'group_field': 
                result.append(key) 
        return result


    def build_code_lists(self):
        for field in self.group_fields():
            self.codes[field] = sorted(list(self.data[field].unique()))


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
        self.datasource = st.radio('Data', options=data_options, index=self.datasource)
        self.datasource = data_options.index(self.datasource)
        if self.datasource > 0:
            self.show_upload()
        self.build_code_lists()
        self.data = self.filter_data()
        with st.expander('Preview data', expanded=True):
            st.markdown(f"{len(self.data)} records")
            st.write(self.data)
            st.download_button(label="Download data as CSV",
                data=self.data.to_csv(sep=';').encode('utf-8'),
                file_name='fontus_data.csv',
                mime='text/csv',
            )

        with st.expander('Fields', expanded=True):
            cols = st.columns([2,2,1,2,3])
            fields = self.fields
            with cols[0]:
                st.markdown('Field')
                for key, value in fields.items():
                    id = self.fields_list.index(key)
                    st.selectbox(label=' ', options=self.fields_list, index=id, label_visibility='collapsed', key=key +'0')
            with cols[1]:
                st.markdown('Label')
                for key, value in fields.items():
                    st.text_input(label=' ', value=value['label'], label_visibility='collapsed', key=key +'1')
            with cols[2]:
                st.markdown('Digits')
                for key, value in fields.items():
                    st.number_input(label=' ', value=value['digits'], label_visibility='collapsed', key=key +'2')
            with cols[3]:
                st.markdown('Map')
                for key, value in fields.items():
                    id = self.SYSTEM_FIELDS.index(value['map']) + 1 if value['map'] in self.SYSTEM_FIELDS else 0
                    self.fields[key]['map'] = st.selectbox(label=' ', options = [None] + self.SYSTEM_FIELDS, index=id, label_visibility='collapsed', key=key +'3')
        st.session_state['project'] = self




