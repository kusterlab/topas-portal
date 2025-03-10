import numpy as np
import plotly.io as pltio
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import scipy.spatial as scs
import scipy.cluster.hierarchy as sch

from collections import OrderedDict
from plotly.graph_objs import graph_objs


def create_dendrogram(
    X,
    orientation="bottom",
    labels=None,
    colorscale=None,
    distfun=None,
    linkagefun=lambda x: sch.linkage(x, "complete"),
    hovertext=None,
    color_threshold=None,
):

    s = X.shape
    if distfun is None:
        distfun = scs.distance.pdist

    dendrogram = _Dendrogram(
        X,
        orientation,
        labels,
        colorscale,
        distfun=distfun,
        linkagefun=linkagefun,
        hovertext=hovertext,
        color_threshold=color_threshold,
    )
    return graph_objs.Figure(data=dendrogram.data, layout=dendrogram.layout)


def get_piechart(
    labels: list = ["Oxygen", "Hydrogen", "Carbon_Dioxide", "Nitrogen"],
    values: list = [4500, 2500, 1053, 500],
):
    """
    Returns:
        JSON pie chart object for vue plotly on the frontend
    Inputs:
        
        :labels: list object with the names of the labels
        :values: list object with the values
    """
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3)])
    fig.update_layout(width=500, height=500)
    figure_data = pltio.to_json(fig)
    return figure_data


def get_barplot(df, x="sample", y="silhouette_score"):
    """
    Returns:
        JSON object for vue plotly
    Inputs:
        :df: dataFrame with three columns meta_data column is obligatory for coloring
        :x: name for first column
        :y: name for the second column
    """
    fig = px.histogram(df, x=x, y=y, color="meta_data", orientation="v", height=400)
    fig.update_layout(width=1400, height=600)
    figure_data = pltio.to_json(fig)
    return figure_data


def get_dendrogram(df: pd.DataFrame):
    """
    dendrograms plotly JSON
    Input : a pandas data frame with named columns and index
    Return a heatmap object as json
    """
    new_array = df.T.to_numpy()
    fig = create_dendrogram(new_array, labels=df.columns)
    fig.update_layout(width=800, height=500)
    figure_data = pltio.to_json(fig)
    return figure_data


def get_simple_heatmap(df: pd.DataFrame, title: str = "Scores"):
    """
    heatmap with no dendrograms on x or y axis
    Input : a pandas data frame with named columns and index
    Return a heatmap object as json
    """
    try:
        min_data = df.min().min()
        max_data = df.max().max()
        delta = abs(max_data - min_data)
        zero_half = abs(0 - min_data)
        zero_z_score = min(max(zero_half / delta, 0), 1)
        if np.isnan(zero_z_score):
            zero_z_score = 0

        # reverse order of rows because plotly plots the first row at the bottom
        df = df.iloc[::-1]

        fig = go.Figure(
            data=go.Heatmap(
                z=df,
                x=df.columns,
                y=df.index,
                colorscale=[[0, "blue"], [zero_z_score, "white"], [1, "red"]],
                hoverongaps=False,
            )
        )

        fig.update_layout(
            {"width": 800, "height": 800},
            title=title,
            xaxis_nticks=len(df.columns),
            yaxis_nticks=len(df.index),
        )

        figure_data = pltio.to_json(fig)
        return figure_data
    except Exception as err:
        print(err)
        return {}


