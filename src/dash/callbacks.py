import re
from .layouts import get_layout_from_data, get_layout_from_task, get_layout_from_flow, get_layout_from_run
from dash.dependencies import Input, Output
import dash_html_components as html
from .helpers import *
from .data_callbacks import register_data_callbacks
from .task_callbacks import register_task_callbacks
from .flow_callbacks import register_flow_callbacks
from .run_callbacks import register_run_callbacks


def register_callbacks(app):
    """Register all callbacks of the dash app

    :param app: the dash application
    :return:
    """

    @app.callback([Output('page-content', 'children'),
                   Output('intermediate-value', 'children')],
                  [Input('url', 'pathname')])
    def render_layout(pathname):
        """
        Main callback invoked when a URL with a data/run/flow/task ID is entered.
        :param: pathname: str
            The URL entered, typically consists of dashboard/data/dataID or
            dashboard/task/ID
        :return: page-content: dash layout
            The basic layout of the dash application in the requested URL
        :return: intermediate-value: json
            Cached df in json format for sharing between callbacks
        """
        df = pd.DataFrame()
        if pathname is not None and '/dashboard/data' in pathname:
            data_id = int(re.search('data/(\d+)', pathname).group(1))
            layout, df = get_layout_from_data(data_id)
            cache = df.to_json(date_format='iso', orient='split')
            return layout, cache
        elif pathname is not None and 'dashboard/task' in pathname:
            task_id = int(re.search('task/(\d+)', pathname).group(1))
            layout, taskdf = get_layout_from_task(task_id)
            cache = taskdf.to_json(date_format='iso', orient='split')
            return layout, cache
        elif pathname is not None and 'dashboard/flow' in pathname:
            flow_id = int(re.search('flow/(\d+)', pathname).group(1))
            layout, flowdf = get_layout_from_flow(flow_id)
            cache = flowdf.to_json(date_format='iso', orient='split')
            return layout, cache
        elif pathname is not None and 'dashboard/run' in pathname:
            run_id = int(re.search('run/(\d+)', pathname).group(1))
            layout, rundf = get_layout_from_run(run_id)
            cache = rundf.to_json(date_format='iso', orient='split')
            return layout, cache
        else:
            index_page = html.Div([html.H1('Welcome to dash dashboard')])
            cache = df.to_json(date_format='iso', orient='split')
            return index_page, cache

    register_data_callbacks(app)
    register_run_callbacks(app)
    register_task_callbacks(app)
    register_flow_callbacks(app)





