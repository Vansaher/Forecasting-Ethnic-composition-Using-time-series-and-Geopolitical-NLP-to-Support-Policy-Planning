
# app.py -- Ethnic Demography Dashboard (MASTER + OD FILES)
# Expected MASTER columns:
# iso3,year,ethnic_group,share,count,total_pop,model_name,view_type,scenario_name,
# delta_migrants,delta_in,delta_out,delta_count,total_pop_shock
#
# Expected OD MIGRATION columns (od_migration_master.csv):
# iso3_dest, iso3_orig, year, view_type, scenario_name, model_name,
# migrant_stock, migrant_stock_pred, migrant_stock_shock,
# delta_in_od, delta_out_od, delta_stock_od
#
# Expected OD ETHNIC IMPACT columns (od_ethnic_impact_2025.csv):
# iso3_dest, year, scenario_name, dest_ethnic_bucket, origin_ethnic_group, delta_migrants_ethnic

import pandas as pd
import numpy as np

from dash import Dash, dcc, html, Input, Output, callback_context
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go


# =========================
# CONFIG
# =========================
BEST_MODEL = "XGB_BASE"
FOCUS_COUNTRIES = ["USA", "MYS", "IDN"]

MASTER_FILE = "Imports/ethnic_demography_master.csv"
OD_MIGRATION_FILE = "Imports/od_migration_master.csv"
OD_ETHNIC_IMPACT_FILE = "Imports/od_ethnic_impact_2025.csv"

# Plotly theme (light, soft) with a higher-contrast override for key charts
THEME_TEMPLATE = dict(
    layout=dict(
        font=dict(family="Trebuchet MS, Segoe UI, Arial, sans-serif", color="#1f2a33"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f5f7fb",
        colorway=["#66e9e6", "#15c8c5", "#4896fe", "#887bfd", "#5347cd"],
        xaxis=dict(gridcolor="#e3e9f5", zerolinecolor="#e3e9f5", automargin=True),
        yaxis=dict(gridcolor="#e3e9f5", zerolinecolor="#e3e9f5", automargin=True),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor="rgba(255,255,255,0.7)", bordercolor="#e3e9f5", borderwidth=1),
    )
)
pio.templates["soft_teal"] = THEME_TEMPLATE
px.defaults.template = "soft_teal"

# Soft teal categorical palette (kept consistent across charts)
THEME_CATEGORICAL = [
    "#66e9e6", "#15c8c5", "#4896fe", "#887bfd", "#5347cd",
    "#7af0ee", "#35d6d3", "#6aa9ff", "#a094ff", "#6b5ee0",
]


# =========================
# LOAD MASTER
# =========================
m = pd.read_csv(MASTER_FILE)

REQUIRED = [
    "iso3", "year", "ethnic_group", "share", "count", "total_pop",
    "model_name", "view_type", "scenario_name",
    "delta_migrants", "delta_in", "delta_out", "delta_count", "total_pop_shock"
]
missing = [c for c in REQUIRED if c not in m.columns]
if missing:
    raise RuntimeError(f"MASTER CSV missing columns: {missing}")

m["iso3"] = m["iso3"].astype(str).str.strip().str.upper()
m["year"] = pd.to_numeric(m["year"], errors="coerce").astype(int)
m["ethnic_group"] = m["ethnic_group"].astype(str)
m["model_name"] = m["model_name"].astype(str)
m["view_type"] = m["view_type"].astype(str).str.strip().str.upper()
m["scenario_name"] = m["scenario_name"].fillna("").astype(str)

num_cols = ["share", "count", "total_pop", "delta_migrants", "delta_in", "delta_out", "delta_count", "total_pop_shock"]
for c in num_cols:
    m[c] = pd.to_numeric(m[c], errors="coerce")

if any(c in set(m["iso3"]) for c in FOCUS_COUNTRIES):
    m = m[m["iso3"].isin(FOCUS_COUNTRIES)].copy()

AVAILABLE_COUNTRIES = sorted(m["iso3"].unique().tolist())
ALL_GROUPS = sorted(m["ethnic_group"].unique().tolist())
AVAILABLE_YEARS = sorted(m["year"].unique().tolist())
YEAR_MIN = int(min(AVAILABLE_YEARS)) if AVAILABLE_YEARS else 0
YEAR_MAX = int(max(AVAILABLE_YEARS)) if AVAILABLE_YEARS else 0

SCENARIO_LIST = sorted(
    [s for s in m.loc[m["view_type"] == "SCENARIO", "scenario_name"].unique().tolist() if s.strip() != ""]
)

# =========================
# LOAD OD MIGRATION + ETHNIC IMPACT
# =========================
odm = pd.read_csv(OD_MIGRATION_FILE)
need_odm = [
    "iso3_dest", "iso3_orig", "year", "view_type", "scenario_name", "model_name",
    "migrant_stock", "migrant_stock_pred", "migrant_stock_shock",
    "delta_in_od", "delta_out_od", "delta_stock_od"
]
miss_odm = [c for c in need_odm if c not in odm.columns]
if miss_odm:
    raise RuntimeError(f"od_migration_master.csv missing columns: {miss_odm}")