def get_heatmap(df: pd.DataFrame):
    """
    heatmap with side and bottom dendrograms
    Input : a pandas data frame with named columns and index
    Return a heatmap object as json
    """
    data = df.fillna(0).copy()
    labels1 = data.columns
    labels2 = data.index
    data_t = data.transpose()
    fig = create_dendrogram(data_t, orientation="bottom", labels=labels1)
    for i in range(len(fig["data"])):
        fig["data"][i]["yaxis"] = "y2"

    # Create Side Dendrogram
    dendro_side = create_dendrogram(data, orientation="right", labels=labels2)
    for i in range(len(dendro_side["data"])):
        dendro_side["data"][i]["xaxis"] = "x2"

    # Add Side Dendrogram Data to Figure
    for dat in dendro_side["data"]:
        fig.add_trace(dat)

    # Create Heatmap
    dendro_leaves_y = dendro_side["layout"]["yaxis"]["ticktext"]
    dendro_leaves_x = fig["layout"]["xaxis"]["ticktext"]

    # updating the rows and columns
    dendro_leaves_x = list(map(str, dendro_leaves_x))
    dendro_leaves_y = list(map(str, dendro_leaves_y))
    heat_data = data.loc[dendro_leaves_y, dendro_leaves_x]

    heatmap = [
        go.Heatmap(
            x=dendro_leaves_x,
            y=dendro_leaves_y,
            z=heat_data,
            colorscale="reds",
            colorbar={"orientation": "h"},
        )
    ]
    heatmap[0]["x"] = fig["layout"]["xaxis"]["tickvals"]
    heatmap[0]["y"] = dendro_side["layout"]["yaxis"]["tickvals"]
    fig["layout"]["yaxis"]["tickvals"] = heatmap[0]["y"]
    fig["layout"]["yaxis"]["ticktext"] = np.array(dendro_leaves_y)

    # Add Heatmap Data to Figure
    for datt in heatmap:
        fig.add_trace(datt)

    # Edit Layout
    fig.update_layout(
        {"width": 800, "height": 800, "showlegend": False, "hovermode": "closest",}
    )
    # Edit xaxis

    fig.update_layout(
        xaxis={
            "domain": [0.15, 1],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "ticks": "",
        }
    )
    # Edit xaxis2
    fig.update_layout(
        xaxis2={
            "domain": [0, 0.15],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": True,
            "ticks": "",
        }
    )
    # Edit yaxis
    fig.update_layout(
        yaxis={
            "domain": [0, 0.85],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": False,
            "ticks": "",
        }
    )
    # Edit yaxis2
    fig.update_layout(
        yaxis2={
            "domain": [0.825, 0.975],
            "mirror": False,
            "showgrid": False,
            "showline": False,
            "zeroline": False,
            "showticklabels": True,
            "ticks": "",
        }
    )

    figure_data = pltio.to_json(fig)
    return figure_data


