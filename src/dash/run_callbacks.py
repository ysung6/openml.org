import plotly.graph_objs as go
import re
from .layouts import get_layout_from_data, get_layout_from_task, get_layout_from_flow, get_layout_from_run
from plotly import tools
from dash.dependencies import Input, Output, State
import dash_html_components as html
import dash_core_components as dcc
from .helpers import *
import dash_table_experiments as dt
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve
from sklearn.preprocessing import label_binarize
import time
from .data_callbacks import register_data_callbacks


def register_run_callbacks(app):

    @app.callback(
        Output('runplot', 'children'),
        [Input('intermediate-value', 'children'),
         Input('url', 'pathname'),
         Input('runtable', 'data'),
         Input('runtable', 'selected_rows'),
         ])
    def run_plot(df_json, pathname, rows, selected_row_indices):
        """

        :param df_json: cached data
        :param pathname: url
        :param rows: rows of the feature table
        :param selected_row_indices: selected rows of the feature table
        :return: subplots containing violin plot or histogram for selected_row_indices
        """


        if '/dashboard/run' in pathname and df_json is not None:
            print('entered run update #1')
        else:
            return [], []
        df = pd.read_json(df_json, orient='split')
        rows = pd.DataFrame(rows)


        if len(selected_row_indices) != 0:

            selected_rows = rows.loc[selected_row_indices]["evaluations"].values
            numplots = len(selected_rows)

            i = numplots
            fig = tools.make_subplots(rows=numplots, cols=1)
            for metric in selected_rows:
                measure = df.loc[df['evaluations'] == metric]
                x = measure['results'].values[0]
                trace1 = go.Box(
                x=x,
                name=metric)
                fig.append_trace(trace1,i,1)
                i = i-1
            fig['layout'].update(title = 'Cross-validation details (10-fold Crossvalidation)',hovermode='closest', height=numplots*200, margin=dict(l=200))
        else:
            fig = []

        return html.Div(dcc.Graph(figure=fig))

    @app.callback(
        [Output('pr', 'children'),
         Output('roc','children')],
        [Input('intermediate-value', 'children'),
         Input('url', 'pathname'),
         Input('runtable', 'rows'),
         # Input('runtable', 'selected_row_indices'),
         ])
    def prchart(df_json, pathname, rows):

        if pathname is not None and 'dashboard/run' in pathname:
            id = int(re.search('run/(\d+)', pathname).group(1))
            print(id)
        items = vars(runs.get_run(int(id)))
        ID = items['output_files']['predictions']
        url = "https://www.openml.org/data/download/{}".format(ID) + "/predictions.arff"


        from scipy.io import arff
        import urllib.request
        import io  # for io.StringIO()

        ftpstream = urllib.request.urlopen(url)
        data, meta = arff.loadarff(io.StringIO(ftpstream.read().decode('utf-8')))
        df = pd.DataFrame(data)
        df['prediction'] = df['prediction'].str.decode('utf-8')
        df['correct'] = df['correct'].str.decode('utf-8')
        vals = df['correct'].unique()
        confidence = ["confidence." + str(val) for val in vals]
        # FOR BINARY


        y_codes = pd.Categorical(df['correct']).codes

        y_score = df[confidence[1]].values
        n_classes = df['correct'].nunique()
        data = []
        roc = []
        if n_classes == 2:
            _, idx = np.unique(y_codes, return_index=True)
            y_test = label_binarize(y_codes, classes=y_codes[np.sort(idx)])
            precision, recall, thresholds = precision_recall_curve(y_test, y_score, pos_label=1)
            fpr, tpr, rocthresh = roc_curve(y_test, y_score)

            h = ['Threshold: ' + value for value in thresholds.astype(str)]
            trace1 = go.Scatter(x=recall, y=precision, hovertext=h,
                                mode='lines',
                                line=dict(width=2, color='navy'),
                                name='Precision-Recall curve')

            layout = go.Layout(xaxis=dict(title='Recall'),
                               yaxis=dict(title='Precision'))

            fig = go.Figure(data=[trace1], layout=layout)

            #ROC
            h = ['Threshold: ' + value for value in rocthresh.astype(str)]
            trace2 = go.Scatter(x=fpr, y=tpr, hovertext=h,
                                mode='lines',
                                line=dict(width=2, color='navy'),
                                name='ROC chart')

            layout = go.Layout(xaxis=dict(title='FPR'),
                               yaxis=dict(title='TPR'))

            fig2 = go.Figure(data=[trace2], layout=layout)

        else:
            precision = dict()
            recall = dict()
            threshold = dict()
            rocthresh = dict()
            fpr = dict()
            tpr = dict()
            _, idx = np.unique(y_codes, return_index=True)
            y_test = label_binarize(y_codes, classes=y_codes[np.sort(idx)])
            for i in range(n_classes):
                y_score = df[confidence[i]].values
                precision[i], recall[i], threshold[i] = precision_recall_curve(y_test[:, i], y_score, pos_label=1)
                fpr[i], tpr[i], rocthresh[i] = roc_curve(y_test[:,i], y_score)

            for i in range(n_classes):
                h = ['Threshold: ' + value for value in threshold[i].astype(str)]
                trace3 = go.Scatter(x=recall[i], y=precision[i], name=confidence[i],
                                    hovertext=h,
                                    hoverinfo='text',
                                    hoverlabel=dict(namelength=-1),
                                    mode='lines',
                                    line=dict(width=2),
                                    )
                data.append(trace3)
                h1 = ['Threshold: ' + value for value in rocthresh[i].astype(str)]
                trace = go.Scatter(x=fpr[i], y=tpr[i], name=confidence[i],
                                   hovertext=h1,
                                   hoverinfo='text',
                                   hoverlabel=dict(namelength=-1),
                                   mode='lines',
                                   line=dict(width=2),
                                   )
                roc.append(trace)

            layout = go.Layout(title='PR curve',
                               xaxis=dict(title='Recall'),
                               yaxis=dict(title='Precision'))

            fig = go.Figure(data=data, layout=layout)


            layout = go.Layout(title='Extension of ROC to multi-class',
                               xaxis=dict(title='fpr'),
                               yaxis=dict(title='tpr'))

            fig2 = go.Figure(data=roc, layout=layout)
        graph = dcc.Graph(figure=fig)


        return html.Div(graph), html.Div(dcc.Graph(figure=fig2))
