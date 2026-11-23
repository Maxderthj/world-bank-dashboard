# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.3.0",
#     "marimo>=0.25.2",
#     "numpy==2.5.5",
#     "pandas==3.1.1",
#     "pingouin==0.7.0",
# ]
# ///
import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    import pingouin as pg

    return alt, mo, np, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1YY5iwL8J53umfHMNhJd1m-MbRPtRpX65oyxhq1KjzuI/"
    doc_format = "export?format=csv"

    url = base_url + doc_id + doc_format

    df_raw = pd.read_csv(url)
    return (df_raw,)


@app.cell
def _(df_raw, np):
    df = df_raw.copy()
    df["year"] = df["date"].str.split("-").str[0].astype(int)
    df = df[(df["year"] >= 2000) & (df["year"] <= 2020)].reset_index(drop=True)

    df["gdp_per_capita"] = np.where(
        df["population"] > 0,
        df["GDP_current_US"] / df["population"],
        np.nan,
    )

    df["CO2_emisions_per_capita"] = np.where(
        df["population"] > 0,
        df['CO2_emisions']
        * 1000 / df["population"],
        np.nan,
    )
    return (df,)


@app.cell
def _(df):
    five_countries = [
        "Germany",
        "Mexico",
        "United States",
        "India",
        "Korea, Rep.",
    ]

    df_base = df[
        df["country"].isin(five_countries)
    ][
        [
            "country",
            "year",
            "life_expectancy_at_birth",
            "gdp_per_capita",
            "renewvable_energy_consumption%",
            "CO2_emisions_per_capita",
            "inflation_annual%"
        ]
    ].copy()
    return (df_base,)


@app.cell
def _(mo):
    main_indicator = "renewvable_energy_consumption%"

    indicator_labels = {
        "GDP per capita (US$)": "gdp_per_capita",
        "CO2 emissions per capita (t)": "CO2_emisions_per_capita",
        "Annual inflation (%)": "inflation_annual%",
        "Life expectancy at birth (years)": "life_expectancy_at_birth",
    }

    column_labels = {column: label for label, column in indicator_labels.items()}
    column_labels[main_indicator] = "Renewable energy (% of final energy use)"

    indicator_dd = mo.ui.dropdown(
        options=indicator_labels,
        value="GDP per capita (US$)",
        label="Compare with: ",
    )
    return column_labels, indicator_dd, main_indicator


@app.cell
def _(mo):
    ## show_value off (it shows years as "2,000"), the header shows the period instead; debounce: update when the slider is released, partially written by AI
    year_slider = mo.ui.range_slider(
        start=2000, stop=2020, step=1, value=[2000, 2020],
        label="Period: ", full_width=True, show_value=False, debounce=True,
    )
    return (year_slider,)


@app.cell
def _(df_base, indicator_dd, main_indicator, mo, year_slider):
    indicator = indicator_dd.value
    y0, y1 = year_slider.value

    df_selected = (
        df_base[['country', 'year', main_indicator, indicator]]
        .dropna(subset=[indicator, main_indicator])
        .query("@y0 <= year <= @y1")
        .reset_index(drop=True)
    )

    df_selected["year"] = df_selected["year"].astype("str")

    mo.stop(df_selected.empty, mo.md("no data in selected period"))
    return df_selected, indicator