odm["iso3_dest"] = odm["iso3_dest"].astype(str).str.strip().str.upper()
odm["iso3_orig"] = odm["iso3_orig"].astype(str).str.strip().str.upper()
odm["year"] = pd.to_numeric(odm["year"], errors="coerce").astype(int)
odm["view_type"] = odm["view_type"].astype(str).str.strip().str.upper()
odm["scenario_name"] = odm["scenario_name"].fillna("").astype(str)
odm["model_name"] = odm["model_name"].astype(str)
for c in ["migrant_stock", "migrant_stock_pred", "migrant_stock_shock", "delta_in_od", "delta_out_od", "delta_stock_od"]:
    odm[c] = pd.to_numeric(odm[c], errors="coerce")

ode = pd.read_csv(OD_ETHNIC_IMPACT_FILE)
need_ode = ["iso3_dest", "year", "scenario_name", "dest_ethnic_bucket", "origin_ethnic_group", "delta_migrants_ethnic"]
miss_ode = [c for c in need_ode if c not in ode.columns]
if miss_ode:
    raise RuntimeError(f"od_ethnic_impact_2025.csv missing columns: {miss_ode}")

ode["iso3_dest"] = ode["iso3_dest"].astype(str).str.strip().str.upper()
ode["year"] = pd.to_numeric(ode["year"], errors="coerce").astype(int)
ode["scenario_name"] = ode["scenario_name"].fillna("").astype(str)
ode["dest_ethnic_bucket"] = ode["dest_ethnic_bucket"].astype(str)
ode["origin_ethnic_group"] = ode["origin_ethnic_group"].fillna("").astype(str)
ode["delta_migrants_ethnic"] = pd.to_numeric(ode["delta_migrants_ethnic"], errors="coerce")


# =========================
# HELPERS
# =========================
def baseline_hist_forecast(df: pd.DataFrame, iso3: str) -> pd.DataFrame:
    """
    Baseline dataset for main plots:
    - HIST rows
    - FORECAST rows for BEST_MODEL (fallback to any model if BEST_MODEL missing)
    """
    sub = df[df["iso3"] == iso3].copy()

    hist = sub[sub["view_type"] == "HIST"].copy()
    hist["type_plot"] = "historical"

    fore_all = sub[sub["view_type"] == "FORECAST"].copy()
    if (not fore_all.empty) and (BEST_MODEL in set(fore_all["model_name"])):
        fore = fore_all[fore_all["model_name"] == BEST_MODEL].copy()
    else:
        fore = fore_all.copy()
    fore["type_plot"] = "forecast"

    return pd.concat([hist, fore], ignore_index=True)


def scenario_2025(df: pd.DataFrame, iso3: str, scenario_name: str) -> pd.DataFrame:
    if scenario_name == "Baseline":
        return df.iloc[0:0].copy()

    return df[
        (df["iso3"] == iso3) &
        (df["view_type"] == "SCENARIO") &
        (df["scenario_name"] == scenario_name) &
        (df["year"] == 2025)
    ].copy()


def pick_top_groups_by_share(df: pd.DataFrame, top_k: int = 6) -> list[str]:
    if df.empty:
        return []
    y = int(df["year"].max())
    snap = df[df["year"] == y].copy()
    snap = snap.dropna(subset=["share"])
    if snap.empty:
        return []
    snap = snap.sort_values("share", ascending=False)
    return snap["ethnic_group"].head(top_k).tolist()


def groups_for_country(df: pd.DataFrame, iso3: str) -> list[str]:
    if not iso3:
        return ALL_GROUPS
    return sorted(df.loc[df["iso3"] == iso3, "ethnic_group"].unique().tolist())


def make_group_color_map(groups: list[str]) -> dict[str, str]:
    return {g: THEME_CATEGORICAL[i % len(THEME_CATEGORICAL)] for i, g in enumerate(groups)}


