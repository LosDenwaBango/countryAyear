import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import os
import requests
import numpy as np
import datetime
import pycountry
import pycountry_convert
import country_converter as coco
from PIL import Image
import base64
import io
from dash.dependencies import ALL, MATCH
import dash_mantine_components as dmc
from dash.exceptions import PreventUpdate
from dash import ctx
from dash import callback_context

# --- Data Preparation (same as Streamlit version) ---
continent_map = {
    'AF': 'Africa',
    'AS': 'Asia',
    'EU': 'Europe',
    'NA': 'North America',
    'OC': 'Oceania',
    'SA': 'South America',
    'AN': 'Antarctica'
}
UN_MEMBER_ALPHA2 = set([
    'AF', 'AL', 'DZ', 'AD', 'AO', 'AG', 'AR', 'AM', 'AU', 'AT', 'AZ',
    'BS', 'BH', 'BD', 'BB', 'BY', 'BE', 'BZ', 'BJ', 'BT', 'BO', 'BA', 'BW',
    'BR', 'BN', 'BG', 'BF', 'BI', 'CV', 'KH', 'CM', 'CA', 'CF', 'TD', 'CL',
    'CN', 'CO', 'KM', 'CD', 'CG', 'CR', 'CI', 'HR', 'CU', 'CY', 'CZ', 'DK',
    'DJ', 'DM', 'DO', 'EC', 'EG', 'SV', 'GQ', 'ER', 'EE', 'SZ', 'ET', 'FJ',
    'FI', 'FR', 'GA', 'GM', 'GE', 'DE', 'GH', 'GR', 'GD', 'GT', 'GN', 'GW',
    'GY', 'HT', 'HN', 'HU', 'IS', 'IN', 'ID', 'IR', 'IQ', 'IE', 'IL', 'IT',
    'JM', 'JP', 'JO', 'KZ', 'KE', 'KI', 'KP', 'KR', 'KW', 'KG', 'LA', 'LV',
    'LB', 'LS', 'LR', 'LY', 'LI', 'LT', 'LU', 'MG', 'MW', 'MY', 'MV', 'ML',
    'MT', 'MH', 'MR', 'MU', 'MX', 'FM', 'MD', 'MC', 'MN', 'ME', 'MA', 'MZ',
    'MM', 'NA', 'NR', 'NP', 'NL', 'NZ', 'NI', 'NE', 'NG', 'MK', 'NO', 'OM',
    'PK', 'PW', 'PS', 'PA', 'PG', 'PY', 'PE', 'PH', 'PL', 'PT', 'QA', 'RO',
    'RU', 'RW', 'KN', 'LC', 'VC', 'WS', 'SM', 'ST', 'SA', 'SN', 'RS', 'SC',
    'SL', 'SG', 'SK', 'SI', 'SB', 'SO', 'ZA', 'SS', 'ES', 'LK', 'SD', 'SR',
    'SE', 'CH', 'SY', 'TW', 'TJ', 'TZ', 'TH', 'TL', 'TG', 'TO', 'TT', 'TN',
    'TR', 'TM', 'UG', 'UA', 'AE', 'GB', 'US', 'UY', 'UZ', 'VU', 'VA', 'VE',
    'VN', 'YE', 'ZM', 'ZW', 'AQ'
])
COUNTRY_LIST = []
def get_continent(alpha_2):
    special_cases = {
        'AQ': 'Antarctica',
        'TL': 'Asia',
        'VA': 'Europe',
        'TR': 'Europe',
    }
    if alpha_2 in special_cases:
        return special_cases[alpha_2]
    try:
        continent_code = pycountry_convert.country_alpha2_to_continent_code(alpha_2)
        return continent_map.get(continent_code, 'Unknown')
    except Exception:
        return 'Unknown'
for country in list(pycountry.countries):
    if hasattr(country, 'alpha_2') and country.alpha_2 in UN_MEMBER_ALPHA2:
        short_name = coco.convert(names=country.alpha_2, to='name_short')
        COUNTRY_LIST.append({
            "name": short_name,
            "alpha_2": country.alpha_2,
            "continent": get_continent(country.alpha_2)
        })
country_options = [f"{c['name']} ({c['alpha_2']})" for c in COUNTRY_LIST]

