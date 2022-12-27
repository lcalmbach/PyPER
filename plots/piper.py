from bokeh.models.tools import SaveTool
import pandas as pd
import streamlit as st
from bokeh.io import export_png, export_svgs
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead
from bokeh.models.annotations import Title
from bokeh.core.enums import MarkerType, LineDash
import os

from helper import get_random_filename, add_meqpl_columns, flash_text, random_string
from config import *
from project import Project
import colors

gap = 20
figure_padding_left = 10
figure_padding_right = 10
figure_padding_top = 10
figure_padding_bottom = 20
marker_size = 10
tick_len = 2
grid_color = 'darkgrey'
line_color = 'black'
grid_line_pattern = 'dashed'
grid_line_pattern = 'dotted'
legend_location = "top_right"
arrow_length = 5
arrow_size = 5
MARKER_GENERATORS = ['1) symbol, 2) color',
                     '1) color, 2) symbol',
                     'color+symbol']

class Piper():
    def __init__(self, prj: Project):
        self.data = pd.DataFrame()
        self.project = prj


    @property
    def project(self):
        return self._project
    
    @project.setter
    def project(self, prj):
        self._project = prj
        self.cfg = {
            'group-plot-by': None,
            'color': None,
            'marker-size': 8,
            'marker-fill-alpha': 0.8,
            'marker-line-color': '#303132',
            'color-palette': 'Category20',
            'color-number': 11,
            'marker-generator': MARKER_GENERATORS[0],
            'marker-colors': [],
            'marker-types': ['circle', 'square', 'triangle', 'diamond', 'inverted_triangle'],
            'tooltips': {},
            'plot-width': 800,
            'plot-title': '',
            'plot-title-text-size': 1.0,
            'plot-title-align': 'center',
            'plot-title-font': 'arial',
            'image_format': 'png',
            'show-grid': True,
            'show-tick-labels': True,
            'tick-label-font-size': 9,
            'axis-title-font-size': 12,
        }
        self.data = self.init_data(self.project.data)
        self.cfg['tooltips'] = self.init_tooltips()


    def init_tooltips(self):
        tooltips = {}
        for field in self.project.fields_list:
            tooltips[field] = True if field in ['date', 'sample_date', 'station', 'ca', 'mg', 'k', 'na', 'cl', 'hco3', 'so4'] else False
        return tooltips


    def init_data(self, df):
        self.data = df
        self.data.replace(to_replace=[None], value=0, inplace=True)
        cations = [x for x in self.data.columns if x in ALL_CATIONS]
        anions = [x for x in self.data.columns if x in ALL_ANIONS]
        self.data = add_meqpl_columns(self.data, cations + anions)
        meqpl_cations = [f"{item}_meqpl" for item in cations]
        meqpl_anions = [f"{item}_meqpl" for item in anions]
        self.data['sum_cations_meqpl'] = self.data[meqpl_cations].sum(axis=1)
        self.data['sum_anions_meqpl'] = self.data[meqpl_anions].sum(axis=1)
        for par in cations:
            self.data[f"{par}_pct"] = self.data[f"{par}_meqpl"] / self.data['sum_cations_meqpl'] * 100
        for par in anions:
            self.data[f"{par}_pct"] = self.data[f"{par}_meqpl"] / self.data['sum_anions_meqpl'] * 100
        self.cfg['cation_cols'] = [f"{x}_pct" for x in cations]
        self.cfg['anion_cols'] = [f"{x}_pct" for x in anions]
        self.data['ion_balance_pct'] = (self.data['sum_cations_meqpl'] - self.data['sum_anions_meqpl']) / (self.data['sum_cations_meqpl'] + self.data['sum_anions_meqpl']) * 100

        if list(self.cfg['tooltips'].keys()) != self.project.fields_list:
            self.init_tooltips()
        return self.data

    def get_tooltips(self):
        tooltips = []
        for key, value in self.project.fields.items():
            if self.cfg['tooltips'][key]:
                if value['type'] == 'float':
                    format_string = f"{{%0.{value['digits']}f}}"
                elif value['type'] == 'date':
                    format_string = f"{{%F}}"
                else:
                    format_string = ""
                tooltip = (value['label'], f"@{key}{format_string}")
                tooltips.append(tooltip)
        return tooltips
    
    
    def get_tooltip_formatter(self):
        formatter = {}
        for key, value in self.project.fields.items():
            if value['type'] == 'float':
                formatter[f"@{key}"] = 'printf'
            elif value['type'] == 'date':
                formatter[f"@{key}"] = 'datetime'
        return formatter


    def get_tranformed_data(self, df:pd.DataFrame):
        def transform_to_xy(df, type):
            if type == 'cations':
                ions_list = ['ca_pct','na_pct','mg_pct']
                if 'k_pct' in self.cfg['cation_cols']:
                    _df = df.reset_index()[self.cfg['cation_cols'] + ['index']]
                    _df['na_pct'] = _df['na_pct'] + _df['k_pct']
                    _df = _df[ions_list].reset_index()
                else:
                    _df = df.reset_index()[ions_list + ['index']]
                pct_array = _df[ions_list + ['index']].to_numpy()
                offset = 0
            else:
                ions_list = ['hco3_pct','cl_pct','so4_pct']
                if 'co3_pct' in self.cfg['anion_cols']:
                    _df = df.reset_index()[self.cfg['anion_cols'] + ['index']]
                    _df['hco3_pct'] = _df['hco3_pct'] + _df['co3_pct']
                    _df = _df[ions_list + ['index']]
                else:
                    _df = df.reset_index()[ions_list + ['index']]
                pct_array = _df[ions_list + ['index']].to_numpy()
                offset = 100 + gap
            df_xy = pd.DataFrame()
            index_col = pct_array.shape[1]-1
            x = 0
            y = 0
            i = 0
            for row in pct_array:
                if row[0] == 100:
                    x = 0
                    y = 0
                elif row[1] == 100:
                    x = 100
                    y = 0
                elif row[2] == 100:
                    x = 50
                    y = 100 * sin60
                else:
                    x = row[1] / (row[0] + row[1]) * 100
                    # find linear equation mx + q = y
                    if x != 50:
                        m = 100 / (50 - x)
                        q = -(m * x)
                        x = (row[2] - q) / m
                    y = sin60 * row[2]
                df_xy = df_xy.append({'index': row[index_col], '_x': x + offset, '_y': y, 'type': type[0:1]}, ignore_index=True)
                i += 1
            df_xy['index'] = df_xy['index'].astype(int)
            df_xy = df_xy.set_index('index').join(df)
            return df_xy

        def projected_point(anions: pd.DataFrame, cations: pd.DataFrame):
            # ax! = ax! + 110
            #
            # m! = TAN60
            # Q1! = cy! - m! * cx!
            # Q2! = ay! + m! * ax!
            # prx! = (Q2! - Q1!) / (2 * m!)
            # pry! = TAN60 * prx! + Q1!

            df_xy = pd.DataFrame()
            for i in range(0, len(anions)):
                m = tan60
                q1 = cations.iloc[i]['_y'] - (m * cations.iloc[i]['_x'])
                q2 = anions.iloc[i]['_y'] + (m * anions.iloc[i]['_x'])
                
                prx = (q2 - q1) / (2 * m)
                pry = m * prx + q1
                df_xy = df_xy.append({'index': anions.reset_index().iloc[i]['index'], '_x': prx, '_y': pry,'type': 'p'}, ignore_index=True)
            
            df_xy['index'] = df_xy['index'].astype(int)
            df_xy = df_xy.set_index('index').join(self.data)
            return df_xy
        
        cations_df = transform_to_xy(df, 'cations')
        anions_df = transform_to_xy(df, 'anions')
        projected_df = projected_point(anions_df, cations_df)
        df_xy = pd.concat([cations_df, anions_df, projected_df], ignore_index=True)
        return df_xy


    def draw_triangles(self):
        x1 = [0, 100, 50, 0]
        y1 = [0, 0, sin60*100, 0]

        x2 = [100+gap, 200+gap, 150+gap, 100+gap]
        y2 = [0, 0, sin60*100, 0]

        x4 = [100+gap/2, 50+gap/2, 100+gap/2, 150+gap/2, 100+gap/2]
        y4 = [sin60 * gap, sin60*(100 + gap), sin60*(200 + gap), sin60 * (100 + gap), sin60*gap]
        self.plot.axis.visible = False
        self.plot.grid.visible = False

        self.plot.line(x1, y1, line_width=1, color=line_color)
        self.plot.line(x2, y2, line_width=1, color=line_color)
        self.plot.line(x4, y4, line_width=1, color=line_color)


    def draw_axis(self):
        def draw_xaxis_base(offset:bool):
            y = [0,-tick_len * sin60]
            for i in range(1,5):
                delta = (100+gap) if offset else 0
                if offset:
                    x = [i*20+delta, i*20 - tick_len * cos60 + delta]
                else:
                    x = [i*20+delta, i*20 + tick_len * cos60 + delta]
                self.plot.line(x, y, line_width=1, color=line_color) 
                if self.cfg['show-tick-labels']:
                    text = str(i*20) if offset else str(100-i*20)
                    tick_label = Label(x=x[1]-2, y=y[1]-6,text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                        text=text, render_mode='css')
                    self.plot.add_layout(tick_label)

        def draw_triangle_left(offset:bool):
            delta = (100+gap) if offset else 0
            for i in range(1,5):
                x_tick = [delta + i * 10, delta + i * 10 - tick_len] 
                y_tick = [i * 20 * sin60, i * 20 * sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                if not offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] - 5
                    if self.cfg['show-tick-labels']:
                        tick_label = Label(x=x, y=y,text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                            text=str(i*20), render_mode='css')
                        self.plot.add_layout(tick_label)

        def draw_triangle_right(offset:bool):
            delta = (100+gap) if offset else 0
            for i in range(1,5):
                x_tick = [delta + 100 - i * 10, delta + 100 - i * 10 + tick_len ] 
                y_tick = [i * 20 * sin60, i*20 * sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                if offset:
                    y = y_tick[1] - 3
                    x = x_tick[1] + 1
                    if self.cfg['show-tick-labels']:
                        tick_label = Label(x=x, y=y,text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                            text=str(i*20), render_mode='css')
                        self.plot.add_layout(tick_label)

        def draw_diamond_ul():
            for i in range(1, 5):
                x_tick = [50 + gap/2 + i*10, 50 + gap/2 + i*10 - tick_len * cos60]
                y_tick = [(100 + gap + i * 20) * sin60, (100 + gap + i * 20) * sin60 + tick_len * sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)  
                y = y_tick[1] - 2
                x = x_tick[1] - 5
                if self.cfg['show-tick-labels']:
                    tick_label = Label(x=x, y=y, text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                        text=str(i*20), render_mode='css')
                    self.plot.add_layout(tick_label)
        
        def draw_diamond_ur():
            for i in range(1, 5):
                x_tick = [100 + gap/2 + i*10, 100 + gap/2 + i*10 + tick_len * cos60]
                y_tick = [(200 + gap - i * 20) * sin60, (200 + gap - i * 20) * sin60 + tick_len * sin60]
                self.plot.line(x_tick, y_tick, line_width=1, color=line_color)
                y = y_tick[1] - 2
                x = x_tick[1] + 1
                tick_label = Label(x=x, y=y, text_font_size=f"{self.cfg['tick-label-font-size']}pt",
                                text=str(100-i*20), render_mode='css')
                self.plot.add_layout(tick_label)


        def draw_grids():        
            def draw_triangle_grids(offset: bool):
                delta = (100+gap) if offset else 0
                for i in range(1,5):
                    # left-right
                    x = [i*10+delta,100 - i*10 + delta]
                    y = [i*20 * sin60, i*20 * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # horizontal
                    x = [i*20+delta,50 + i*10 + delta]
                    y = [0,(100 - i*20) * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # right-left
                    x = [i*20+delta,i*10 + delta]
                    y = [0, i*20 * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 

            def draw_diamond_grid():
                for i in range(1,5):   
                    # diamond left-right
                    x = [50 + gap/2 + i*10, 100 + gap/2 + i*10 ]
                    y = [(100 + gap + i * 20) * sin60, (gap + i * 20) * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # diamond right-left
                    x = [100 + gap/2 + i*10, 50 + gap/2 + i*10 ]
                    y = [(200 + gap - i * 20) * sin60, (100 + gap - i * 20) * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern)  
                    # diamond horizontal top
                    x = [50 + gap/2 + i*10, 100 + gap/2 + 50 - i*10 ]
                    y = [(100 + gap + i * 20) * sin60, (100 + gap + i * 20) * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                    # diamond horizontal bottom
                    x = [100 + gap/2 + i*10, 100 + gap/2 - i*10]
                    y = [(gap + i * 20) * sin60, (gap + i * 20) * sin60]
                    self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 
                # middle line
                x = [50 + gap/2, 100 + gap + 50 -gap/2]
                y = [(100 + gap)*sin60,(100 + gap)*sin60]
                self.plot.line(x, y, line_width=1, color = grid_color, line_dash=grid_line_pattern) 

            
            def draw_axis_titles():
                def draw_ca_title():
                    x = 50 - 3
                    y = 0 - 3 - self.cfg['axis-title-font-size'] 
                    xa = [x - 2, x - 2 - arrow_size]
                    ya = [y + 2.5, y + arrow_size ]
                    title = 'Ca++'

                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold')
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=arrow_size), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                
                def draw_cl_title():
                    x = 100 + gap + 50 - 3
                    y = 0 - 3 - self.cfg['axis-title-font-size'] 
                    xa = [x + 7, x + 11]
                    ya = [y + 2.5, y + 2 ]
                    title = 'Cl-'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold')
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[0]))
                
                def draw_mg_title():
                    x = 12
                    y = 44 - self.cfg['axis-title-font-size'] + 3
                    #self.plot.circle(x=x,y=y)
                    xa = [x + 9 * cos60, x + 9 * cos60 + 4 * cos60]
                    ya = [y + 14 * sin60, y + 14 * sin60 + 4 * sin60 ]

                    title = 'Mg++'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = 60.5, # not sure why 60 gives the wrong angle
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_SO4_title():
                    x = 200 + gap - 25 - 13 * cos60 + 14
                    y = 50 * sin60 - self.cfg['axis-title-font-size'] + 15*sin60
                    #self.plot.circle(x=x,y=y)
                    xa = [x + 2 * cos60, x + 2 * cos60 - 4 * cos60]
                    ya = [y + 2 * sin60, y + 2 * sin60 + 4 * sin60 ]

                    title = 'SO4--'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = -60.5, # not sure why 60 gives the wrong angle
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_cl_so4_title():
                    x = 50 + gap/2 + 20 - 10
                    y = (100 + gap + 40)*sin60

                    xa = [x + 23 * cos60 - 2 * cos60, x + 25 * cos60 - 2 * cos60 + (arrow_length * cos60)]
                    ya = [y + 23 * sin60 + 2*sin60, y + 25 * sin60 + 2*sin60 + (arrow_length * sin60)]

                    title = 'Cl- + SO4--'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = 60, # not sure why 60 gives the wrong angle
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_ca_mg_title():
                    x = 100 + gap + 50 - 33
                    y = (100 + gap + 70) * sin60

                    xa = [x + 30 * cos60 + 3 * cos60, x + 30 * cos60 + 3 * cos60 + (arrow_length * cos60)]
                    ya = [y - 30 * sin60 + 3 * sin60, y - 30 * sin60 + 3 * sin60 - (arrow_length * sin60)]

                    title = 'Ca++ + Mg++'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = -60, 
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_HCO3_CO3_title():
                    x = 100 + gap / 2 + 23
                    y = gap + 20

                    xa = [x - 3 , x - 3 - (arrow_length * cos60)]
                    ya = [y, y - (arrow_length * sin60)]

                    title = 'HCO3- + CO3--'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = 60, 
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)
                
                def draw_Na_K_title():
                    x = 100 + gap/2 - 30 - 9
                    y = (80-3) * sin60

                    xa = [x + (19 + 6) * cos60, x + (19 + 6) * cos60 + (arrow_length * cos60)]
                    ya = [y - 19  * sin60, y - 19  *sin60 - (arrow_length * sin60)]

                    title = 'Na+ + K+'
                    tick_label = Label(x=x, y=y,
                        text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                        text=title, text_font_style ='bold',
                        angle = -60, 
                        angle_units="deg")
                    self.plot.add_layout(tick_label)
                    self.plot.add_layout(Arrow(end=NormalHead(size=5), line_color=line_color,
                        x_start=xa[0], y_start=ya[0], x_end=xa[1], y_end=ya[1]),)

                draw_ca_title()
                draw_cl_title()
                draw_mg_title()
                draw_SO4_title()
                draw_cl_so4_title()
                draw_ca_mg_title()
                draw_HCO3_CO3_title()
                draw_Na_K_title()

            def draw_main_labels(titles:list, offset:bool):
                delta = 100 + gap if offset else 0
                # Ca/Alk
                if not offset:
                    x = 0 - self.cfg['axis-title-font-size'] * .6 + delta
                else:
                    x = delta
                y = 0 - self.cfg['axis-title-font-size'] * .8
                tick_label = Label(x=x, y=y,
                    text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[0], text_font_style ='bold')
                self.plot.add_layout(tick_label)
                
                # Na+K/Cl: todo: find out how the calculate the length of the text
                if not offset:
                    x = 100 - 6 - len(titles[1]) + delta
                else:
                    x = 100 + delta
                y = 0 - self.cfg['axis-title-font-size'] * .8
                tick_label = Label(x=x, y=y,text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[1], text_font_style ='bold')
                self.plot.add_layout(tick_label)

                # Mg/SO4
                x = 50  + delta
                y = 100 * sin60 + 2   
                tick_label = Label(x=x, y=y,text_font_size=f"{self.cfg['axis-title-font-size']}pt",
                    text=titles[2], text_font_style ='bold')
                self.plot.add_layout(tick_label)

            if self.cfg['show-grid']:
                draw_triangle_grids(offset=False)
                draw_triangle_grids(offset=True)
                draw_diamond_grid()
            draw_axis_titles()
            self.plot.legend.click_policy="mute"

        draw_xaxis_base(False)
        draw_xaxis_base(True)
        draw_triangle_left(False)
        draw_triangle_left(True)
        draw_triangle_right(False)
        draw_triangle_right(True)
        draw_diamond_ul()
        draw_diamond_ur()

        draw_grids()


    def draw_markers(self, df):
        def color_generator(i: int):
            all_colors = colors.get_colors(self.cfg['color-palette'], self.cfg['color-number'])
            if MARKER_GENERATORS.index(self.cfg['marker-generator']) == 0: # symbol first then color
                color_id = i // len(self.cfg['marker-types'])
                color = all_colors[color_id]
                marker_type_id = i % len(self.cfg['marker-types'])
                marker_type = self.cfg['marker-types'][marker_type_id]
            elif MARKER_GENERATORS.index(self.cfg['marker-generator']) == 1: # color first then symbol
                marker_type_id = i // len(self.cfg['marker-types'])
                marker_type = self.cfg['marker-types'][marker_type_id]
                color_id = i % len(self.cfg['marker-types'])
                color = all_colors[color_id]
            else:
                serie_len = len(self.cfg['marker-types']) if len(self.cfg['marker-types']) < len(self.cfg['marker-types']) else len(self.cfg['marker-types'])
                id = i % serie_len
                color = all_colors[id]
                marker_type = self.cfg['marker-types'][id]
            return color, marker_type

        def draw_symbol(df, marker_color, marker_type, label):
            if marker_type =='asterisk':
                self.plot.asterisk('_x', '_y',  legend_label=label, size=self.cfg['marker-size'], color=marker_color, alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='circle':
                self.plot.circle('_x', '_y', legend_label=label, size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='circle_cross':
                self.plot.circle_cross('_x', '_y', legend_label=label, size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='circle_dot':
                self.plot.circle_dot('_x', '_y', legend_label=label, size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='circle_x':
                self.plot.circle_x('_x', '_y', legend_label=label, size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='circle_y':
                self.plot.circle_y('_x', '_y', legend_label=label, size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='cross':
                self.plot.cross('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='dash':
                self.plot.dash('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='diamond':
                self.plot.diamond('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='diamond_cross':
                self.plot.diamond_cross('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='diamond_dot':
                self.plot.diamond_dot('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='dot':
                self.plot.dot('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='hex':
                self.plot.hex('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='hex_dot':
                self.plot.hex_dot('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='inverted_triangle':
                self.plot.inverted_triangle('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='plus':
                self.plot.plus('_x', '_y',  legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='square':
                self.plot.square('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='square_cross':
                self.plot.square_cross('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='square_dot':
                self.plot.square_dot('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='square_pin':
                self.plot.square_pin('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='square_x':
                self.plot.square_x('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='star':
                self.plot.star('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='star_dot':
                self.plot.star_dot('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='triangle':
                self.plot.triangle('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='triangle_dot':
                self.plot.triangle_dot('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='x':
                self.plot.x('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)
            elif marker_type=='y':
                self.plot.y('_x', '_y', legend_label=label,size=self.cfg['marker-size'], color=marker_color, line_color=self.cfg['marker-line-color'], alpha=self.cfg['marker-fill-alpha'], source = df)


        if self.cfg['color'] == None:
            draw_symbol(df, colors.get_colors(self.cfg['color-palette'], 3)[0], self.cfg['marker-types'][0], '')
            self.plot.legend.visible = False
        else:
            items = list(df[self.cfg['color']].dropna().unique())
            if len(items) > MAX_LEGEND_ITEMS:
                warning = f'Plot has {len(items)} items, only the first {MAX_LEGEND_ITEMS} will be shown. Use filters to further reduce the number of legend-items'
                flash_text(warning, 'warning')
                items = items[:MAX_LEGEND_ITEMS]
            i = 0
            for item in items:
                color, marker_type = color_generator(i)
                filtered_df = df[df[self.cfg['color']] == item]
                draw_symbol(filtered_df,color, marker_type, item)
                i+=1
            self.plot.legend.location = legend_location


    def get_user_input(self):
        if st.session_state['project'] != self.project:
            st.write('eqal')
            self.init_data(self.project.data)
        else:
            st.write('ne')
            self.project = st.session_state['project']
        with st.expander('Plot properties', expanded=True):
            #title 
            group_by_options = [None] + self.project.group_fields()
            self.cfg['plot-title'] = st.text_input('Plot Title', value=self.cfg['plot-title'])
            self.cfg['plot-title-text-size'] = st.number_input('Plot title font size', min_value=0.1, max_value=5.0, value=self.cfg['plot-title-text-size'])
            id = HORIZONTAL_ALIGNEMENT_OPTIONS.index(self.cfg['plot-title-align'])
            self.cfg['plot-title-align'] = st.selectbox('Plot title alignment', options=HORIZONTAL_ALIGNEMENT_OPTIONS, index=id)
            id = group_by_options.index(self.cfg['group-plot-by'])
            self.cfg['group-plot-by'] = st.selectbox('Group plot by', options=group_by_options, index=id)
            id = group_by_options.index(self.cfg['color'])
            self.cfg['color'] = st.selectbox('Group Legend by', options=group_by_options, index=id)
            self.cfg['plot-width'] = st.number_input('Plot width', min_value= 100, max_value=2000, step=50, value=self.cfg['plot-width'])
            self.cfg['show-grid'] = st.checkbox('Show grid', value=self.cfg['show-grid'])
            self.cfg['show-tick-labels'] = st.checkbox('Show tick labels', value=self.cfg['show-tick-labels'])
            if self.cfg['show-tick-labels']:
                id = FONT_SIZES.index(self.cfg['tick-label-font-size'])
                self.cfg['tick-label-font-size'] = st.selectbox('Tick label font size', options=FONT_SIZES, index=id)
            id = FONT_SIZES.index(self.cfg['axis-title-font-size'])
            self.cfg['axis-title-font-size'] = st.selectbox('Axis title label font size', options=FONT_SIZES, index=id)
            id = IMAGE_FORMATS.index(self.cfg['image_format'])
            self.cfg['image_format'] = st.selectbox('Image output format', options=IMAGE_FORMATS, index=id)
        with st.expander('Marker properties', expanded=True):
            # https://github.com/d3/d3-3.x-api-reference/blob/master/Ordinal-Scales.md#categorical-colors
            self.cfg['marker-size'] = st.number_input('Marker size', min_value=1, max_value=50, step=1, value=int(self.cfg['marker-size']))
            self.cfg['color-palette'], self.cfg['color-number'] = colors.user_input_palette('Marker color palette', self.cfg['color-palette'], self.cfg['color-number'])
            id = MARKER_GENERATORS.index(self.cfg['marker-generator'])
            self.cfg['marker-generator'] = st.selectbox('Marker generator algorithm', options=MARKER_GENERATORS, index=id)
            self.cfg['marker-fill-alpha'] = st.number_input('Marker fill opacity', min_value=0.0,max_value=1.0,step=0.1, value=self.cfg['marker-fill-alpha'])
            self.cfg['marker-types'] = st.multiselect('Marker types', options=list(MarkerType), default=self.cfg['marker-types'])
            st.markdown('Tooltips')
            for key, value in self.project.fields.items():
                self.cfg['tooltips'][key] = st.checkbox(f"Show {value['label']}", value = self.cfg['tooltips'][key], key=key +'cb')


    def get_plot(self, df):
        self.plot = figure(width=int(self.cfg['plot-width']),
                           height=int(self.cfg['plot-width'] * sin60), 
                           y_range=(-figure_padding_bottom, int((200+gap+figure_padding_top) * sin60)),
                           x_range=(-figure_padding_left, 200 + gap + figure_padding_right))
        self.plot.add_tools(HoverTool(
                tooltips=self.get_tooltips(),
                formatters=self.get_tooltip_formatter(),
            ),
        )
        if self.cfg['plot-title'] != '':
            title = Title()
            placeholder = f"{{{self.cfg['group-plot-by']}}}"
            if placeholder in self.cfg['plot-title']:
                value = df.iloc[0][self.cfg['group-plot-by']]
                title.text = self.cfg['plot-title'].replace(placeholder, value)
            else:
                title.text = self.cfg['plot-title']
            title.text_font_size = f"{self.cfg['plot-title-text-size']}em"
            title.align = self.cfg['plot-title-align']
            self.plot.title = title

        self.draw_triangles()
        self.draw_axis()
        data_transformed = self.get_tranformed_data(df)
        self.draw_markers(data_transformed)
        self.plot.background_fill_color = None
        self.plot.border_fill_color = None
        return self.plot
    

    def show_save_file_button(self, p):
        # os.environ["PATH"] += os.pathsep + os.getcwd()
        #if st.button("Save png file", key=f'save_{random_string(5)}'):
        filename = get_random_filename('piper', self.cfg['image_format'])
        p.toolbar_location = None
        p.outline_line_color = None
        if self.cfg['image_format'] == 'png':
            export_png(p, filename=filename)
        else:
            p.output_backend = "svg"
            export_svgs(p, filename=filename)
        # flash_text(f"The Piper plot has been saved to **{filename}** and is ready for download", 'info')
        with open(filename, "rb") as file:
            btn = st.download_button(
                label="Download image",
                data=file,
                file_name=filename,
                mime="image/png"
            )

    def show_plot_footer(self, p, df:pd.DataFrame):
        with st.expander('Data', expanded=False):
            st.write(f"{len(df)} records")
            st.write(df)
            st.download_button(label="Download data as CSV",
                data=df.to_csv(sep=';').encode('utf-8'),
                file_name='fontus_piper_data.csv',
                mime='text/csv',
                key = f'save_button_{random_string(5)}'
            )
        self.show_save_file_button(p)

    def show_plot(self):
        if self.cfg['group-plot-by']:
            for item in self.project.codes[self.cfg['group-plot-by']]:
                df_filtered = self.data[self.data[self.cfg['group-plot-by']]==item]
                if len(df_filtered) > 0:
                    p = self.get_plot(df_filtered)
                    st.bokeh_chart(p)
                    self.show_plot_footer(p, self.data)
        else:
            p = self.get_plot(self.data)
            st.bokeh_chart(p)
            self.show_plot_footer(p, self.data)
       