@app.cell
def _(indicator_dd, mo, year_slider):
    ## header layout (title, three cards, controls) partially written by AI

    ## text of the three cards (claim, indicators, countries) partially written by AI
    _cards = [
        (
            "The claim",
            "Opponents of climate policy often warn that switching to renewable energy slows growth and pushes up prices. "
            "Because this argument shapes energy debates, we put it to the test.",
        ),
        (
            "The indicators",
            "The renewable share of final energy use stands for the green transition. "
            "GDP per capita, inflation and life expectancy show whether people end up poorer. "
            "CO₂ per capita checks whether renewables really replace fossil fuels.",
        ),
        (
            "The countries",
            "Germany, Mexico, the United States, India and South Korea span three continents, "
            "high and lower incomes and very different starting points in the energy transition.",
        ),
    ]

    claim_section = mo.vstack([
        mo.md('# Group 2 · "The green transition makes countries poorer."'),
        mo.md("*Dashboard by Ko-Hsin Lo and Max Mausolf*"),
        mo.hstack(
            [
                mo.md(f"**{_title}**\n\n{_text}").style(
                    {"border-left": "3px solid #c8c8c8", "padding": "0 14px", "height": "100%"}
                )
                for _title, _text in _cards
            ],
            widths="equal",
            gap=1.5,
            wrap=True,
            align="stretch",
        ),
    ])

    ## usage line partially written by AI
    _usage = mo.md(
        "<small>Choose an indicator and a period – the scatterplot, the tests and the verdict update. "
        "The tabs *Over time* and *Distributions* show the trends and the checks behind the method.</small>"
    )

    mo.vstack([
        claim_section,
        mo.hstack(
            [indicator_dd, year_slider, mo.md(f"**{year_slider.value[0]}–{year_slider.value[1]}**")],
            widths=[4, 6, 1],
            align="center",
            gap=2,
        ),
        _usage,
    ])
    return


@app.cell
def _(alt, column_labels, df_selected, indicator, main_indicator):
    ## axes not forced to start at zero, tooltip only on the points, shorter title, partially written by AI
    _base = alt.Chart(df_selected).encode(
        x=alt.X(f"{indicator}:Q", title=column_labels[indicator], scale=alt.Scale(zero=False)),
        y=alt.Y(f"{main_indicator}:Q", title=column_labels[main_indicator], scale=alt.Scale(zero=False)),
        color=alt.Color("country:N", title="Country"),
    )

    scatter = _base.mark_circle(size=40).encode(
        tooltip=[
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip(f"{indicator}:Q", title=column_labels[indicator], format=",.2f"),
            alt.Tooltip(f"{main_indicator}:Q", title=column_labels[main_indicator], format=".1f"),
        ]
    )

    _line = _base.transform_regression(indicator, main_indicator, groupby=["country"]).mark_line()

    full_scatter_plt = (scatter + _line).properties(
        width=420, height=300, title="Each point is one country in one year"
    )
    return (full_scatter_plt,)


@app.cell
def _(alt, column_labels, df_selected, indicator, main_indicator):
    ## one small histogram per country with its own bins (in a facet all countries share the same bins), partially written by AI
    def _histograms(column):
        _countries = sorted(df_selected["country"].unique())
        return alt.hconcat(*[
            alt.Chart(df_selected[df_selected["country"] == _c]).mark_bar().encode(
                x=alt.X(f"{column}:Q", title=None, bin=alt.Bin(maxbins=8)),
                y=alt.Y("count():Q", title="years" if _i == 0 else None),
            ).properties(width=110, height=80, title=_c)
            for _i, _c in enumerate(_countries)
        ]).resolve_scale(y="shared").properties(title=column_labels[column])

    main_bar_plt = _histograms(main_indicator)
    chosen_bar_plt = _histograms(indicator)

    bar_plots = alt.vconcat(main_bar_plt, chosen_bar_plt)
    return (bar_plots,)


@app.cell
def _(
    bar_plots,
    column_labels,
    df_selected,
    indicator,
    main_indicator,
    mo,
    pg,
):
    ## only countries with 5+ years (like the tests), rounded tables with readable names, partially written by AI
    _years = df_selected.groupby("country")["year"].transform("count")
    _df_check = df_selected[_years >= 5]

    def _normality(column):
        return round(
            pg.normality(_df_check, dv=column, group="country")[["pval", "normal"]], 3
        ).rename(columns={"pval": "Shapiro–Wilk p", "normal": "normal?"})

    if _df_check.empty:
        _checks = mo.callout(
            mo.md("Too few years in this period for the skewness and normality checks."), kind="warn"
        )
    else:
        _checks = mo.accordion({
            "Skewness": round(_df_check.groupby("country")[[main_indicator, indicator]].skew(), 2).rename(columns=column_labels),
            f"Normality: {column_labels[main_indicator]}": _normality(main_indicator),
            f"Normality: {column_labels[indicator]}": _normality(indicator),
        })

    assumptions = mo.vstack([bar_plots, _checks])
    return (assumptions,)