class _Dendrogram(object):
    """Refer to FigureFactory.create_dendrogram() for docstring."""

    def __init__(
        self,
        X,
        orientation="bottom",
        labels=None,
        colorscale=None,
        width=np.inf,
        height=np.inf,
        xaxis="xaxis",
        yaxis="yaxis",
        distfun=None,
        linkagefun=lambda x: sch.linkage(x, "complete"),
        hovertext=None,
        color_threshold=None,
    ):
        self.orientation = orientation
        self.labels = labels
        self.xaxis = xaxis
        self.yaxis = yaxis
        self.data = []
        self.leaves = []
        self.sign = {self.xaxis: 1, self.yaxis: 1}
        self.layout = {self.xaxis: {}, self.yaxis: {}}

        if self.orientation in ["left", "bottom"]:
            self.sign[self.xaxis] = 1
        else:
            self.sign[self.xaxis] = -1

        if self.orientation in ["right", "bottom"]:
            self.sign[self.yaxis] = 1
        else:
            self.sign[self.yaxis] = -1

        if distfun is None:
            distfun = scs.distance.pdist

        (dd_traces, xvals, yvals, ordered_labels, leaves) = self.get_dendrogram_traces(
            X, colorscale, distfun, linkagefun, hovertext, color_threshold
        )

        self.labels = ordered_labels
        self.leaves = leaves
        yvals_flat = yvals.flatten()
        xvals_flat = xvals.flatten()

        self.zero_vals = []

        for i in range(len(yvals_flat)):
            if yvals_flat[i] == 0.0 and xvals_flat[i] not in self.zero_vals:
                self.zero_vals.append(xvals_flat[i])

        if len(self.zero_vals) > len(yvals) + 1:
            l_border = int(min(self.zero_vals))
            r_border = int(max(self.zero_vals))
            correct_leaves_pos = range(
                l_border, r_border + 1, int((r_border - l_border) / len(yvals))
            )
            # Regenerating the leaves pos from the self.zero_vals with equally intervals.
            self.zero_vals = [v for v in correct_leaves_pos]

        self.zero_vals.sort()
        self.layout = self.set_figure_layout(width, height)
        self.data = dd_traces

    def get_color_dict(self, colorscale):

        d = {
            "r": "red",
            "g": "green",
            "b": "blue",
            "c": "cyan",
            "m": "magenta",
            "y": "yellow",
            "k": "black",
            # TODO: 'w' doesn't seem to be in the default color
            # palette in scipy/cluster/hierarchy.py
            "w": "white",
        }
        default_colors = OrderedDict(sorted(d.items(), key=lambda t: t[0]))

        if colorscale is None:
            rgb_colorscale = [
                "rgb(0,116,217)",  # blue
                "rgb(35,205,205)",  # cyan
                "rgb(61,153,112)",  # green
                "rgb(40,35,35)",  # black
                "rgb(133,20,75)",  # magenta
                "rgb(255,65,54)",  # red
                "rgb(255,255,255)",  # white
                "rgb(255,220,0)",  # yellow
            ]
        else:
            rgb_colorscale = colorscale

        for i in range(len(default_colors.keys())):
            k = list(default_colors.keys())[i]  # PY3 won't index keys
            if i < len(rgb_colorscale):
                default_colors[k] = rgb_colorscale[i]

        new_old_color_map = [
            ("C0", "b"),
            ("C1", "g"),
            ("C2", "r"),
            ("C3", "c"),
            ("C4", "m"),
            ("C5", "y"),
            ("C6", "k"),
            ("C7", "g"),
            ("C8", "r"),
            ("C9", "c"),
        ]
        for nc, oc in new_old_color_map:
            try:
                default_colors[nc] = default_colors[oc]
            except KeyError:
                # it could happen that the old color isn't found (if a custom
                # colorscale was specified), in this case we set it to an
                # arbitrary default.
                default_colors[nc] = "rgb(0,116,217)"

        return default_colors

    def set_axis_layout(self, axis_key):
        axis_defaults = {
            "type": "linear",
            "ticks": "outside",
            "mirror": "allticks",
            "rangemode": "tozero",
            "showticklabels": True,
            "zeroline": False,
            "showgrid": False,
            "showline": True,
        }

        if len(self.labels) != 0:
            axis_key_labels = self.xaxis
            if self.orientation in ["left", "right"]:
                axis_key_labels = self.yaxis
            if axis_key_labels not in self.layout:
                self.layout[axis_key_labels] = {}
            self.layout[axis_key_labels]["tickvals"] = [
                zv * self.sign[axis_key] for zv in self.zero_vals
            ]
            self.layout[axis_key_labels]["ticktext"] = self.labels
            self.layout[axis_key_labels]["tickmode"] = "array"

        self.layout[axis_key].update(axis_defaults)

        return self.layout[axis_key]

    def set_figure_layout(self, width, height):
        """
        Sets and returns default layout object for dendrogram figure.

        """
        self.layout.update(
            {
                "showlegend": False,
                "autosize": False,
                "hovermode": "closest",
                "width": width,
                "height": height,
            }
        )

        self.set_axis_layout(self.xaxis)
        self.set_axis_layout(self.yaxis)

        return self.layout

    def get_dendrogram_traces(
        self, X, colorscale, distfun, linkagefun, hovertext, color_threshold
    ):
        d = distfun(X)
        Z = linkagefun(d)
        P = sch.dendrogram(
            Z,
            orientation=self.orientation,
            labels=self.labels,
            no_plot=True,
            color_threshold=color_threshold,
        )
        icoord = np.array(P["icoord"])
        dcoord = np.array(P["dcoord"])
        ordered_labels = np.array(P["ivl"])
        color_list = np.array(P["color_list"])
        colors = self.get_color_dict(colorscale)

        trace_list = []

        for i in range(len(icoord)):
            # xs and ys are arrays of 4 points that make up the '∩' shapes
            # of the dendrogram tree
            if self.orientation in ["top", "bottom"]:
                xs = icoord[i]
            else:
                xs = dcoord[i]

            if self.orientation in ["top", "bottom"]:
                ys = dcoord[i]
            else:
                ys = icoord[i]
            color_key = color_list[i]
            hovertext_label = None
            if hovertext:
                hovertext_label = hovertext[i]
            trace = dict(
                type="scatter",
                x=np.multiply(self.sign[self.xaxis], xs),
                y=np.multiply(self.sign[self.yaxis], ys),
                mode="lines",
                marker=dict(color=colors[color_key]),
                text=hovertext_label,
                hoverinfo="text",
            )

            try:
                x_index = int(self.xaxis[-1])
            except ValueError:
                x_index = ""

            try:
                y_index = int(self.yaxis[-1])
            except ValueError:
                y_index = ""

            trace["xaxis"] = "x" + x_index
            trace["yaxis"] = "y" + y_index

            trace_list.append(trace)

        return trace_list, icoord, dcoord, ordered_labels, P["leaves"]
