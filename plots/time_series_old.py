from bokeh.models.tools import SaveTool
import pandas as pd
import numpy as np
import streamlit as st
from bokeh.plotting import figure
from bokeh.tile_providers import CARTODBPOSITRON, get_provider
from bokeh.models import ColumnDataSource, GMapOptions, HoverTool
from bokeh.core.enums import MarkerType, LineDash
from bokeh.models import ColumnDataSource, Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span
from bokeh.transform import factor_mark, factor_cmap
import bokeh.palettes as bpal 
from bokeh.models.tickers import FixedTicker
from bokeh.models import BoxAnnotation
from datetime import datetime 
import itertools

from helper import get_lang, get_ticks
from const import MARKERS


class Time_series:
    def __init__(self, df:pd.DataFrame, cfg:dict):
        self.data = df
        self.cfg = cfg
        lang = get_lang(lang=st.session_state.language, py_file=__file__)

    def add_markers(self, p, df):
        p.circle(x="x", y="y", size=self.cfg['symbol_size'], fill_color=self.cfg['fill_colors'][0], fill_alpha=self.cfg['fill_alpha'], source=df)
        return p

    def get_plot(self):
        p = figure(title=self.cfg['plot_title'], x_axis_type="datetime", 
                   toolbar_location="above", 
                   tools = [],
                   plot_width = int(self.cfg['plot_width']), 
                   plot_height = int(self.cfg['plot_height']))
        p.title.align = "center"
        p.yaxis.axis_label = self.cfg['y_axis_title']
        if not self.cfg['y_axis_auto']:
            p.y_range = Range1d(self.cfg['y_axis_start'], self.cfg['y_axis_end'])
            if self.cfg['y_axis_tick_interval'] > 0:
                p.yaxis.ticker = FixedTicker(ticks=get_ticks(self.cfg['y_axis_tick_interval'], (self.cfg['y_axis_start'], self.cfg['y_axis_end'])))
        if not self.cfg['time_axis_auto']:
            t_min = datetime(self.cfg['time_axis_start'].year, self.cfg['time_axis_start'].month, self.cfg['time_axis_start'].day)
            t_max = datetime(self.cfg['time_axis_end'].year, self.cfg['time_axis_end'].month, self.cfg['time_axis_end'].day)
            p.x_range = Range1d(t_min,t_max)
        
        palette_len = 4 if len(self.cfg['parameters']) <=4 else 9
        color = itertools.cycle(bpal.all_palettes[self.cfg['palette']][palette_len]) #helper.color_gen(self.cfg['palette'], 10)
        i=0
        legend_items = []
        for item in self.cfg['parameters']:
            index = self.cfg['parameters'].index(item)
            #st.write(self.data,self.cfg['legend_col'],item)
            df = self.data[self.data[self.cfg['legend_col']] == int(item)]
            df = df.rename(columns={"sampling_date": 'date'})
            clr = next(color)
            l = p.line(x = 'date', 
                        y=self.cfg['y_col'], 
                        line_color = clr, 
                        line_width = 2, 
                        alpha = self.cfg['fill_alpha'], 
                        source=df)
            m = p.scatter(x = 'date',
                        y = self.cfg['y_col'],
                        marker = MARKERS[i],
                        size = self.cfg['symbol_size'],
                        color = clr,
                        alpha = self.cfg['fill_alpha'],
                        source = df)
            legend_items.append((self.cfg['legend_items'][index],[l,m]))
            i+=1
            
        if self.cfg['show_average_line']:
            dummy = pd.DataFrame({'x':[1], 'y':[1]})
            avg = df['value_numeric'].mean()
            hline = Span(location=avg, dimension='width', 
                line_color=self.cfg['avg_line_col'], 
                line_width=self.cfg['avg_line_width'], 
                line_alpha = self.cfg['avg_line_alpha'], 
                line_dash=self.cfg['avg_line_dash'])
            p.renderers.extend([hline])
            l = p.line(line_color=self.cfg['avg_line_col'], line_width=self.cfg['avg_line_width'], alpha=self.cfg['avg_line_alpha'],line_dash=self.cfg['avg_line_dash'])
            legend_items.append(('Average',[l]))

        if self.cfg['show_percentile_band'] > 0:
            def get_limits(index):
                if index == 1: #5/95
                    bottom = df['value_numeric'].quantile(0.05)
                    top = df['value_numeric'].quantile(0.95)
                elif index == 2: #10/90
                    bottom = df['value_numeric'].quantile(0.1)
                    top = df['value_numeric'].quantile(0.9)
                else: 
                    bottom = df['value_numeric'].quantile(0.25)
                    top = df['value_numeric'].quantile(0.75)
                return top, bottom

            # add bands to the y-grid
            top, bottom = get_limits(self.cfg['show_percentile_band'])
            box = BoxAnnotation(bottom=bottom, top=top, fill_color=self.cfg['pct_band_color'], fill_alpha=self.cfg['pct_band_alpha'])
            p.add_layout(box)

        if 'hlines' in self.cfg:
            for lin in self.cfg['hlines']:
                hline = Span(location=lin['location'], dimension='width', line_color=lin['color'], line_width=lin['width'])
                p.renderers.extend([hline])
        legend = Legend(items=legend_items, 
                        location=(0, 0), 
                        click_policy="hide")
        p.add_layout(legend, 'right')
        p.add_tools(HoverTool(
            tooltips=[
                ('Station', '@station_identifier'),
                ('Date', '@date{%F}'),
                ('Parameter', f'@parameter_name'),
                ('Value', '@value_numeric')
            ],
            formatters={
                '@date': 'datetime', # use 'datetime' formatter for 'date' field
            })
        )
        
        return p

