from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

import helper
import const as cn

class Histogram:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.data = df
        self.cfg = cfg

    def get_plot(self):
        def get_bins(df, par):
            arr_hist, edges = np.histogram(df['value_numeric'], 
                                           bins = int(self.cfg['bins']),
                                           range = [self.cfg['x_min'], self.cfg['x_max']])
            result = pd.DataFrame({'counts': arr_hist, 
                                   'left': edges[:-1], 
                                   'right': edges[1:]})
            return result
            

        p = figure(plot_height = self.cfg['plot_height'], plot_width = self.cfg['plot_width'], 
                    title = self.cfg['plot_title'],
                    x_axis_label = self.cfg['x_axis_title'], 
                    y_axis_label = self.cfg['y_axis_title'])

        # Add a quad glyph
        bins = get_bins(self.data, self.cfg['parameter'])
        p.quad(bottom=0, top=bins['counts'], 
               fill_alpha=self.cfg['fill_alpha'],
               left=bins['left'], right=bins['right'],
               fill_color=self.cfg['fill_color'], 
               line_color='grey')
        return p