@app.cell
def _(np):
    def interpret_r(r):
        if np.abs(r) < 0.1:
            return "negligible"
        elif np.abs(r) < 0.3:
            return "small"
        elif np.abs(r) < 0.5:
            return "moderate"
        else: return "large"

    return (interpret_r,)


@app.cell
def _(alt, df_selected, indicator, main_indicator, mo, pd, pg):
    #correlation test
    test = "spearman"

    ## method text partially written by AI
    method_text = mo.md("""
        **Method: Spearman.** Before looking at any results, we checked all indicator pairs per country (2000–2020): for every pair, at least one country is clearly skewed (|skew| > 1) and not normally distributed (Shapiro–Wilk p < 0.05), and the scatterplots show curved patterns or single extreme years in some countries. With only about 20 years per country, normality cannot be shown reliably anyway, so all tests use Spearman, which compares ranks, captures relationships that are not straight lines (monotonic) and gives extreme years less weight. Since all tests use Spearman, the results are comparable across countries and indicators.
        """)

    corrs = list()
    skipped = list()


    ## texts of the messages for skipped countries partially written by AI
    for _country in df_selected["country"].unique():
        _filtered_df = df_selected[df_selected["country"]==_country]

        if len(_filtered_df["year"].unique()) < 5:
            skipped.append(f"**{_country}** has fewer than 5 years with data in this period, so it is not tested.")
            continue

        elif (_filtered_df[main_indicator].nunique() == 1) | (_filtered_df[indicator].nunique() == 1):
            skipped.append(f"For **{_country}**, one of the two indicators does not change in this period, so it is not tested.")
            continue

        else:
            _df = pg.corr(_filtered_df[main_indicator], _filtered_df[indicator], method=test)
            _df["country"] = _country
            corrs.append(_df)

    ## stop check moved after the loop, partially written by AI
    mo.stop(
        len(corrs) == 0,
        mo.callout(mo.md("No country has enough data for this period. Please choose a longer period."), kind="warn"),
    )

    corrs_df = pd.concat(corrs)
    corrs_df["significant?"] = (corrs_df["p_val"] < 0.05).map({True: "statistically significant", False: "not significant"})
    corrs_df = round(corrs_df, 4)



    _order = corrs_df.sort_values("r")["country"].tolist()

    ## readable axis titles, grey tones for significance (country colours stay for the countries), tooltip with country, partially written by AI
    corr_histo = alt.Chart(corrs_df).mark_bar().encode(
        x=alt.X("country:N", sort=_order, title=None, axis=alt.Axis(labelAngle=-40)),
        y=alt.Y("r:Q", title="Spearman r", scale=alt.Scale(domain=[-1, 1])),
        color=alt.Color(
            "significant?:N",
            title=None,
            scale=alt.Scale(
                domain=["statistically significant", "not significant"],
                range=["#555555", "#c8c8c8"],
            ),
            legend=alt.Legend(orient="bottom", direction="vertical"),
        ),
        tooltip=[
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("r:Q", title="Spearman r", format=".2f"),
            alt.Tooltip("p_val:Q", title="p-value", format=".3f"),
            alt.Tooltip("n:Q", title="Years (n)"),
        ],
    ).properties(width=180, height=300, title="Spearman r per country")
    return corr_histo, corrs_df, method_text, skipped


