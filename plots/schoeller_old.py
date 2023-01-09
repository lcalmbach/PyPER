from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.models import Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot, SingleIntervalTicker, FuncTickFormatter
import itertools
from bokeh.palettes import Category10
from scipy.stats.stats import pearsonr

import helper
import const as cn

lang = {}
def set_lang():
    global lang
    lang = helper.get_lang(lang=st.session_state.language, py_file=__file__)

class Schoeller:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        set_lang()
        self.identifier_col = 'sampling_date'
        self.cfg = cfg
        self.data = self.transform_data(df)
        

    def color_gen(self):
        yield from itertools.cycle(Category10[10])


    def transform_data(self, df:pd.DataFrame):
        """generates the lists of points required by bokeh: [1,2,3,4,5,6] [Ca, Mg, NA+K, Cl, SO4, HCO3)]

        Args:
            df (pd.DataFrame): dataframe in the format 1 sample per row
        """
        lines = []
        
        for index, row in df.iterrows():
            x = []
            y = []
            i=1
            values=0
            for par in self.cfg['parameter_names']:
                if row[par] != None:
                    x.append(i)
                    y.append(row[par])
                    values += 1
                i+=1
            if values > 1:
                lines.append({'legend': str(row[self.identifier_col]), 'x': x, 'y': y})
        return lines


    def get_plot(self):
        def init_plot():
            plot = figure(toolbar_location="above", 
                    y_axis_type="log",
                    tools = [],
                    plot_width = self.cfg['plot_width'], 
                    plot_height = self.cfg['plot_height'],
                    title = self.cfg['plot_title'])
            plot.xaxis.ticker = [1,2,3,4,5,6]
            label_dic = {1:'Ca++',2:'Mg++',3:'Na+',4:'Cl-',5:'SO4--',6:'HCO3-'}
            plot.xaxis.major_label_overrides = label_dic
            if self.cfg['y_auto'] == False:
                plot.y_range = Range1d(float(self.cfg['y_axis_min']), float(self.cfg['y_axis_max']))
            plot.title.align = "center"
            plot.yaxis.axis_label = f"{lang['concentration']} (meq/L)"
            plot.xaxis.axis_label = ""
            
            return plot

        plot = init_plot()
        color = self.color_gen()
        # markers are grouped as legends
        i=1
        legend_items = []
        for line in self.data:
            clr = next(color)
            m = plot.line(x=line['x'], 
                y=line['y'],
                line_width=2, 
                color=clr)
            legend_items.append((line['legend'], [m]))
            i+=1
            
            if i == 20: break

        legend = Legend(items=legend_items, 
                        location=(0, 0), 
                        click_policy="hide")
        plot.add_layout(legend, 'right')
        return plot
