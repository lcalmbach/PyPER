import pandas as pd
import numpy as np
import streamlit as st
from bokeh.models.tools import SaveTool
from bokeh.plotting import figure
# from bokeh.models import Legend, Range1d, LabelSet, Label, HoverTool, Arrow, NormalHead, OpenHead, VeeHead, Span, Grid, Line, LinearAxis, Plot, SingleIntervalTicker, FuncTickFormatter

import helper
import const as cn

class Boxplot:
    def __init__(self, df: pd.DataFrame, cfg: dict):
        self.cfg = cfg
        self.data = df

    def get_plot(self):
        # Find the quartiles and IQR foor each category
        groups = self.data.groupby('group')
        q1 = groups.quantile(q=0.25)
        q2 = groups.quantile(q=0.5)
        q3 = groups.quantile(q=0.75)
        iqr = q3 - q1
        upper = q3 + 1.5*iqr
        lower = q1 - 1.5*iqr

        # find the outliers for each category
        def outliers(group):
            cat = group.name
            result = group[(group.score > upper.loc[cat]['score']) | (group.score < lower.loc[cat]['score'])]['score']
            return result

        out = groups.apply(outliers).dropna()
        cats = self.data['group'].unique()
        if not out.empty:
            outx = list(out.index.get_level_values(0))
            outy = list(out.values)

        p = figure(tools="save", background_fill_color=self.cfg['background_fill_color'], title="", x_range=cats)

        p = figure(tools="", background_fill_color="#efefef", x_range=cats, toolbar_location=None)

        # if no outliers, shrink lengths of stems to be no longer than the minimums or maximums
        qmin = groups.quantile(q=0.00)
        qmax = groups.quantile(q=1.00)
        upper.score = [min([x,y]) for (x,y) in zip(list(qmax.loc[:,'score']),upper.score)]
        lower.score = [max([x,y]) for (x,y) in zip(list(qmin.loc[:,'score']),lower.score)]

        # stems
        p.segment(cats, upper.score, cats, q3.score, line_color="black")
        p.segment(cats, lower.score, cats, q1.score, line_color="black")

        # boxes
        p.vbar(cats, 0.7, q2.score, q3.score, fill_color="#E08E79", line_color="black")
        p.vbar(cats, 0.7, q1.score, q2.score, fill_color="#3B8686", line_color="black")

        # whiskers (almost-0 height rects simpler than segments)
        p.rect(cats, lower.score, 0.2, 0.01, line_color="black")
        p.rect(cats, upper.score, 0.2, 0.01, line_color="black")

        # outliers
        if not out.empty:
            p.circle(outx, outy, size=6, color="#F38630", fill_alpha=0.6)

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = "white"
        p.grid.grid_line_width = 2
        p.xaxis.major_label_text_font_size="16px"
        return p