# --- Dash App Layout ---
today = datetime.date.today()
current_year = today.year
current_month = today.month
months_full = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.layout = dmc.MantineProvider(
    html.Div([
        html.Div([
            dbc.Container([
                html.H2("A Country a Year", style={"marginBottom": "16px"}),
                html.Div(
                    [
                        "This tool charts the number of countries you've visited over time and compares it to your age.",
                        html.Br(),
                        "The challenge?  Always try to stay ahead; visit more countries than the number of years you've been alive.",
                        html.Br(),
                        "You're not competing against other people....you're competing against time itself!"
                    ],
                    style={
                        "fontSize": "16px",
                        "color": "#444",
                        "marginBottom": "24px",
                        "marginTop": "0px",
                        "textAlign": "left"
                    }
                ),
                # Subheader: Your details
                html.Div("Your details", style={"fontSize": 18, "fontWeight": 600, "marginTop": 0, "marginBottom": 12}),
                # Name input row
                html.Div([
                    html.Div("What is your name? (optional)", style={"fontSize": 15, "fontWeight": 400, "color": "#444", "marginBottom": 6, "width": "220px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "10px", "textAlign": "left"}),
                    dcc.Input(id="user_name", type="text", placeholder="Enter your name...", style={"width": "220px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "20px", "fontSize": 15, "padding": "6px 10px", "borderRadius": "6px", "border": "1px solid #ccc"}),
                ], style={"marginBottom": "18px", "display": "flex", "alignItems": "center"}),
                # Date of birth selectors row
                html.Div([
                    html.Div("When were you born?", style={"fontSize": 15, "fontWeight": 400, "color": "#444", "marginBottom": 6, "width": "220px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "10px", "textAlign": "left"}),
            dcc.Dropdown(
                id="dob_year",
                options=[{"label": str(y), "value": y} for y in range(1900, current_year + 1)],
                value=1990,
                clearable=False,
                style={"width": "140px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "20px"}
            ),
            dcc.Dropdown(
                id="dob_month",
                        options=[{"label": month, "value": i+1} for i, month in enumerate(months_full[:current_month])],
                value=1,
                clearable=False,
                style={"width": "120px", "display": "inline-block", "verticalAlign": "middle"}
            ),
        ], style={"marginBottom": "24px", "display": "flex", "alignItems": "center"}),
                # Subheader: Travel timeline
                html.H4("Travel timeline", style={"marginTop": "12px", "marginBottom": "12px"}),
                html.Div([
                    # Big header 'Timeline of first visits' now removed, only subheader remains
            dmc.MultiSelect(
                id="country_select",
                        data=[label for label in country_options],
                value=[],
                        placeholder="Where have you visited?",
                searchable=True,
                clearable=True,
                maxDropdownHeight=300,
                        style={"width": "510px"},
                        disabled=True
                    ),
                    dcc.Interval(id="country_select_timer", interval=2000, n_intervals=0, max_intervals=1),
                ], style={"flex": 1, "minWidth": "520px", "maxWidth": "600px", "marginBottom": "24px"}),
                html.Div(
                    "When did you first visit these countries?",
                    id="visit_countries_label",
                    style={"fontSize": 14, "marginBottom": "18px", "display": "none"}
                ),
                html.Div(id="visit_inputs", style={"marginTop": "8px", "marginBottom": "18px"}),
                # Residence section, toggled by button (move back above Generate)
                html.Div([
                    html.Div("Countries of residence", style={"fontSize": 17, "fontWeight": 600, "marginBottom": "6px"}),
                    html.Div(id="residence_periods_container", style={"marginBottom": "18px"}),
                    html.Button("Add residence period", id="add_residence_period_btn", n_clicks=0, style={"backgroundColor": "#e0e0e0", "color": "#222", "border": "none", "padding": "8px 14px", "marginTop": "8px", "borderRadius": "6px", "fontWeight": 600, "fontSize": "14px", "cursor": "pointer"}),
                ], id="residence_section", style={"display": "none", "marginTop": "32px", "minWidth": "520px", "maxWidth": "600px"}),
        html.Br(),
                html.Div([
                    html.Button("Add countries of residence", id="toggle_residence_btn", n_clicks=0, style={"backgroundColor": "#e0e0e0", "color": "#222", "border": "none", "padding": "10px 18px", "marginRight": "16px", "borderRadius": "6px", "fontWeight": 600, "fontSize": "15px", "cursor": "pointer"}),
                    dbc.Button("Generate!", id="generate_btn", color="primary", n_clicks=0),
                ], style={"display": "flex", "flexDirection": "row", "alignItems": "center"}),
            ], style={"maxWidth": "1200px", "margin": "0 auto"}),
        html.Br(),
            html.Div(id="summary"),
        dcc.Loading(
            id="loading-plot",
            type="default",
            children=[html.Div(id="graph_container")]
        ),
        ], style={"padding": "32px 32px 32px 32px", "background": "#fff", "borderRadius": "18px", "boxShadow": "0 2px 12px 0 rgba(0,0,0,0.03)", "maxWidth": "900px", "margin": "0 auto"})
    ], style={"background": "#eafbe7", "minHeight": "100vh", "width": "100vw", "paddingTop": "40px"})
)

# --- Dynamic Inputs for Visit Dates ---
@app.callback(
    Output("visit_inputs", "children"),
    Input("country_select", "value"),
    State("dob_month", "value"),
    State("dob_year", "value"),
    State({"type": "visit_year", "code": ALL}, "value"),
    State({"type": "visit_month", "code": ALL}, "value"),
    State({"type": "visit_year", "code": ALL}, "id"),
    State({"type": "visit_month", "code": ALL}, "id"),
    prevent_initial_call=False
)
def update_visit_inputs(selected_labels, dob_month, dob_year, visit_years, visit_months, year_ids, month_ids):
    if not selected_labels:
        return ""
    import datetime
    default_month = dob_month or 1
    default_year = dob_year or 1990
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    # Build a dict of selected years for each country code
    selected_year_dict = {}
    if year_ids and visit_years:
        for yid, yval in zip(year_ids, visit_years):
            if yid and isinstance(yid, dict) and "code" in yid:
                selected_year_dict[yid["code"]] = yval
    # Build a dict of selected months for each country code
    selected_month_dict = {}
    if month_ids and visit_months:
        for mid, mval in zip(month_ids, visit_months):
            if mid and isinstance(mid, dict) and "code" in mid:
                selected_month_dict[mid["code"]] = mval
    # Sort selected_labels by (year, month) if possible
    label_to_date = {}
    for label in selected_labels:
        c = next(c for c in COUNTRY_LIST if f"{c['name']} ({c['alpha_2']})" == label)
        code = c["alpha_2"]
        year = selected_year_dict.get(code, default_year)
        month = selected_month_dict.get(code, default_month)
        label_to_date[label] = (year, month)
    sorted_labels = sorted(selected_labels, key=lambda l: label_to_date[l])
    # --- Add column headers for visit table ---
    header = html.Div([
        html.Div('Country', style={'width': '280px', 'fontSize': 13, 'color': '#888', 'fontWeight': 500, 'textAlign': 'left', 'lineHeight': '20px', 'marginRight': '8px'}),
        html.Div('First visited in...', style={'width': '180px', 'fontSize': 13, 'color': '#888', 'fontWeight': 500, 'textAlign': 'center', 'lineHeight': '20px', 'marginRight': '16px', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
        html.Div('', style={'width': '120px'}),
        html.Div('', style={'flex': 1}),
    ], style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'center', 'marginBottom': '2px', 'marginLeft': '2px'})
    inputs = []
    for label in sorted_labels:
        c = next(c for c in COUNTRY_LIST if f"{c['name']} ({c['alpha_2']})" == label)
        code = c["alpha_2"]
        selected_year = selected_year_dict.get(code, default_year)
        selected_month = selected_month_dict.get(code, default_month)
        # For visit selectors, allow any year/month from dob to current year/current month
        year_options = [y for y in range(default_year, current_year + 1)]
        # If selected_year is in the future, reset to current_year
        if selected_year > current_year:
            selected_year = current_year
        # Restrict month options
        def get_month_options(year):
            if year == default_year and year == current_year:
                # If dob year is also current year, restrict from dob month to current month
                return [(months_full[m-1], m) for m in range(default_month, current_month+1)]
            elif year == default_year:
                # If dob year, allow from dob month to December
                return [(months_full[m-1], m) for m in range(default_month, 13)]
            elif year == current_year:
                # If current year, allow from Jan to current month
                return [(months_full[m-1], m) for m in range(1, current_month+1)]
            else:
                # Any other year, allow all months
                return [(months_full[m-1], m) for m in range(1, 13)]
        month_options = get_month_options(selected_year)
        # If selected_month is not in month_options, pick the first valid month
        valid_month_values = [v for _, v in month_options]
        if selected_month not in valid_month_values:
            selected_month = valid_month_values[0]
        row = html.Div([
            html.Div(
                html.B(c['name'], style={"fontSize": 13, "textAlign": "left"}),
                style={"width": "220px", "display": "inline-block", "marginRight": "10px"}
            ),
            dcc.Dropdown(
                id={"type": "visit_year", "code": code},
                options=[{"label": str(y), "value": y} for y in year_options],
                value=selected_year,
                clearable=False,
                style={"width": "140px", "display": "inline-block", "verticalAlign": "middle", "marginRight": "20px"}
            ),
            dcc.Dropdown(
                id={"type": "visit_month", "code": code},
                options=[{"label": label, "value": value} for label, value in month_options],
                value=selected_month,
                clearable=False,
                style={"width": "120px", "maxHeight": "120px", "display": "inline-block", "verticalAlign": "middle"}
            ),
        ], style={"marginBottom": "18px", "display": "flex", "alignItems": "center", "maxWidth": "600px"})
        inputs.append(row)
    return [header] + inputs

# --- Dynamic month options for each visit selector ---
@app.callback(
    Output({"type": "visit_month", "code": MATCH}, "options"),
    Output({"type": "visit_month", "code": MATCH}, "value"),
    Input({"type": "visit_year", "code": MATCH}, "value"),
    State("dob_month", "value"),
    State("dob_year", "value"),
    State({"type": "visit_month", "code": MATCH}, "value"),
    State({"type": "visit_year", "code": MATCH}, "id"),
)
def update_visit_month_options(selected_year, dob_month, dob_year, selected_month, year_id):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    default_month = dob_month or 1
    default_year = dob_year or 1990
    if selected_year == default_year and selected_year == current_year:
        month_options = [(months_full[m-1], m) for m in range(default_month, current_month+1)]
    elif selected_year == default_year:
        month_options = [(months_full[m-1], m) for m in range(default_month, 13)]
    elif selected_year == current_year:
        month_options = [(months_full[m-1], m) for m in range(1, current_month+1)]
    else:
        month_options = [(months_full[m-1], m) for m in range(1, 13)]
    valid_month_values = [v for _, v in month_options]
    if selected_month not in valid_month_values:
        selected_month = valid_month_values[0]
    return ([{"label": label, "value": value} for label, value in month_options], selected_month)

# --- Main Callback: Generate Plot ---
@app.callback(
    Output("summary", "children"),
    Output("graph_container", "children"),
    Input("generate_btn", "n_clicks"),
    State("dob_month", "value"),
    State("dob_year", "value"),
    State("country_select", "value"),
    State({"type": "visit_month", "code": dash.ALL}, "value"),
    State({"type": "visit_year", "code": dash.ALL}, "value"),
    State({"type": "visit_month", "code": dash.ALL}, "id"),
    State({"type": "visit_year", "code": dash.ALL}, "id"),
    State({"type": "res_country", "index": dash.ALL}, "value"),
    State({"type": "res_from_year", "index": dash.ALL}, "value"),
    State({"type": "res_from_month", "index": dash.ALL}, "value"),
    State({"type": "res_until_year", "index": dash.ALL}, "value"),
    State({"type": "res_until_month", "index": dash.ALL}, "value"),
    State("user_name", "value"),
    prevent_initial_call=True
)
def generate_plot(n_clicks, dob_month, dob_year, selected_labels, visit_months, visit_years, month_ids, year_ids, res_countries, res_from_years, res_from_months, res_until_years, res_until_months, user_name):
    if not selected_labels:
        return "Please select at least one country and enter the age you first visited.", None
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    visit_info = {}
    for m_id, y_id, m_val, y_val in zip(month_ids, year_ids, visit_months, visit_years):
        code = m_id["code"]
        visit_info[code] = {"visit_month": m_val or 1, "visit_year": y_val or 1990}
    visited = []
    for label in selected_labels:
        c = next(c for c in COUNTRY_LIST if f"{c['name']} ({c['alpha_2']})" == label)
        code = c["alpha_2"]
        info = visit_info.get(code, {"visit_month": 1, "visit_year": 1990})
        age = (info["visit_year"] - dob_year) + (info["visit_month"] - dob_month) / 12
        visited.append({'country': c, 'age': age, 'visit_month': info["visit_month"], 'visit_year': info["visit_year"]})
    visited_sorted = sorted(visited, key=lambda x: x['age'])
    visited_sorted_chart = list(reversed(visited_sorted))
    if not visited_sorted_chart:
        return "Please select at least one country and enter the age you first visited.", None
    country_names = [c['country']['name'] for c in visited_sorted_chart]
    ages = [c['age'] for c in visited_sorted_chart]
    codes = [c['country']['alpha_2'] for c in visited_sorted_chart]
    today = datetime.date.today()
    birth_date = datetime.date(dob_year, dob_month, 1)
    current_age = (today.year - birth_date.year) + (today.month - birth_date.month) / 12
    max_visit_age = max(ages) if ages else current_age
    x_axis_max = max(current_age, max_visit_age) + max(1, min(2, current_age * 0.2))
    n_countries = len(visited_sorted_chart)
    flag_height_px = min(82, max(42, 62))
    slot_height = flag_height_px + 2
    chart_height = max(600, n_countries * slot_height)
    pixels_per_data_unit = chart_height / n_countries if n_countries > 0 else 1
    margin_px = 1
    margin_data_units = margin_px / pixels_per_data_unit
    bar_height = 1.0 - 2 * margin_data_units
    flag_height = bar_height - 2 * margin_data_units
    y_pos = np.arange(len(visited_sorted_chart))
    fig = go.Figure()
    # Draw subtle vertical grid lines for each year, and more prominent for each 5 years
    for age in range(0, int(current_age) + 1):
        if age % 5 == 0:
            fig.add_shape(type="line", x0=age, x1=age, y0=-0.5, y1=len(visited_sorted_chart)-0.5,
                          line=dict(color="#cccccc", dash="dot", width=1.5), layer="below")
        elif age > 0:
            fig.add_shape(type="line", x0=age, x1=age, y0=-0.5, y1=len(visited_sorted_chart)-0.5,
                          line=dict(color="#eeeeee", dash="dot", width=1), layer="below")
    zebra_colors = ['#d0f5df', '#b2eac7']
    n_ticks = len(visited_sorted_chart)
    # --- Residence period extraction from dynamic rows ---
    residence_periods = []
    for country_label, from_year, from_month, until_year, until_month in zip(res_countries, res_from_years, res_from_months, res_until_years, res_until_months):
        if not country_label:
            continue
        c = next((c for c in COUNTRY_LIST if f"{c['name']} ({c['alpha_2']})" == country_label), None)
        if not c:
            continue
        code = c["alpha_2"]
        from_age = (from_year - dob_year) + (from_month - dob_month) / 12
        until_age = (until_year - dob_year) + (until_month - dob_month) / 12
        residence_periods.append({'code': code, 'from_age': from_age, 'until_age': until_age})
    for i, c in enumerate(visited_sorted_chart):
        code = c['country']['alpha_2']
        block = ((n_ticks - 1 - i) // 5) % 2
        bar_color = zebra_colors[block]
        # Draw the main bar (full period)
        bar_start = c['age']
        bar_end = current_age
        fig.add_trace(go.Bar(
            y=[i],
            x=[bar_end - bar_start],
            base=bar_start,
            orientation='h',
            marker=dict(color=bar_color),
            width=bar_height,
            showlegend=False,
            hoverinfo='none',
        ))
        # Draw all gold residence bars for this country
        for period in residence_periods:
            if period['code'] == code:
                res_start = max(period['from_age'], bar_start)
                res_end = min(period['until_age'], bar_end)
                if res_end > res_start:
                    # Use deeper gold for dark green stripes, lighter gold for light green stripes
                    residence_gold = '#ffd700' if block == 1 else '#ffe066'
                    fig.add_trace(go.Bar(
                        y=[i],
                        x=[res_end - res_start],
                        base=res_start,
                        orientation='h',
                        marker=dict(color=residence_gold),
            width=bar_height,
            showlegend=False,
            hoverinfo='none',
        ))
    # Add flag images
    for i, c in enumerate(visited_sorted_chart):
        code = c['country']['alpha_2']
        flag_b64 = get_flag_base64(code)
        if flag_b64:
            flag_sizex = 2.5
            flag_x = c['age']
            # If flag would overflow right edge, center it on the bar
            if flag_x + flag_sizex > x_axis_max:
                flag_x = min(x_axis_max - flag_sizex / 2, max(flag_sizex / 2, c['age']))
                xanchor = "center"
            else:
                xanchor = "left"
            fig.add_layout_image(
                dict(
                    source=flag_b64,
                    xref="x",
                    yref="y",
                    x=flag_x,
                    y=i,
                    sizex=flag_sizex,
                    sizey=flag_height,
                    xanchor=xanchor,
                    yanchor="middle",
                    layer="above",
                    sizing="contain"
                )
            )
    # --- X-axis ticks: only up to current_age ---
    x_tick_step = 5 if current_age > 10 else 1
    x_tick_end = int(current_age) if current_age % 1 == 0 else int(current_age) + 1
    x_tickvals = list(range(0, x_tick_end + 1, x_tick_step))
    if x_tickvals[-1] < round(current_age):
        x_tickvals.append(round(current_age))
    x_tickvals = [v for v in x_tickvals if v <= current_age]
    x_ticktext = [str(v) for v in x_tickvals]
    fig.update_xaxes(title_text="Age", range=[0, x_axis_max], linewidth=3, linecolor="black", showline=False, zeroline=False, tickvals=x_tickvals, ticktext=x_ticktext)
    # Robust y-axis ticks: 0 at bottom, 5, 10, ... at correct places, topmost value always labeled
    n_ticks = len(visited_sorted_chart)
    tickvals = [n_ticks - 0.5 - i*5 for i in range((n_ticks // 5) + 1)]
    ticktext = [str(i*5) for i in range((n_ticks // 5) + 1)]
    if n_ticks % 5 != 0:
        tickvals = [-0.5] + tickvals
        ticktext = [str(n_ticks)] + ticktext
    fig.update_yaxes(
        tickvals=tickvals,
        ticktext=ticktext,
        range=[-0.5, len(visited_sorted_chart)-0.5],
        autorange=False,
        title_text="Total countries visited",
        title_font=dict(size=16, family="Arial, sans-serif", color="black"),
        showticklabels=True,
        showline=False,
        linewidth=3,
        linecolor="black"
    )
    # Add a custom vertical black line for the y-axis
    fig.add_shape(
        type="line",
        x0=0, x1=0,
        y0=-0.5, y1=len(visited_sorted_chart)-0.5,
        line=dict(color="black", width=4),
        layer="above"
    )
    # Add country name/age annotations, dynamically position to right or left of flag
    label_width = 2.5  # estimate of label width in data units
    for i, c in enumerate(visited_sorted_chart):
        visit_age = c['age']
        # Default: place to right of flag
        ann_x = visit_age + 2.7
        ann_xanchor = "left"
        # If label would overflow right edge, place to left
        if ann_x + label_width > x_axis_max:
            ann_x = max(visit_age - 2.7, 0)
            ann_xanchor = "right"
        fig.add_annotation(
            x=ann_x,
            y=i,
            text=f"{c['country']['name']} ({c['age']:.1f})",
            showarrow=False,
            font=dict(size=14, family="Arial, sans-serif", color="#222"),
            xanchor=ann_xanchor,
            yanchor="middle",
            align="left",
            bgcolor="rgba(255,255,255,0.0)",
            borderpad=2,
            opacity=1
        )
    fig.update_layout(
        title={"text": "Countries visited by age", "x": 0.5, "xanchor": "center"},
        height=chart_height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=40, t=80, b=40),
        bargap=0,
        bargroupgap=0,
        barmode='overlay',
        yaxis_autorange="reversed",
    )
    # Restore the thin black line at the bottom of the lowest bar to mimic the x-axis
    fig.add_shape(type="line", x0=0, x1=current_age, y0=len(visited_sorted_chart)-0.5, y1=len(visited_sorted_chart)-0.5, line=dict(color="black", width=2), layer="above")
    n_countries = len(visited_sorted_chart)
    age_now = max(ages) if ages else 0
    percent = (n_countries / current_age) * 100 if current_age > 0 else 0
    # --- SUMMARY TEXT ---
    summary_text = html.Div([
        html.Div(f"You have visited {n_countries} countries, which is {percent:.1f}% of your age.", style={"fontSize": 18, "fontWeight": 600, "marginBottom": "8px"})
    ])
    # --- Place summary above chart ---
    download_button = dbc.Button(
        "Download chart as PNG",
        id="download_chart_btn",
        n_clicks=0,
        color="primary",
        style={"marginTop": "18px", "marginBottom": "8px"}
    )
    # Legend flag: use first visited country or default to Cuba
    if visited_sorted_chart:
        first_flag_code = visited_sorted_chart[0]['country']['alpha_2'].lower()
    else:
        first_flag_code = 'cu'
    flag_url = f"https://flagcdn.com/w20/{first_flag_code}.png"
    return (
        summary_text,
        html.Div([
            html.Div([
                # Split green swatch
                html.Span([
                    html.Div(style={"background": "#b2eac7", "height": "9px", "width": "18px", "borderTopLeftRadius": "3px", "borderTopRightRadius": "3px"}),
                    html.Div(style={"background": "#d0f5df", "height": "9px", "width": "18px", "borderBottomLeftRadius": "3px", "borderBottomRightRadius": "3px"}),
                ], style={"display": "inline-block", "width": "18px", "height": "18px", "verticalAlign": "middle", "marginRight": "8px", "overflow": "hidden"}),
                html.Span("Country visited", style={"fontWeight": 600, "fontSize": "15px", "marginRight": "24px", "verticalAlign": "middle"}),
                # Split gold swatch
                html.Span([
                    html.Div(style={"background": "#ffd700", "height": "9px", "width": "18px", "borderTopLeftRadius": "3px", "borderTopRightRadius": "3px"}),
                    html.Div(style={"background": "#ffe066", "height": "9px", "width": "18px", "borderBottomLeftRadius": "3px", "borderBottomRightRadius": "3px"}),
                ], style={"display": "inline-block", "width": "18px", "height": "18px", "verticalAlign": "middle", "marginRight": "8px", "overflow": "hidden"}),
                html.Span("Where I lived", style={"fontWeight": 600, "fontSize": "15px", "marginRight": "8px", "verticalAlign": "middle"}),
                html.Img(src=flag_url, style={"width": "18px", "height": "14px", "marginRight": "8px", "verticalAlign": "middle", "border": "1px solid #bbb", "borderRadius": "2px"}),
                html.Span("Country first visited", style={"fontWeight": 600, "fontSize": "15px", "verticalAlign": "middle"}),
            ], style={"display": "flex", "flexDirection": "row", "alignItems": "center", "marginBottom": "10px", "marginTop": "0", "marginLeft": "0"}),
            dcc.Graph(figure=fig, id="country_plot", style={"width": "100%", "height": f"{chart_height}px", "marginLeft": 0}),
            download_button
        ])
    )

# Add clientside callback to trigger Plotly downloadImage
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            var graphDiv = document.getElementById('country_plot');
            if (graphDiv && window.Plotly) {
                window.Plotly.downloadImage(graphDiv, {format: 'png', filename: 'countries_by_age'});
            }
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output('download_chart_btn', 'n_clicks'),
    Input('download_chart_btn', 'n_clicks')
)

# --- Helper: Download and cache flag images as base64 ---
FLAG_DIR = "Flags"
os.makedirs(FLAG_DIR, exist_ok=True)
def get_flag_base64(code):
    flag_path = os.path.join(FLAG_DIR, f"{code}.png")
    if not os.path.exists(flag_path):
        url = f"https://flagcdn.com/w40/{code.lower()}.png"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(flag_path, "wb") as f:
                f.write(r.content)
        except Exception:
            return None
    try:
        with open(flag_path, "rb") as f:
            img = Image.open(io.BytesIO(f.read())).convert("RGBA")
            # Add 2px transparent border to top and bottom
            border_px = 2
            new_width, new_height = img.width, img.height + 2 * border_px
            new_img = Image.new("RGBA", (new_width, new_height), (255, 255, 255, 0))
            new_img.paste(img, (0, border_px))
            buffered = io.BytesIO()
            new_img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_b64}"
    except Exception:
        return None

@app.callback(
    Output("dob_month", "options"),
    Input("dob_year", "value")
)
def update_dob_month_options(selected_year):
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    if selected_year == current_year:
        return [{"label": month, "value": i+1} for i, month in enumerate(months_full[:current_month])]
    else:
        return [{"label": month, "value": i+1} for i, month in enumerate(months_full)]

# --- Enable country select after 3 seconds ---
@app.callback(
    Output("country_select", "disabled"),
    Input("country_select_timer", "n_intervals"),
    prevent_initial_call=False
)
def enable_country_select(n_intervals):
    return False if n_intervals and n_intervals > 0 else True

# --- Toggle residence section visibility ---
@app.callback(
    Output("residence_section", "style"),
    Input("toggle_residence_btn", "n_clicks"),
    State("residence_section", "style"),
    prevent_initial_call=False
)
def toggle_residence_section(n_clicks, current_style):
    if not n_clicks or n_clicks % 2 == 0:
        # Hide section
        style = dict(current_style) if current_style else {}
        style["display"] = "none"
        return style
    else:
        # Show section
        style = dict(current_style) if current_style else {}
        style["display"] = "block"
        return style

# --- Residence periods: dynamic rows ---
@app.callback(
    Output('residence_periods_container', 'children'),
    Input('add_residence_period_btn', 'n_clicks'),
    Input({'type': 'remove_residence_period', 'index': ALL}, 'n_clicks'),
    Input('residence_section', 'style'),
    Input({'type': 'res_country', 'index': ALL}, 'value'),
    Input({'type': 'res_from_year', 'index': ALL}, 'value'),
    Input({'type': 'res_from_month', 'index': ALL}, 'value'),
    Input({'type': 'res_until_year', 'index': ALL}, 'value'),
    Input({'type': 'res_until_month', 'index': ALL}, 'value'),
    State('residence_periods_container', 'children'),
    State('country_select', 'value'),
    State('dob_year', 'value'),
    State('dob_month', 'value'),
    State({'type': 'visit_year', 'code': ALL}, 'value'),
    State({'type': 'visit_month', 'code': ALL}, 'value'),
    State({'type': 'visit_year', 'code': ALL}, 'id'),
    State({'type': 'visit_month', 'code': ALL}, 'id'),
    State({'type': 'res_country', 'index': ALL}, 'value'),
    State({'type': 'res_from_year', 'index': ALL}, 'value'),
    State({'type': 'res_from_month', 'index': ALL}, 'value'),
    State({'type': 'res_until_year', 'index': ALL}, 'value'),
    State({'type': 'res_until_month', 'index': ALL}, 'value'),
    prevent_initial_call=False
)
def update_residence_periods(add_clicks, remove_clicks, res_section_style, input_countries, input_from_years, input_from_months, input_until_years, input_until_months, current_children, visited_countries, dob_year, dob_month, visit_years, visit_months, visit_year_ids, visit_month_ids, res_countries, res_from_years, res_from_months, res_until_years, res_until_months):
    # Use the input_* values for the current state
    res_countries = input_countries
    res_from_years = input_from_years
    res_from_months = input_from_months
    res_until_years = input_until_years
    res_until_months = input_until_months
    import copy
    from dash import html, dcc
    import datetime
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    # --- Add column headers for residence table ---
    header = html.Div([
        html.Div('Country', style={'width': '280px', 'fontSize': 13, 'color': '#888', 'fontWeight': 500, 'textAlign': 'left', 'lineHeight': '20px', 'marginRight': '8px'}),
        html.Div('From', style={'width': '180px', 'fontSize': 13, 'color': '#888', 'fontWeight': 500, 'textAlign': 'center', 'lineHeight': '20px', 'marginRight': '16px', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
        html.Div('Until', style={'width': '180px', 'fontSize': 13, 'color': '#888', 'fontWeight': 500, 'textAlign': 'center', 'lineHeight': '20px', 'marginRight': '16px', 'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),
        html.Div('', style={'flex': 1}),
    ], style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'center', 'marginBottom': '2px', 'marginLeft': '2px'})
    
    def build_row(idx, country, from_year, from_month, until_year, until_month, options):
        allowed_country_options = options if options else []
        return html.Div([
            html.Div([
                dcc.Dropdown(
                    id={'type': 'res_country', 'index': idx},
                    options=[{'label': c, 'value': c} for c in allowed_country_options],
                    value=country,
                    placeholder='Where have you lived?',
                    style={'width': '280px', 'fontSize': 15}
                )
            ], style={'width': '280px', 'marginRight': '8px', 'display': 'flex', 'alignItems': 'center'}),
            html.Div([
                dcc.Dropdown(
                    id={'type': 'res_from_year', 'index': idx},
                    options=[{'label': str(y), 'value': y} for y in range(dob_year, current_year + 1)],
                    value=from_year,
                    style={'width': '100px', 'marginRight': '6px', 'fontSize': 15, 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    id={'type': 'res_from_month', 'index': idx},
                    options=[{'label': m, 'value': i+1} for i, m in enumerate(months_full)],
                    value=from_month,
                    style={'width': '80px', 'fontSize': 15, 'display': 'inline-block'}
                ),
            ], style={'width': '180px', 'display': 'flex', 'alignItems': 'center', 'marginRight': '16px'}),
            html.Div([
                dcc.Dropdown(
                    id={'type': 'res_until_year', 'index': idx},
                    options=[{'label': str(y), 'value': y} for y in range(dob_year, current_year + 1)],
                    value=until_year,
                    style={'width': '100px', 'marginRight': '6px', 'fontSize': 15, 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    id={'type': 'res_until_month', 'index': idx},
                    options=[{'label': m, 'value': i+1} for i, m in enumerate(months_full)],
                    value=until_month,
                    style={'width': '80px', 'fontSize': 15, 'display': 'inline-block'}
                ),
            ], style={'width': '180px', 'display': 'flex', 'alignItems': 'center', 'marginRight': '16px'}),
            html.Div([
                html.Button('Remove', id={'type': 'remove_residence_period', 'index': idx}, n_clicks=0, style={'backgroundColor': '#eee', 'color': '#222', 'border': 'none', 'padding': '4px 10px', 'borderRadius': '4px', 'fontSize': '13px', 'cursor': 'pointer', 'height': '38px', 'display': 'flex', 'alignItems': 'center'})
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], style={'marginBottom': '12px', 'display': 'flex', 'alignItems': 'center'})
    triggered = ctx.triggered_id
    options = visited_countries or []
    section_visible = res_section_style and res_section_style.get('display') == 'block'
    def ensure_list(val):
        if isinstance(val, list):
            return val
        elif val is None:
            return []
        else:
            return [val]
    res_countries = ensure_list(res_countries)
    res_from_years = ensure_list(res_from_years)
    res_from_months = ensure_list(res_from_months)
    res_until_years = ensure_list(res_until_years)
    res_until_months = ensure_list(res_until_months)
    # Remove row if remove button clicked
    if isinstance(triggered, dict) and triggered.get('type') == 'remove_residence_period':
        idx = triggered['index']
        res_countries = [c for i, c in enumerate(res_countries) if i != idx]
        res_from_years = [y for i, y in enumerate(res_from_years) if i != idx]
        res_from_months = [m for i, m in enumerate(res_from_months) if i != idx]
        res_until_years = [y for i, y in enumerate(res_until_years) if i != idx]
        res_until_months = [m for i, m in enumerate(res_until_months) if i != idx]
    # Always keep at least one row
    if not res_countries or len(res_countries) == 0:
        default_country = options[0] if options else None
        from_year = dob_year
        from_month = dob_month
        until_year = current_year
        until_month = current_month
        res_countries = [default_country]
        res_from_years = [from_year]
        res_from_months = [from_month]
        res_until_years = [until_year]
        res_until_months = [until_month]
    # Add new row if add button clicked
    if triggered == 'add_residence_period_btn' and section_visible:
        idx = len(res_countries)
        # Find the next available country (not already used), or allow repeats if all are used
        used_countries = set(res_countries)
        next_country = next((c for c in options if c not in used_countries), options[0] if options else None)
        # Use the last row's until as the new row's from
        last_until_year = res_until_years[-1] if res_until_years[-1] is not None else dob_year
        last_until_month = res_until_months[-1] if res_until_months[-1] is not None else dob_month
        from_year = last_until_year
        from_month = last_until_month
        until_year = current_year
        until_month = current_month
        # Append new row values
        res_countries = res_countries + [next_country]
        res_from_years = res_from_years + [from_year]
        res_from_months = res_from_months + [from_month]
        res_until_years = res_until_years + [until_year]
        res_until_months = res_until_months + [until_month]
    # --- AUTO-RESET/CLEAR FUTURE PERIODS (move before building rows) ---
    n = len(res_countries)
    last_valid = 1 if n > 0 else 0
    for i in range(1, n):
        # Only check if from is after until (invalid period)
        if (res_until_years[i] < res_from_years[i]) or (res_until_years[i] == res_from_years[i] and res_until_months[i] < res_from_months[i]):
            break
        # Check if country is set
        if not res_countries[i]:
            break
        last_valid = i + 1
    # Truncate all lists at the first invalid/non-sequential period
    res_countries = res_countries[:last_valid]
    res_from_years = res_from_years[:last_valid]
    res_from_months = res_from_months[:last_valid]
    res_until_years = res_until_years[:last_valid]
    res_until_months = res_until_months[:last_valid]
    # Build all rows
    preserved_rows = [build_row(i, res_countries[i], res_from_years[i], res_from_months[i], res_until_years[i], res_until_months[i], options) for i in range(len(res_countries))]
    return [header] + preserved_rows

@app.callback(
    Output("toggle_residence_btn", "style"),
    Input("residence_section", "style"),
    State("toggle_residence_btn", "style"),
    prevent_initial_call=False
)
def hide_toggle_residence_btn(res_section_style, btn_style):
    style = dict(btn_style) if btn_style else {}
    if res_section_style and res_section_style.get("display") == "block":
        style["display"] = "none"
    else:
        style["display"] = ""
    return style

# --- Residence period logic: restrict 'until' >= 'from' and prevent overlaps ---
@app.callback(
    Output({'type': 'res_until_year', 'index': MATCH}, 'options'),
    Output({'type': 'res_until_month', 'index': MATCH}, 'options'),
    Input({'type': 'res_from_year', 'index': MATCH}, 'value'),
    Input({'type': 'res_from_month', 'index': MATCH}, 'value'),
    Input({'type': 'res_country', 'index': MATCH}, 'value'),
    State({'type': 'res_until_year', 'index': MATCH}, 'value'),
    State({'type': 'res_until_month', 'index': MATCH}, 'value'),
    State({'type': 'res_country', 'index': ALL}, 'value'),
    State({'type': 'res_from_year', 'index': ALL}, 'value'),
    State({'type': 'res_from_month', 'index': ALL}, 'value'),
    State({'type': 'res_until_year', 'index': ALL}, 'value'),
    State({'type': 'res_until_month', 'index': ALL}, 'value'),
    State('dob_year', 'value'),
    State('dob_month', 'value'),
    prevent_initial_call=False
)
def restrict_until_options(from_year, from_month, country, until_year, until_month, all_countries, all_from_years, all_from_months, all_until_years, all_until_months, dob_year, dob_month):
    import datetime
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    if from_year is None:
        from_year = dob_year
    until_year_options = [y for y in range(from_year, current_year + 1)]
    if until_year is None:
        until_year = from_year
    if from_month is None:
        from_month = dob_month or 1
    if until_year == from_year:
        until_month_options = [(months_full[m-1], m) for m in range(from_month, current_month+1 if until_year==current_year else 13)]
    elif until_year == current_year:
        until_month_options = [(months_full[m-1], m) for m in range(1, current_month+1)]
    else:
        until_month_options = [(months_full[m-1], m) for m in range(1, 13)]
    this_idx = None
    for idx, (c, fy, fm, uy, um) in enumerate(zip(all_countries, all_from_years, all_from_months, all_until_years, all_until_months)):
        if c == country and fy == from_year and fm == from_month and uy == until_year and um == until_month:
            this_idx = idx
            break
    def age_tuple(y, m):
        return (y or dob_year, m or 1)
    this_from = age_tuple(from_year, from_month)
    # --- CHANGED: collect all other periods, not just same country ---
    other_periods = []
    for idx, (c, fy, fm, uy, um) in enumerate(zip(all_countries, all_from_years, all_from_months, all_until_years, all_until_months)):
        if idx == this_idx or fy is None or uy is None:
            continue
        other_periods.append((age_tuple(fy, fm), age_tuple(uy, um)))
    filtered_until_year_options = []
    filtered_until_month_options = []
    current_until_year = all_until_years[this_idx] if this_idx is not None else None
    current_until_month = all_until_months[this_idx] if this_idx is not None else None
    for y in until_year_options:
        for m in ([v for _, v in until_month_options] if y == until_year else range(1, 13)):
            this_until = (y, m)
            overlap = False
            for (o_from, o_until) in other_periods:
                if not (this_until <= o_from or this_from >= o_until):
                    overlap = True
                    break
            if not overlap or (y == current_until_year and m == current_until_month):
                if y not in filtered_until_year_options:
                    filtered_until_year_options.append(y)
                if y == until_year or y == current_until_year:
                    filtered_until_month_options.append((months_full[m-1], m))
    if not filtered_until_year_options:
        filtered_until_year_options = [from_year]
    if not filtered_until_month_options:
        filtered_until_month_options = [(months_full[from_month-1], from_month)]
    return (
        [{'label': str(y), 'value': y} for y in filtered_until_year_options],
        [{'label': label, 'value': value} for label, value in filtered_until_month_options]
    )

@app.callback(
    Output({'type': 'res_from_year', 'index': MATCH}, 'options'),
    Output({'type': 'res_from_month', 'index': MATCH}, 'options'),
    Input({'type': 'res_country', 'index': MATCH}, 'value'),
    Input({'type': 'res_until_year', 'index': MATCH}, 'value'),
    Input({'type': 'res_until_month', 'index': MATCH}, 'value'),
    State({'type': 'res_country', 'index': ALL}, 'value'),
    State({'type': 'res_from_year', 'index': ALL}, 'value'),
    State({'type': 'res_from_month', 'index': ALL}, 'value'),
    State({'type': 'res_until_year', 'index': ALL}, 'value'),
    State({'type': 'res_until_month', 'index': ALL}, 'value'),
    State('dob_year', 'value'),
    State('dob_month', 'value'),
    prevent_initial_call=False
)
def restrict_from_options(country, until_year, until_month, all_countries, all_from_years, all_from_months, all_until_years, all_until_months, dob_year, dob_month):
    import datetime
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month
    # 1. Restrict from_year to <= until_year
    if until_year is None:
        until_year = current_year
    from_year_options = [y for y in range(dob_year, until_year + 1)]
    # 2. Restrict from_month to <= until_month if same year, else all months
    if until_month is None:
        until_month = current_month if until_year == current_year else 12
    if dob_month is None:
        dob_month = 1
    if until_year == dob_year:
        from_month_options = [(months_full[m-1], m) for m in range(dob_month, until_month+1)]
    elif until_year == current_year:
        from_month_options = [(months_full[m-1], m) for m in range(1, until_month+1)]
    else:
        from_month_options = [(months_full[m-1], m) for m in range(1, 13)]
    # --- CHANGED: collect all other periods, not just same country ---
    this_idx = None
    for idx, (c, fy, fm, uy, um) in enumerate(zip(all_countries, all_from_years, all_from_months, all_until_years, all_until_months)):
        if c == country and uy == until_year and um == until_month and fy == all_from_years[idx] and fm == all_from_months[idx]:
            this_idx = idx
            break
    def age_tuple(y, m):
        return (y or dob_year, m or 1)
    this_until = age_tuple(until_year, until_month)
    other_periods = []
    for idx, (c, fy, fm, uy, um) in enumerate(zip(all_countries, all_from_years, all_from_months, all_until_years, all_until_months)):
        if idx == this_idx or fy is None or uy is None:
            continue
        other_periods.append((age_tuple(fy, fm), age_tuple(uy, um)))
    filtered_from_year_options = []
    filtered_from_month_options = []
    # Always include the currently selected value
    current_from_year = all_from_years[this_idx] if this_idx is not None else None
    current_from_month = all_from_months[this_idx] if this_idx is not None else None
    for y in from_year_options:
        for m in ([v for _, v in from_month_options] if y == dob_year else range(1, 13)):
            this_from = (y, m)
            overlap = False
            for (o_from, o_until) in other_periods:
                if not (this_until <= o_from or this_from >= o_until):
                    overlap = True
                    break
            if not overlap or (y == current_from_year and m == current_from_month):
                if y not in filtered_from_year_options:
                    filtered_from_year_options.append(y)
                if y == dob_year or y == current_from_year:
                    filtered_from_month_options.append((months_full[m-1], m))
    if not filtered_from_year_options:
        filtered_from_year_options = [dob_year]
    if not filtered_from_month_options:
        filtered_from_month_options = [(months_full[dob_month-1], dob_month)]
    return (
        [{'label': str(y), 'value': y} for y in filtered_from_year_options],
        [{'label': label, 'value': value} for label, value in filtered_from_month_options]
    )

# Add auto-correction for from/until residence period selection
@app.callback(
    Output({'type': 'res_from_year', 'index': MATCH}, 'value'),
    Output({'type': 'res_from_month', 'index': MATCH}, 'value'),
    Output({'type': 'res_until_year', 'index': MATCH}, 'value'),
    Output({'type': 'res_until_month', 'index': MATCH}, 'value'),
    Input({'type': 'res_from_year', 'index': MATCH}, 'value'),
    Input({'type': 'res_from_month', 'index': MATCH}, 'value'),
    Input({'type': 'res_until_year', 'index': MATCH}, 'value'),
    Input({'type': 'res_until_month', 'index': MATCH}, 'value'),
    State('dob_year', 'value'),
    State('dob_month', 'value'),
    prevent_initial_call=False
)
def autocorrect_from_until(from_year, from_month, until_year, until_month, dob_year, dob_month):
    # If until is before from, set from = until
    # If from is after until, set until = from
    if from_year is None or from_month is None:
        return from_year, from_month, until_year, until_month
    if until_year is None or until_month is None:
        return from_year, from_month, until_year, until_month
    from_tuple = (from_year, from_month)
    until_tuple = (until_year, until_month)
    if until_tuple < from_tuple:
        return until_year, until_month, until_year, until_month
    if from_tuple > until_tuple:
        return from_year, from_month, from_year, from_month
    return from_year, from_month, until_year, until_month

# Add a callback to show/hide the label based on country selection
@app.callback(
    Output("visit_countries_label", "style"),
    Input("country_select", "value"),
)
def show_visit_label(selected_countries):
    if selected_countries and len(selected_countries) > 0:
        return {"fontSize": 14, "marginBottom": "18px", "display": "block"}
    else:
        return {"fontSize": 14, "marginBottom": "18px", "display": "none"}

if __name__ == "__main__":
    app.run(debug=True) 