def lighten_hex(hex_color: str, factor: float) -> str:
    """
    Lighten a hex color by mixing with white. factor in [0,1].
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


def round_away_from_zero(values: pd.Series | np.ndarray) -> np.ndarray:
    vals = np.asarray(values, dtype=float)
    rounded = np.where(vals >= 0, np.ceil(vals), np.floor(vals))
    if np.isscalar(values) or vals.shape == ():
        return float(rounded)
    return rounded


def snap_year_to_available(year: int) -> int:
    if not AVAILABLE_YEARS:
        return year
    return min(AVAILABLE_YEARS, key=lambda y: abs(y - year))


def scenario_name_from_controls(aid_level: str, conflict_internal_level: str, conflict_external_level: str) -> str:
    aid_level = (aid_level or "OFF").upper()
    conflict_internal_level = (conflict_internal_level or "OFF").upper()
    conflict_external_level = (conflict_external_level or "OFF").upper()

    parts = []
    if aid_level != "OFF":
        parts.append(f"Aid_{aid_level}")
    if conflict_internal_level != "OFF":
        parts.append(f"Conflict_internal_{conflict_internal_level}")
    if conflict_external_level != "OFF":
        parts.append(f"Conflict_external_{conflict_external_level}")

    if not parts:
        return "Baseline"
    return "__".join(parts)


def build_treemap_df(iso3: str, year: int, scenario_name: str) -> pd.DataFrame:
    """
    Treemap rows from od_ethnic_impact_2025:
      parent = dest_ethnic_bucket
      child  = origin_ethnic_group
      value  = delta_migrants_ethnic
    """
    if scenario_name == "Baseline":
        return pd.DataFrame(columns=["id", "parent", "label", "value", "color_hex"])

    sub = ode[
        (ode["iso3_dest"] == iso3) &
        (ode["year"] == year) &
        (ode["scenario_name"] == scenario_name)
    ].copy()
    if sub.empty:
        return pd.DataFrame(columns=["id", "parent", "label", "value", "color_hex"])

    sub = sub.dropna(subset=["delta_migrants_ethnic"])
    sub = sub.rename(columns={"delta_migrants_ethnic": "value"})

    # Normalize unknown-like labels into "Other"
    oeg = sub["origin_ethnic_group"].astype(str).str.strip()
    unknown_mask = oeg.str.lower().isin([
        "unknown", "unknown origin", "unknown_origin",
        "n/a", "na", "unspecified", "not specified", "other/unknown"
    ])
    sub.loc[unknown_mask, "origin_ethnic_group"] = "Other"

    sub = sub.groupby(["dest_ethnic_bucket", "origin_ethnic_group"], as_index=False)["value"].sum()

    rows = []
    for bucket, bdf in sub.groupby("dest_ethnic_bucket"):
        base_color = BUCKET_COLOR_MAP.get(bucket, THEME_CATEGORICAL[0])
        bdf = bdf.sort_values("value", ascending=False).reset_index(drop=True)

        rows.append({
            "id": f"{bucket}",
            "parent": "",
            "label": bucket,
            "value": float(bdf["value"].sum()),
            "color_hex": base_color,
        })

        n = max(len(bdf), 1)
        for i, r in bdf.iterrows():
            lighten = 0.15 + (0.55 * (i / max(n - 1, 1)))
            rows.append({
                "id": f"{bucket}|{r['origin_ethnic_group']}",
                "parent": f"{bucket}",
                "label": r["origin_ethnic_group"],
                "value": float(r["value"]),
                "color_hex": lighten_hex(base_color, lighten),
            })

    return pd.DataFrame(rows)


def build_origin_map_df(iso3: str, year: int, scenario_name: str) -> pd.DataFrame:
    """
    Origin map rows from od_migration_master:
      location = iso3_orig
      value    = migrant_stock_pred (baseline) or delta_stock_od (scenario)
    """
    sub = odm[(odm["iso3_dest"] == iso3) & (odm["year"] == year)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["iso3_orig", "value"])

    if scenario_name == "Baseline":
        fore = sub[sub["view_type"] == "FORECAST"].copy()
        use = fore if not fore.empty else sub[sub["view_type"] == "HIST"].copy()
        if use.empty:
            return pd.DataFrame(columns=["iso3_orig", "value"])
        use["value"] = np.where(use["view_type"] == "FORECAST", use["migrant_stock_pred"], use["migrant_stock"])
        use = use.dropna(subset=["value"])
        return use[["iso3_orig", "value"]]

    scen = sub[(sub["view_type"] == "SCENARIO") & (sub["scenario_name"] == scenario_name)].copy()
    if scen.empty:
        return pd.DataFrame(columns=["iso3_orig", "value"])
    scen = scen.dropna(subset=["delta_stock_od"])
    scen = scen.rename(columns={"delta_stock_od": "value"})
    return scen[["iso3_orig", "value"]]


# Consistent category colors across charts
GROUP_COLOR_MAP = make_group_color_map(ALL_GROUPS)
DEST_BUCKETS = sorted(ode["dest_ethnic_bucket"].dropna().unique().tolist())
BUCKET_COLOR_MAP = {}
missing_idx = 0
for b in DEST_BUCKETS:
    if b in GROUP_COLOR_MAP:
        BUCKET_COLOR_MAP[b] = GROUP_COLOR_MAP[b]
    else:
        BUCKET_COLOR_MAP[b] = THEME_CATEGORICAL[missing_idx % len(THEME_CATEGORICAL)]
        missing_idx += 1


# =========================
# APP
# =========================
app = Dash(__name__)
server = app.server


def kpi_children(title: str, value: str, subtitle: str | None = None):
    children = [html.Div(title, className="kpi-title"), html.Div(value, className="kpi-value")]
    if subtitle:
        children.append(html.Div(subtitle, className="kpi-subtitle"))
    return children


def kpi_card(title: str, value: str, subtitle: str | None = None, card_id: str | None = None):
    props = {"className": "kpi-card"}
    if card_id is not None:
        props["id"] = card_id
    return html.Div(kpi_children(title, value, subtitle), **props)


app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="header",
            children=[
                html.H2("Ethnic Composition Forecast Dashboard"),
                html.Div(
                    className="subheader",
                    children=[
                        html.Div("Scenario deltas shown for 2025 (Scenario - Baseline)."),
                    ],
                ),
            ],
        ),

        dcc.Store(id="scenario-store", data="Baseline"),
        dcc.Store(id="insights-open", data=False),

        html.Div(
            className="layout",
            style={"display": "flex", "gap": "16px", "alignItems": "flex-start"},
            children=[
                # ---------- Sidebar ----------
                html.Div(
                    className="sidebar",
                    style={
                        "minWidth": "240px",
                        "maxWidth": "280px",
                        "position": "sticky",
                        "top": "12px",
                        "alignSelf": "flex-start",
                    },
                    children=[
                        html.Div(
                            className="control-card",
                            children=[
                                html.Label("Country"),
                                dcc.Dropdown(
                                    id="country-dd",
                                    options=[{"label": c, "value": c} for c in AVAILABLE_COUNTRIES],
                                    value=AVAILABLE_COUNTRIES[0] if AVAILABLE_COUNTRIES else None,
                                    clearable=False,
                                ),
                            ],
                        ),
                        html.Div(
                            className="control-card dropdown-card",
                            children=[
                                html.Label("Ethnic groups (optional filter)"),
                                dcc.Dropdown(
                                    id="groups-dd",
                                    options=[{"label": g, "value": g} for g in ALL_GROUPS],
                                    value=[],
                                    multi=True,
                                    placeholder="All groups",
                                ),
                            ],
                        ),
                        html.H4("Scenario Picker (2025)"),
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                            children=[
                                html.Div("Baseline"),
                                html.Button("Reset", id="scenario-reset", n_clicks=0),
                            ],
                        ),
                        html.Hr(),
                        html.Label("Aid response"),
                        dcc.RadioItems(
                            id="aid-level",
                            options=[{"label": "Off", "value": "OFF"}, {"label": "Low", "value": "LOW"}, {"label": "High", "value": "HIGH"}],
                            value="OFF",
                            labelStyle={"display": "inline-block", "marginRight": "10px"},
                        ),
                        html.Br(),
                        html.Label("Conflict internal"),
                        dcc.RadioItems(
                            id="conflict-internal-level",
                            options=[{"label": "Off", "value": "OFF"}, {"label": "Low", "value": "LOW"}, {"label": "High", "value": "HIGH"}],
                            value="OFF",
                            labelStyle={"display": "inline-block", "marginRight": "10px"},
                        ),
                        html.Br(),
                        html.Label("Conflict external"),
                        dcc.RadioItems(
                            id="conflict-external-level",
                            options=[{"label": "Off", "value": "OFF"}, {"label": "Low", "value": "LOW"}, {"label": "High", "value": "HIGH"}],
                            value="OFF",
                            labelStyle={"display": "inline-block", "marginRight": "10px"},
                        ),
                        html.Br(),
                        html.Hr(),
                        html.Div(
                            children=[
                                html.Div("Scenario KPI (2025)", style={"fontWeight": "bold"}),
                                html.Div(id="scenario-kpi-row", style={"marginTop": "6px"}),
                            ],
                        ),
                        html.Div(
                            className="card no-blob",
                            children=[
                                html.Div(
                                    style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                    children=[
                                        html.H4("Policy Statistical Insights"),
                                        html.Button("↗", id="insights-open-btn", className="insight-pop"),
                                    ],
                                ),
                                html.Div(id="policy-insights", className="insight-box"),
                            ],
                        ),
                    ],
                ),

                # ---------- Main content ----------
                html.Div(
                    className="content",
                    style={"flex": "1 1 auto"},
                    children=[
                        html.Div(
                            className="controls",
                            children=[
                                html.Div(
                                    className="control-card",
                                    children=[
                                        html.Label("Year range"),
                                        dcc.RangeSlider(
                                            id="year-slider",
                                            min=YEAR_MIN,
                                            max=YEAR_MAX,
                                            step=None,
                                            value=[YEAR_MIN, YEAR_MAX],
                                            marks={y: str(y) for y in AVAILABLE_YEARS},
                                        ),
                                    ],
                                ),
                            ],
                        ),

                        html.Div(
                            className="kpi-row",
                            children=[
                                kpi_card("Planning horizon", f"{YEAR_MIN}-{YEAR_MAX}", card_id="planning-horizon-card"),
                                kpi_card("Origin countries", str(len(AVAILABLE_COUNTRIES)), card_id="origin-countries-card"),
                                kpi_card("Origin ethnic groups", str(len(ALL_GROUPS)), card_id="origin-ethnic-card"),
                            ],
                        ),

                        html.Div(
                            className="grid",
                            children=[
                                html.Div(
                                    className="card card-map",
                                    children=[
                                        html.H4("Origin map -- migrant origins"),
                                        dcc.Graph(id="origin-map"),
                                    ],
                                ),
                            ],
                        ),

                        html.Div(
                            className="grid",
                            children=[
                                html.Div(
                                    className="card",
                                    children=[
                                        html.H4("Total population (baseline vs scenario shock)"),
                                        html.Div(
                                            style={"display": "flex", "gap": "12px", "alignItems": "center"},
                                            children=[
                                                html.Div(style={"flex": "1 1 auto"}, children=[dcc.Graph(id="pop-line")]),
                                                html.Div(
                                                    style={"minWidth": "140px", "textAlign": "center", "borderLeft": "1px solid #e2e2e2", "paddingLeft": "12px"},
                                                    children=[
                                                        html.Div("Delta (2025)", style={"fontWeight": "bold"}),
                                                        html.Div(id="pop-delta", style={"marginTop": "4px", "fontSize": "18px"}),
                                                    ],
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                html.Div(className="card", children=[html.H4("Ethnic composition (stacked)"), dcc.Graph(id="share-line")]),
                            ],
                        ),

                        html.Div(
                            className="grid",
                            children=[
                                html.Div(className="card", children=[html.H4("Projected counts (latest forecast year)"), dcc.Graph(id="count-bar")]),
                            ],
                        ),

                        html.Div(
                            className="grid",
                            children=[
                                html.Div(
                                    className="card",
                                    children=[
                                        html.H4("Scenario impact (2025) -- delta count by ethnic group"),
                                        dcc.Graph(id="scenario-delta-bar"),
                                    ],
                                ),
                            ],
                        ),

                        html.Div(
                            className="grid",
                            children=[
                                html.Div(
                                    className="card",
                                    children=[
                                        html.H4("Treemap -- scenario ethnic impact"),
                                        html.Div(
                                            style={"display": "flex", "gap": "12px", "alignItems": "center"},
                                            children=[
                                                html.Div(
                                                    style={"minWidth": "220px"},
                                                    children=[
                                                        html.Label("Treemap year (scenario impact)"),
                                                        dcc.Dropdown(id="treemap-year", options=[], value=None, clearable=False),
                                                        html.Div(
                                                            "Note: uses od_ethnic_impact_2025.csv (scenario impact).",
                                                            style={"fontSize": "12px", "opacity": 0.8, "marginTop": "6px"},
                                                        ),
                                                    ],
                                                ),
                                                html.Div(style={"flex": "1 1 auto"}, children=[dcc.Graph(id="treemap")]),
                                            ],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(
            id="insights-modal",
            className="insight-modal",
            children=[
                html.Div(
                    className="insight-modal-content",
                    children=[
                        html.Div(
                            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                            children=[
                                html.H4("Policy-relevant statistical insights"),
                                html.Button("✕", id="insights-close-btn", className="insight-close"),
                            ],
                        ),
                        html.Div(id="policy-insights-full"),
                    ],
                ),
            ],
        ),
    ],
)


# =========================
# CALLBACKS
# =========================
@app.callback(
    Output("groups-dd", "options"),
    Output("groups-dd", "value"),
    Input("country-dd", "value"),
    Input("groups-dd", "value"),
)
def sync_groups_options(country, selected_groups):
    groups = groups_for_country(m, country)
    options = [{"label": g, "value": g} for g in groups]
    if not selected_groups:
        return options, []
    filtered = [g for g in selected_groups if g in groups]
    return options, filtered


@app.callback(
    Output("scenario-store", "data"),
    Output("aid-level", "value"),
    Output("conflict-internal-level", "value"),
    Output("conflict-external-level", "value"),
    Input("aid-level", "value"),
    Input("conflict-internal-level", "value"),
    Input("conflict-external-level", "value"),
    Input("scenario-reset", "n_clicks"),
)
def update_scenario_store(aid_level, conflict_internal_level, conflict_external_level, reset_clicks):
    triggered = ""
    if callback_context.triggered:
        triggered = callback_context.triggered[0]["prop_id"]

    if "scenario-reset" in triggered:
        scenario_name = "Baseline"
        return scenario_name, "OFF", "OFF", "OFF"

    scenario_name = scenario_name_from_controls(aid_level, conflict_internal_level, conflict_external_level)
    return scenario_name, aid_level or "OFF", conflict_internal_level or "OFF", conflict_external_level or "OFF"


@app.callback(
    Output("treemap-year", "options"),
    Output("treemap-year", "value"),
    Input("country-dd", "value"),
)
def update_treemap_years(country):
    if not country:
        return [], None

    years = sorted(ode.loc[ode["iso3_dest"] == country, "year"].unique().tolist())
    if not years:
        years = sorted(odm.loc[odm["iso3_dest"] == country, "year"].unique().tolist())
    opts = [{"label": str(y), "value": int(y)} for y in years]
    default = int(years[-1]) if years else None
    return opts, default


@app.callback(
    Output("insights-open", "data"),
    Input("insights-open-btn", "n_clicks"),
    Input("insights-close-btn", "n_clicks"),
)
def toggle_insights_modal(open_clicks, close_clicks):
    triggered = ""
    if callback_context.triggered:
        triggered = callback_context.triggered[0]["prop_id"]
    if "insights-open-btn" in triggered:
        return True
    if "insights-close-btn" in triggered:
        return False
    return False


@app.callback(
    Output("share-line", "figure"),
    Output("count-bar", "figure"),
    Output("scenario-delta-bar", "figure"),
    Output("scenario-kpi-row", "children"),
    Output("planning-horizon-card", "children"),
    Output("origin-countries-card", "children"),
    Output("origin-ethnic-card", "children"),
    Output("pop-line", "figure"),
    Output("pop-delta", "children"),
    Output("origin-map", "figure"),
    Output("treemap", "figure"),
    Output("policy-insights", "children"),
    Output("policy-insights-full", "children"),
    Output("insights-modal", "style"),
    Input("country-dd", "value"),
    Input("scenario-store", "data"),
    Input("groups-dd", "value"),
    Input("year-slider", "value"),
    Input("treemap-year", "value"),
    Input("insights-open", "data"),
)
def update(country, scenario_name, groups, year_range, treemap_year, insights_open):
    if not country:
        empty = px.line(title="No data.")
        horizon_children = kpi_children("Planning horizon", f"{YEAR_MIN}-{YEAR_MAX}")
        origin_countries_children = kpi_children("Origin countries", "0")
        origin_ethnic_children = kpi_children("Origin ethnic groups", "0")
        return (
            empty, empty, empty, "", horizon_children, origin_countries_children, origin_ethnic_children,
            empty, "N/A", empty, empty, "", "", {"display": "none"}
        )

    y_min = snap_year_to_available(int(year_range[0]))
    y_max = snap_year_to_available(int(year_range[1]))
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    horizon_children = kpi_children("Planning horizon", f"{y_min}-{y_max}")
    origin_countries = (
        odm.loc[odm["iso3_dest"] == country, "iso3_orig"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    origin_countries = origin_countries[origin_countries != ""]
    origin_countries_children = kpi_children("Origin countries", str(origin_countries.nunique()))

    origin_ethnic = (
        ode.loc[ode["iso3_dest"] == country, "origin_ethnic_group"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    origin_ethnic = origin_ethnic[origin_ethnic != ""]
    origin_ethnic_children = kpi_children("Origin ethnic groups", str(origin_ethnic.nunique()))

    base = baseline_hist_forecast(m, country)
    base = base[base["year"].between(y_min, y_max)].copy()
    if groups:
        base = base[base["ethnic_group"].isin(groups)].copy()

    # -------- (A) Share stacked composition --------
    comp = base.copy()
    if comp.empty:
        fig_share = px.area(title="No rows for selected filters.")
    else:
        top_groups = pick_top_groups_by_share(comp, top_k=6)
        comp2 = comp.copy()
        comp2["eth_stack"] = np.where(comp2["ethnic_group"].isin(top_groups), comp2["ethnic_group"], "Other")
        agg = comp2.groupby(["year", "eth_stack"], as_index=False)["share"].sum()

        fig_share = px.area(
            agg.sort_values("year"),
            x="year",
            y="share",
            color="eth_stack",
            color_discrete_map=GROUP_COLOR_MAP,
            title=f"{country} -- Ethnic composition (stacked)",
        )
        fig_share.update_yaxes(tickformat=".0%")
        fig_share.update_xaxes(automargin=True)
        fig_share.update_yaxes(automargin=True)
        fig_share.update_traces(hovertemplate="%{x}: %{y:.1%}<extra></extra>")

    # -------- (B) Count bar (latest forecast year) --------
    fut = base[base["type_plot"] == "forecast"].copy()
    if fut.empty or fut["count"].isna().all():
        fig_count = px.bar(title="Projected counts unavailable.")
    else:
        latest_year = int(fut["year"].max())
        snap = fut[fut["year"] == latest_year].copy().sort_values("count", ascending=False)
        fig_count = px.bar(
            snap,
            x="ethnic_group",
            y="count",
            color="ethnic_group",
            color_discrete_map=GROUP_COLOR_MAP,
            title=f"{country} -- Projected counts (year {latest_year})",
        )
        fig_count.update_layout(showlegend=False)
        fig_count.update_yaxes(tickformat=",.0f")
        fig_count.update_xaxes(automargin=True)
        fig_count.update_yaxes(automargin=True)
        fig_count.update_traces(hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")

    # -------- (C) Scenario delta bar (2025 only) --------
    scen = scenario_2025(m, country, scenario_name)
    if groups and not scen.empty:
        scen = scen[scen["ethnic_group"].isin(groups)].copy()

    if scenario_name == "Baseline":
        fig_delta = px.bar(title="Baseline selected -- no scenario deltas.")
        kpis = [kpi_card("Delta migrants (net)", "0"), kpi_card("Delta IN", "0"), kpi_card("Delta OUT", "0")]
    elif scen.empty:
        fig_delta = px.bar(title="No scenario rows found for this country/scenario (year 2025).")
        kpis = [kpi_card("Delta migrants (net)", "N/A"), kpi_card("Delta IN", "N/A"), kpi_card("Delta OUT", "N/A")]
    else:
        scen["delta_count"] = scen["delta_count"].fillna(0.0)
        scen["delta_count_round"] = round_away_from_zero(scen["delta_count"])
        scen["abs_dc"] = scen["delta_count"].abs()
        top = scen.sort_values("abs_dc", ascending=False).head(12).copy().sort_values("delta_count_round")

        fig_delta = px.bar(
            top,
            x="delta_count_round",
            y="ethnic_group",
            color="ethnic_group",
            color_discrete_map=GROUP_COLOR_MAP,
            orientation="h",
            title=f"{country} -- Delta count in 2025 | {scenario_name}",
        )
        fig_delta.update_layout(showlegend=False)
        fig_delta.update_xaxes(tickformat=",.0f")
        fig_delta.update_xaxes(automargin=True)
        fig_delta.update_yaxes(automargin=True)
        fig_delta.update_traces(hovertemplate="%{y}<br>%{x:+,.0f}<extra></extra>")

        dm = float(scen["delta_migrants"].dropna().mean()) if scen["delta_migrants"].notna().any() else 0.0
        din = float(scen["delta_in"].dropna().mean()) if scen["delta_in"].notna().any() else 0.0
        dout = float(scen["delta_out"].dropna().mean()) if scen["delta_out"].notna().any() else 0.0
        kpis = [kpi_card("Delta migrants (net)", f"{dm:,.0f}"), kpi_card("Delta IN", f"{din:,.0f}"), kpi_card("Delta OUT", f"{dout:,.0f}")]

    kpi_row = html.Div(className="kpi-row", children=kpis)

    # -------- (D) Total population baseline vs scenario shock --------
    pop_base = baseline_hist_forecast(m, country)[["year", "total_pop"]].drop_duplicates().sort_values("year").copy()
    pop_base = pop_base.dropna(subset=["total_pop"])

    if pop_base.empty:
        fig_pop = px.line(title="total_pop not available in master.")
        pop_delta_text = "N/A"
    else:
        pop_df = pop_base.rename(columns={"total_pop": "Baseline"}).copy()
        if scenario_name != "Baseline" and (not scen.empty) and scen["total_pop_shock"].notna().any():
            shock_2025 = float(scen["total_pop_shock"].dropna().iloc[0])
            pop_df["Scenario"] = pop_df["Baseline"]

            if (pop_df["year"] == 2025).any():
                base_2025 = float(pop_df.loc[pop_df["year"] == 2025, "Baseline"].iloc[0])
                delta_2025 = shock_2025 - base_2025
                pop_df.loc[pop_df["year"] >= 2025, "Scenario"] = pop_df.loc[pop_df["year"] >= 2025, "Baseline"] + delta_2025
                pop_delta_text = f"{round_away_from_zero(delta_2025):,.0f}"
            else:
                pop_delta_text = "N/A"

            pop_df["Baseline"] = round_away_from_zero(pop_df["Baseline"])
            pop_df["Scenario"] = round_away_from_zero(pop_df["Scenario"])
            fig_pop = px.line(pop_df, x="year", y=["Baseline", "Scenario"], markers=True,
                              title=f"{country} -- Total population (baseline vs scenario)")
            fig_pop.update_traces(
                selector=dict(name="Scenario"),
                line=dict(color="#7b3fe4", dash="dash", width=3)
            )
            fig_pop.update_traces(
                selector=dict(name="Baseline"),
                line=dict(color="#2e9fb3", width=2)
            )
            fig_pop.update_yaxes(tickformat=",.0f")
            fig_pop.update_xaxes(automargin=True)
            fig_pop.update_yaxes(automargin=True)
            fig_pop.update_traces(hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")
        else:
            pop_df["Baseline"] = round_away_from_zero(pop_df["Baseline"])
            fig_pop = px.line(pop_df, x="year", y="Baseline", markers=True,
                              title=f"{country} -- Total population (baseline)")
            fig_pop.update_yaxes(tickformat=",.0f")
            fig_pop.update_xaxes(automargin=True)
            fig_pop.update_yaxes(automargin=True)
            fig_pop.update_traces(hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")
            pop_delta_text = "0" if scenario_name == "Baseline" else "N/A"

    # -------- (E) Origin map + treemap --------
    if treemap_year is None:
        fig_map = px.choropleth(title="Origin map unavailable (missing year).")
        fig_tree = px.treemap(title="Treemap unavailable (missing year).")
    else:
        map_df = build_origin_map_df(country, int(treemap_year), scenario_name)
        if map_df.empty:
            fig_map = px.choropleth(title="Origin map unavailable (no data).")
        else:
            fig_map = px.choropleth(
                map_df,
                locations="iso3_orig",
                color="value",
                color_continuous_scale="Blues",
                projection="natural earth",
                title=f"{country} -- Origin map at {treemap_year}",
            )
            fig_map.update_layout(margin=dict(t=50, l=10, r=10, b=10))
            fig_map.update_geos(fitbounds="locations")
            fig_map.update_coloraxes(colorbar_tickformat=",.0f")
            fig_map.update_traces(hovertemplate="%{location}<br>%{z:,.0f}<extra></extra>")
            fig_map.add_trace(
                go.Scattergeo(
                    locations=[country],
                    locationmode="ISO-3",
                    marker=dict(size=10, color="#887bfd", line=dict(color="#5347cd", width=1.5)),
                    name="Destination",
                    showlegend=False,
                    hovertemplate=f"{country} (destination)<extra></extra>",
                )
            )

        tree_df = build_treemap_df(country, int(treemap_year), scenario_name)
        if tree_df.empty:
            fig_tree = px.treemap(title="Treemap unavailable (no data).")
        else:
            color_map = {c: c for c in tree_df["color_hex"].unique().tolist()}
            fig_tree = px.treemap(
                tree_df,
                ids="id",
                parents="parent",
                names="label",
                values="value",
                color="color_hex",
                color_discrete_map=color_map,
                title=f"{country} -- Ethnic impact treemap at {treemap_year}",
            )
            fig_tree.update_traces(root_color="lightgrey")
            fig_tree.update_layout(margin=dict(t=50, l=10, r=10, b=10))
            fig_tree.update_traces(hovertemplate="%{label}<br>%{value:,.0f}<extra></extra>")

    # -------- (F) Policy insights --------
    insights = []
    if scenario_name != "Baseline" and not scen.empty:
        net = scen["delta_migrants"].dropna().mean()
        din = scen["delta_in"].dropna().mean()
        dout = scen["delta_out"].dropna().mean()

        direction = "net inflow" if net > 0 else "net outflow"
        insights.append((
            "Net migration",
            f"The selected scenario results in a {direction} of approximately "
            f"{abs(net):,.0f} people in 2025, driven by "
            f"{'increased inflows' if din > dout else 'increased outflows'}."
        ))

        scen_counts = scen[["ethnic_group", "delta_count"]].dropna().copy()
        scen_counts["delta_count"] = pd.to_numeric(scen_counts["delta_count"], errors="coerce").fillna(0.0)

        incoming_groups = (
            scen_counts[scen_counts["delta_count"] > 0]
            .sort_values("delta_count", ascending=False)
            .head(3)["ethnic_group"]
            .tolist()
        )
        outgoing_groups = (
            scen_counts[scen_counts["delta_count"] < 0]
            .assign(delta_abs=lambda d: d["delta_count"].abs())
            .sort_values("delta_abs", ascending=False)
            .head(3)["ethnic_group"]
            .tolist()
        )

        def fmt_top(groups: list[str]) -> str:
            if not groups:
                return "no dominant ethnic group"
            if len(groups) == 1:
                return groups[0]
            if len(groups) == 2:
                return f"{groups[0]} and {groups[1]}"
            return f"{groups[0]}, {groups[1]}, and {groups[2]}"

        if "Aid_" in scenario_name:
            amount = max(net, 0.0)
            insights.append((
                "Aid",
                "Policies that ease migration are associated with an inflow of "
                f"{amount:,.0f} migrants, mainly from {fmt_top(incoming_groups)}."
            ))
        if "Conflict_internal_" in scenario_name:
            out_amount = max(-net, 0.0)
            insights.append((
                "Conflict internal",
                "Rising internal conflict may drive an outflow of "
                f"{out_amount:,.0f} people, mainly from {fmt_top(outgoing_groups)}."
            ))
        if "Conflict_external_" in scenario_name:
            amount = max(net, 0.0)
            insights.append((
                "Conflict external",
                f"External conflict pressure may increase inflows to {country} by "
                f"{amount:,.0f}, primarily from {fmt_top(incoming_groups)}."
            ))

        top_groups = (
            scen.assign(abs_dc=scen["delta_count"].abs())
                .sort_values("abs_dc", ascending=False)
                .head(3)["ethnic_group"]
                .tolist()
        )
        if top_groups:
            insights.append((
                "Demographic sensitivity",
                "Concentrated among the following ethnic groups: " + ", ".join(top_groups) + "."
            ))

        od_sub = odm[
            (odm["iso3_dest"] == country) &
            (odm["view_type"] == "SCENARIO") &
            (odm["scenario_name"] == scenario_name)
        ]
        if not od_sub.empty:
            top_orig = (
                od_sub.sort_values("delta_stock_od", ascending=False)
                .head(3)["iso3_orig"]
                .tolist()
            )
            if top_orig:
                insights.append((
                    "Migration pressure",
                    "Primarily associated with " + ", ".join(top_orig) + " as origin countries."
                ))

        insights.append((
            "Planning note",
            "This scenario exhibits higher demographic volatility, which may warrant "
            "wider uncertainty bounds in forward population planning."
        ))
    else:
        insights.append((
            "Baseline",
            "Displayed values represent trend-based forecasts without exogenous geopolitical shocks."
        ))

    insights_view = html.Ul([html.Li([html.Strong(f"{label}: "), text]) for label, text in insights])
    preview = f"{insights[0][0]}: {insights[0][1]}" if insights else ""
    modal_style = {"display": "flex"} if insights_open else {"display": "none"}

    return (
        fig_share, fig_count, fig_delta, kpi_row, horizon_children,
        origin_countries_children, origin_ethnic_children,
        fig_pop, pop_delta_text, fig_map, fig_tree, preview, insights_view, modal_style
    )


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