@app.cell
def _(corrs_df, indicator, interpret_r, mo, year_slider):
    ## verdict cell (logic and all verdict texts) partially written by AI
    # direction the claim expects: -1 = negative r, +1 = positive r
    # CO2 is not part of the claim: it checks whether renewables actually replace fossil energy
    expected_direction = {
        "gdp_per_capita": -1,
        "inflation_annual%": 1,
        "life_expectancy_at_birth": -1,
        "CO2_emisions_per_capita": -1,
    }

    _is_check = indicator == "CO2_emisions_per_capita"
    _dir = expected_direction[indicator]
    _y0, _y1 = year_slider.value

    _n_tested = len(corrs_df)
    _sig= corrs_df["p_val"] < 0.05
    _expected = corrs_df["r"] * _dir > 0
    _opposite = corrs_df["r"] * _dir < 0  # r = 0 counts in neither direction

    _n_expected = int(_expected.sum())
    _n_opposite = int(_opposite.sum())
    _n_zero = _n_tested - _n_expected - _n_opposite
    _n_sig_expected = int((_expected & _sig).sum())
    _n_sig_opposite = int((_opposite & _sig).sum())

    def _countries(n):
        return "1 country" if n == 1 else f"{n} countries"

    def _sig_phrase(k, n):
        if n == 1:
            return "significant" if k == 1 else "not significant"
        if k == n:
            return "both significant" if n == 2 else "all significant"
        if k == 0:
            return "none significant"
        return f"{k} of them significant"

    def _strength(mask):
        return interpret_r(corrs_df.loc[mask, "r"].abs().median())

    # sentence 1: countries in the expected direction (strength, significance)
    _what = (
        "CO₂ per capita falls as the renewable share rises"
        if _is_check
        else "the correlation goes in the direction the claim expects"
    )
    if _n_expected == 0:
        _sentence_1 = f"In none of the {_n_tested} countries {_what}."
    else:
        _sentence_1 = (
            f"In {_n_expected} of {_n_tested} countries {_what} "
            f"({_strength(_expected)}, {_sig_phrase(_n_sig_expected, _n_expected)})."
        )

    # sentence 2: countries in the opposite direction
    if _n_opposite == 0:
        _sentence_2 = ""
    else:
        if _n_zero > 0:
            _other = _countries(_n_opposite)
        elif _n_expected == 0:
            _other = f"all {_n_opposite}"
        elif _n_opposite == 1:
            _other = "the other country"
        else:
            _other = f"the other {_n_opposite}"
        _sentence_2 = (
            f" In {_other}, it goes the opposite way "
            f"({_strength(_opposite)}, {_sig_phrase(_n_sig_opposite, _n_opposite)})."
        )
    if _n_zero > 0:
        _sentence_2 += f" In {_countries(_n_zero)}, there is no correlation at all (r = 0)."

    # verdict: rule fixed before looking at the results (4 of 5 countries)
    if _n_sig_expected >= 4:
        _verdict = "supports"
    elif _n_sig_opposite >= 4:
        _verdict = "contradicts"
    elif _sig.sum() <= 1:
        _verdict = "cannot tell"
    else:
        _verdict = "mixed"

    ## verdict sentences partially written by AI
    _claim_words = {
        "supports": "the data supports the claim",
        "contradicts": "the data contradicts the claim",
        "mixed": "the data gives a mixed picture",
        "cannot tell": "the data cannot tell",
    }
    _check_words = {
        "supports": "the transition is real: in most countries renewables replace fossil energy",
        "contradicts": "in most countries renewables rise without CO₂ falling",
        "mixed": "the transition is real in some countries, not in others",
        "cannot tell": "the data cannot tell whether renewables replace fossil energy",
    }

    if _is_check:
        _verdict_sentence = (
            f"**Check (CO₂ is not part of the claim):** for these countries in {_y0}–{_y1}, "
            f"{_check_words[_verdict]}."
        )
    else:
        _verdict_sentence = (
            f"**Verdict: {_verdict}.** For these countries in {_y0}–{_y1}, {_claim_words[_verdict]}."
        )

    ## caveat text partially written by AI
    _caveat = (
        "Many indicators change steadily over time, so a strong correlation may only reflect a shared trend "
        "(see *Over time tab*), and a correlation cannot show that the green transition causes these changes."
    )

    verdict_text = mo.md(f"{_sentence_1}{_sentence_2} {_verdict_sentence} {_caveat}")
    return (verdict_text,)


@app.cell
def _(corrs_df, mo, pd):
    ### readable test table: only the columns we need, rounded, "< 0.001" instead of 0.0, written by AI
    _df = corrs_df.reset_index(drop=True)

    corr_table = mo.ui.table(
        pd.DataFrame({
            "Country": _df["country"],
            "Years (n)": _df["n"],
            "Spearman r": _df["r"].round(2),
            "95% CI": _df["CI95"].apply(lambda ci: f"[{ci[0]:.2f}, {ci[1]:.2f}]"),
            "p-value": _df["p_val"].apply(lambda p: "< 0.001" if p < 0.001 else f"{p:.3f}"),
            "Significant?": (_df["p_val"] < 0.05).map({True: "yes", False: "no"}),
        }),
        selection=None,
        pagination=False,
        show_column_summaries=False,
        show_data_types=False,
        show_download=False,
        show_search=False,
    )
    return (corr_table,)


@app.cell
def _(alt, column_labels, df_selected, indicator, main_indicator):
    ## partially written by AI
    _df_lines = df_selected.assign(year=df_selected["year"].astype(int))

    main_line_plt = alt.Chart(_df_lines).mark_line(point=True).encode(
        x=alt.X("year:Q", title="Year", axis=alt.Axis(format="d", tickCount=5, tickMinStep=1), scale=alt.Scale(zero=False)),
        y=alt.Y(f"{main_indicator}:Q", title=column_labels[main_indicator], scale=alt.Scale(zero=False)),
        color=alt.Color("country:N", title="Country"),
        tooltip=[
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("year:Q", title="Year", format="d"),
            alt.Tooltip(f"{main_indicator}:Q", title=column_labels[main_indicator], format=".1f"),
        ],
    ).properties(width=300, height=250, title=f"{column_labels[main_indicator]} over the years")

    chosen_line_plt = alt.Chart(_df_lines).mark_line(point=True).encode(
        x=alt.X("year:Q", title="Year", axis=alt.Axis(format="d", tickCount=5, tickMinStep=1), scale=alt.Scale(zero=False)),
        y=alt.Y(f"{indicator}:Q", title=column_labels[indicator], scale=alt.Scale(zero=False)),
        color=alt.Color("country:N", title="Country"),
        tooltip=[
            alt.Tooltip("country:N", title="Country"),
            alt.Tooltip("year:Q", title="Year", format="d"),
            alt.Tooltip(f"{indicator}:Q", title=column_labels[indicator], format=",.2f"),
        ],
    ).properties(width=300, height=250, title=f"{column_labels[indicator]} over the years")

    line_plots = alt.hconcat(main_line_plt, chosen_line_plt)
    return (line_plots,)


@app.cell
def _(mo):
    ### remembers the open tab, so changing the controls does not jump back to the first tab, written by AI
    get_tab, set_tab = mo.state("Claim check")
    return get_tab, set_tab


@app.cell
def _(
    assumptions,
    corr_histo,
    corr_table,
    full_scatter_plt,
    get_tab,
    line_plots,
    method_text,
    mo,
    set_tab,
    skipped,
    verdict_text,
):
    ## the only cell that shows the main view: tabs with claim check, over time and distributions, partially written by AI
    _skipped_note = (
        mo.callout(mo.md("<br>".join(skipped)), kind="warn") if skipped else mo.md("")
    )

    dashboard_tabs = mo.ui.tabs(
        {
            "Claim check": mo.vstack([
                mo.hstack([full_scatter_plt, corr_histo], justify="start", gap=3, wrap=True, align="start"),
                corr_table,
                _skipped_note,
                verdict_text,
                method_text,
            ]),
            "Over time": line_plots,
            "Distributions": assumptions,
        },
        value=get_tab(),
        on_change=set_tab,
    )
    dashboard_tabs
    return


if __name__ == "__main__":
    app.run()
