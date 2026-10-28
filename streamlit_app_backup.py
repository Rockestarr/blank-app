import streamlit as st
import requests
import pandas as pd


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Investment Analyst",
    page_icon="📈",
    layout="wide"
)

st.title("📈 AI Investment Analyst")

st.write(
    "Enter a stock ticker to analyze financial quality, "
    "growth, profitability, cash flow, financial health, "
    "shareholder quality, and valuation."
)


# =========================================================
# API CONFIGURATION
# =========================================================

api_key = st.secrets["FMP_API_KEY"]

BASE_URL = "https://financialmodelingprep.com/stable"


@st.cache_data(ttl=3600)
def get_fmp_data(endpoint, ticker, limit=5):
    url = f"{BASE_URL}/{endpoint}"

    params = {
        "symbol": ticker,
        "limit": limit,
        "apikey": api_key
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(
            f"FMP API error {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        raise Exception(
            f"No data returned from '{endpoint}'. "
            "The ticker may be invalid or this endpoint may "
            "not be included in your FMP plan."
        )

    return data


# =========================================================
# FORMATTING FUNCTIONS
# =========================================================

def money(value):
    if value is None:
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.2f}K"

    return f"${value:,.2f}"


def percent(value):
    if value is None:
        return "N/A"

    return f"{float(value) * 100:.1f}%"


def multiple(value):
    if value is None:
        return "N/A"

    return f"{float(value):.2f}x"


def number_of_shares(value):
    if value is None:
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    return f"{value:,.0f}"


def safe_divide(numerator, denominator):
    if (
        numerator is None
        or denominator is None
        or denominator == 0
    ):
        return None

    return numerator / denominator


def calculate_growth(latest, previous):
    if (
        latest is None
        or previous is None
        or previous == 0
    ):
        return None

    return (latest / previous) - 1


def calculate_cagr(latest, oldest, years):
    if (
        latest is None
        or oldest is None
        or latest <= 0
        or oldest <= 0
        or years <= 0
    ):
        return None

    return (latest / oldest) ** (1 / years) - 1


def trend_label(change, threshold=0.005):
    if change is None:
        return "Not available"

    if change > threshold:
        return "Improving"

    if change < -threshold:
        return "Declining"

    return "Stable"


def get_first_value(dictionary, possible_keys):
    for key in possible_keys:
        value = dictionary.get(key)

        if value is not None:
            return value

    return None


# =========================================================
# SCORING FUNCTIONS
# =========================================================

def score_growth(
    revenue_growth,
    revenue_cagr,
    eps_growth
):
    score = 0

    if revenue_growth is not None:
        if revenue_growth >= 0.20:
            score += 8
        elif revenue_growth >= 0.10:
            score += 6
        elif revenue_growth >= 0.05:
            score += 4
        elif revenue_growth > 0:
            score += 2

    if revenue_cagr is not None:
        if revenue_cagr >= 0.15:
            score += 7
        elif revenue_cagr >= 0.08:
            score += 5
        elif revenue_cagr > 0:
            score += 3

    if eps_growth is not None:
        if eps_growth >= 0.20:
            score += 5
        elif eps_growth >= 0.10:
            score += 4
        elif eps_growth > 0:
            score += 2

    return min(score, 20)


def score_profitability(
    operating_margin,
    net_margin,
    margin_change
):
    score = 0

    if operating_margin is not None:
        if operating_margin >= 0.20:
            score += 7
        elif operating_margin >= 0.10:
            score += 5
        elif operating_margin > 0:
            score += 3

    if net_margin is not None:
        if net_margin >= 0.15:
            score += 5
        elif net_margin >= 0.08:
            score += 4
        elif net_margin > 0:
            score += 2

    if margin_change is not None:
        if margin_change > 0.01:
            score += 3
        elif margin_change >= 0:
            score += 2

    return min(score, 15)


def score_cash_flow(
    free_cash_flow,
    fcf_margin,
    fcf_growth
):
    score = 0

    if free_cash_flow is not None and free_cash_flow > 0:
        score += 5

    if fcf_margin is not None:
        if fcf_margin >= 0.15:
            score += 5
        elif fcf_margin >= 0.08:
            score += 4
        elif fcf_margin > 0:
            score += 2

    if fcf_growth is not None:
        if fcf_growth >= 0.15:
            score += 5
        elif fcf_growth > 0:
            score += 3

    return min(score, 15)


def score_financial_health(
    net_cash,
    current_ratio,
    debt_to_ocf,
    operating_cash_flow
):
    score = 0

    if net_cash is not None:
        if net_cash > 0:
            score += 7
        elif (
            operating_cash_flow is not None
            and operating_cash_flow > 0
        ):
            score += 3

    if current_ratio is not None:
        if current_ratio >= 1.5:
            score += 5
        elif current_ratio >= 1.0:
            score += 3

    if debt_to_ocf is not None:
        if debt_to_ocf <= 1:
            score += 5
        elif debt_to_ocf <= 3:
            score += 3

    if (
        operating_cash_flow is not None
        and operating_cash_flow > 0
    ):
        score += 3

    return min(score, 20)


def score_shareholder_quality(
    share_change,
    stock_comp_percent_revenue
):
    score = 0

    if share_change is not None:
        if share_change <= 0:
            score += 5
        elif share_change <= 0.02:
            score += 3
        elif share_change <= 0.05:
            score += 1

    if stock_comp_percent_revenue is not None:
        if stock_comp_percent_revenue <= 0.03:
            score += 5
        elif stock_comp_percent_revenue <= 0.08:
            score += 3
        elif stock_comp_percent_revenue <= 0.15:
            score += 1

    return min(score, 10)


def score_valuation(
    pe_ratio,
    ev_to_sales,
    ev_to_ebitda,
    ev_to_fcf,
    fcf_yield,
    earnings_yield,
    revenue_growth
):
    score = 0

    # P/E: maximum 4 points
    if pe_ratio is not None and pe_ratio > 0:
        if pe_ratio <= 15:
            score += 4
        elif pe_ratio <= 25:
            score += 3
        elif pe_ratio <= 35:
            score += 2
        elif pe_ratio <= 50:
            score += 1

    # EV/Sales: maximum 3 points
    if ev_to_sales is not None and ev_to_sales > 0:
        if ev_to_sales <= 2:
            score += 3
        elif ev_to_sales <= 5:
            score += 2
        elif ev_to_sales <= 10:
            score += 1

    # EV/EBITDA: maximum 3 points
    if ev_to_ebitda is not None and ev_to_ebitda > 0:
        if ev_to_ebitda <= 12:
            score += 3
        elif ev_to_ebitda <= 20:
            score += 2
        elif ev_to_ebitda <= 30:
            score += 1

    # EV/FCF: maximum 3 points
    if ev_to_fcf is not None and ev_to_fcf > 0:
        if ev_to_fcf <= 15:
            score += 3
        elif ev_to_fcf <= 25:
            score += 2
        elif ev_to_fcf <= 40:
            score += 1

    # FCF yield: maximum 3 points
    if fcf_yield is not None:
        if fcf_yield >= 0.07:
            score += 3
        elif fcf_yield >= 0.04:
            score += 2
        elif fcf_yield >= 0.02:
            score += 1

    # Earnings yield: maximum 2 points
    if earnings_yield is not None:
        if earnings_yield >= 0.06:
            score += 2
        elif earnings_yield >= 0.03:
            score += 1

    # Growth adjustment: maximum 2 points
    if revenue_growth is not None:
        if revenue_growth >= 0.20:
            if (
                pe_ratio is not None
                and pe_ratio > 0
                and pe_ratio <= 50
            ):
                score += 2

        elif revenue_growth >= 0.10:
            if (
                pe_ratio is not None
                and pe_ratio > 0
                and pe_ratio <= 35
            ):
                score += 2

        elif revenue_growth > 0:
            if (
                pe_ratio is not None
                and pe_ratio > 0
                and pe_ratio <= 25
            ):
                score += 1

    return min(score, 20)


# =========================================================
# USER INPUT
# =========================================================

ticker = st.text_input(
    "Ticker Symbol",
    placeholder="Example: HOOD, SNOW, AMZN, AAPL"
).upper().strip()

analyze = st.button(
    "Analyze Investment",
    type="primary",
    use_container_width=True
)


# =========================================================
# MAIN APPLICATION
# =========================================================

if analyze:

    if not ticker:
        st.warning("Enter a ticker symbol first.")

    else:

        with st.spinner(
            f"Building a complete investment analysis for "
            f"{ticker}..."
        ):

            try:

                # =================================================
                # RETRIEVE ALL DATA
                # =================================================

                income_data = get_fmp_data(
                    "income-statement",
                    ticker,
                    5
                )

                balance_data = get_fmp_data(
                    "balance-sheet-statement",
                    ticker,
                    5
                )

                cashflow_data = get_fmp_data(
                    "cash-flow-statement",
                    ticker,
                    5
                )

                key_metrics_data = get_fmp_data(
                    "key-metrics",
                    ticker,
                    5
                )

                ratios_data = get_fmp_data(
                    "ratios",
                    ticker,
                    5
                )

                income = income_data[0]
                balance = balance_data[0]
                cashflow = cashflow_data[0]
                key_metrics = key_metrics_data[0]
                ratios = ratios_data[0]

                st.success(
                    f"Financial and valuation data loaded for "
                    f"{ticker}"
                )

                # =================================================
                # INCOME STATEMENT
                # =================================================

                revenue = income.get("revenue")
                gross_profit = income.get("grossProfit")
                operating_income = income.get("operatingIncome")
                net_income = income.get("netIncome")
                ebitda = income.get("ebitda")

                eps = get_first_value(
                    income,
                    ["epsDiluted", "eps"]
                )

                gross_margin = safe_divide(
                    gross_profit,
                    revenue
                )

                operating_margin = safe_divide(
                    operating_income,
                    revenue
                )

                net_margin = safe_divide(
                    net_income,
                    revenue
                )

                # =================================================
                # BALANCE SHEET
                # =================================================

                cash = balance.get(
                    "cashAndCashEquivalents"
                )

                short_term_investments = balance.get(
                    "shortTermInvestments"
                )

                total_debt = balance.get("totalDebt")
                total_assets = balance.get("totalAssets")

                total_liabilities = balance.get(
                    "totalLiabilities"
                )

                shareholders_equity = balance.get(
                    "totalStockholdersEquity"
                )

                current_assets = balance.get(
                    "totalCurrentAssets"
                )

                current_liabilities = balance.get(
                    "totalCurrentLiabilities"
                )

                total_cash = (
                    (cash or 0)
                    + (short_term_investments or 0)
                )

                net_cash = None

                if total_debt is not None:
                    net_cash = total_cash - total_debt

                current_ratio = safe_divide(
                    current_assets,
                    current_liabilities
                )

                # =================================================
                # CASH FLOW
                # =================================================

                operating_cf = cashflow.get(
                    "operatingCashFlow"
                )

                capex = cashflow.get(
                    "capitalExpenditure"
                )

                free_cash_flow = cashflow.get(
                    "freeCashFlow"
                )

                if (
                    free_cash_flow is None
                    and operating_cf is not None
                    and capex is not None
                ):
                    free_cash_flow = (
                        operating_cf - abs(capex)
                    )

                fcf_margin = safe_divide(
                    free_cash_flow,
                    revenue
                )

                stock_compensation = cashflow.get(
                    "stockBasedCompensation"
                )

                stock_comp_percent_revenue = safe_divide(
                    stock_compensation,
                    revenue
                )

                debt_to_ocf = safe_divide(
                    total_debt,
                    operating_cf
                )

                # =================================================
                # HISTORICAL GROWTH
                # =================================================

                previous_revenue = None
                previous_eps = None
                previous_fcf = None

                if len(income_data) >= 2:
                    previous_revenue = income_data[1].get(
                        "revenue"
                    )

                    previous_eps = get_first_value(
                        income_data[1],
                        ["epsDiluted", "eps"]
                    )

                if len(cashflow_data) >= 2:
                    previous_fcf = cashflow_data[1].get(
                        "freeCashFlow"
                    )

                    if previous_fcf is None:
                        prior_ocf = cashflow_data[1].get(
                            "operatingCashFlow"
                        )

                        prior_capex = cashflow_data[1].get(
                            "capitalExpenditure"
                        )

                        if (
                            prior_ocf is not None
                            and prior_capex is not None
                        ):
                            previous_fcf = (
                                prior_ocf - abs(prior_capex)
                            )

                revenue_growth = calculate_growth(
                    revenue,
                    previous_revenue
                )

                eps_growth = calculate_growth(
                    eps,
                    previous_eps
                )

                fcf_growth = calculate_growth(
                    free_cash_flow,
                    previous_fcf
                )

                revenue_cagr_3y = None

                if len(income_data) >= 4:
                    revenue_cagr_3y = calculate_cagr(
                        revenue,
                        income_data[3].get("revenue"),
                        3
                    )

                # =================================================
                # MARGIN TRENDS
                # =================================================

                previous_operating_margin = None
                previous_net_margin = None

                if len(income_data) >= 2:
                    prior_revenue = income_data[1].get(
                        "revenue"
                    )

                    previous_operating_margin = safe_divide(
                        income_data[1].get(
                            "operatingIncome"
                        ),
                        prior_revenue
                    )

                    previous_net_margin = safe_divide(
                        income_data[1].get("netIncome"),
                        prior_revenue
                    )

                operating_margin_change = None
                net_margin_change = None

                if (
                    operating_margin is not None
                    and previous_operating_margin is not None
                ):
                    operating_margin_change = (
                        operating_margin
                        - previous_operating_margin
                    )

                if (
                    net_margin is not None
                    and previous_net_margin is not None
                ):
                    net_margin_change = (
                        net_margin
                        - previous_net_margin
                    )

                operating_margin_trend = trend_label(
                    operating_margin_change
                )

                net_margin_trend = trend_label(
                    net_margin_change
                )

                # =================================================
                # SHAREHOLDER QUALITY
                # =================================================

                latest_shares = income.get(
                    "weightedAverageShsOutDil"
                )

                previous_shares = None

                if len(income_data) >= 2:
                    previous_shares = income_data[1].get(
                        "weightedAverageShsOutDil"
                    )

                share_change = calculate_growth(
                    latest_shares,
                    previous_shares
                )

                if share_change is None:
                    dilution_status = "Not available"

                elif share_change > 0.05:
                    dilution_status = "High dilution"

                elif share_change > 0.02:
                    dilution_status = "Meaningful dilution"

                elif share_change > 0:
                    dilution_status = "Slight dilution"

                else:
                    dilution_status = (
                        "Flat or declining share count"
                    )

                # =================================================
                # VALUATION METRICS
                # =================================================

                market_cap = get_first_value(
                    key_metrics,
                    ["marketCap", "marketCapitalization"]
                )

                enterprise_value = get_first_value(
                    key_metrics,
                    ["enterpriseValue"]
                )

                ev_to_sales = get_first_value(
                    key_metrics,
                    [
                        "evToSales",
                        "enterpriseValueToSales"
                    ]
                )

                ev_to_ebitda = get_first_value(
                    key_metrics,
                    [
                        "evToEBITDA",
                        "enterpriseValueOverEBITDA"
                    ]
                )

                ev_to_fcf = get_first_value(
                    key_metrics,
                    [
                        "evToFreeCashFlow",
                        "enterpriseValueToFreeCashFlow"
                    ]
                )

                fcf_yield = get_first_value(
                    key_metrics,
                    ["freeCashFlowYield"]
                )

                earnings_yield = get_first_value(
                    key_metrics,
                    ["earningsYield"]
                )

                roic = get_first_value(
                    key_metrics,
                    ["returnOnInvestedCapital"]
                )

                roe = get_first_value(
                    key_metrics,
                    ["returnOnEquity"]
                )

                roa = get_first_value(
                    key_metrics,
                    ["returnOnAssets"]
                )

                pe_ratio = get_first_value(
                    ratios,
                    [
                        "priceToEarningsRatio",
                        "priceEarningsRatio",
                        "peRatio"
                    ]
                )

                price_to_sales = get_first_value(
                    ratios,
                    [
                        "priceToSalesRatio",
                        "priceSalesRatio"
                    ]
                )

                price_to_fcf = get_first_value(
                    ratios,
                    [
                        "priceToFreeCashFlowRatio",
                        "priceFreeCashFlowRatio"
                    ]
                )

                if (
                    price_to_fcf is None
                    and fcf_yield is not None
                    and fcf_yield > 0
                ):
                    price_to_fcf = 1 / fcf_yield

                # =================================================
                # SCORE CALCULATIONS
                # =================================================

                growth_score = score_growth(
                    revenue_growth,
                    revenue_cagr_3y,
                    eps_growth
                )

                profitability_score = score_profitability(
                    operating_margin,
                    net_margin,
                    operating_margin_change
                )

                cashflow_score = score_cash_flow(
                    free_cash_flow,
                    fcf_margin,
                    fcf_growth
                )

                financial_health_score = (
                    score_financial_health(
                        net_cash,
                        current_ratio,
                        debt_to_ocf,
                        operating_cf
                    )
                )

                shareholder_score = (
                    score_shareholder_quality(
                        share_change,
                        stock_comp_percent_revenue
                    )
                )

                valuation_score = score_valuation(
                    pe_ratio,
                    ev_to_sales,
                    ev_to_ebitda,
                    ev_to_fcf,
                    fcf_yield,
                    earnings_yield,
                    revenue_growth
                )

                financial_quality_score = (
                    growth_score
                    + profitability_score
                    + cashflow_score
                    + financial_health_score
                    + shareholder_score
                )

                total_score = (
                    financial_quality_score
                    + valuation_score
                )

                # =================================================
                # REPORT HEADER
                # =================================================

                st.divider()

                st.header(
                    f"{ticker} Complete Investment Analysis"
                )

                st.caption(
                    f"Latest fiscal year: "
                    f"{income.get('fiscalYear', 'N/A')} | "
                    f"Period ending: "
                    f"{income.get('date', 'N/A')}"
                )

                # =================================================
                # SCORECARD
                # =================================================

                st.divider()
                st.header("Investment Scorecard")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Total Investment Score",
                    f"{total_score}/100"
                )

                c2.metric(
                    "Financial Quality",
                    f"{financial_quality_score}/80"
                )

                c3.metric(
                    "Valuation",
                    f"{valuation_score}/20"
                )

                st.progress(
                    min(max(total_score / 100, 0), 1)
                )

                if total_score >= 80:
                    overall_assessment = (
                        "Strong fundamentals and comparatively "
                        "attractive valuation"
                    )

                elif total_score >= 65:
                    overall_assessment = (
                        "Above-average overall investment profile"
                    )

                elif total_score >= 50:
                    overall_assessment = (
                        "Mixed investment profile"
                    )

                elif total_score >= 35:
                    overall_assessment = (
                        "Weak or demanding investment profile"
                    )

                else:
                    overall_assessment = (
                        "High-risk overall investment profile"
                    )

                st.info(
                    f"Model assessment: {overall_assessment}"
                )

                c1, c2, c3, c4, c5, c6 = st.columns(6)

                c1.metric(
                    "Growth",
                    f"{growth_score}/20"
                )

                c2.metric(
                    "Profitability",
                    f"{profitability_score}/15"
                )

                c3.metric(
                    "Cash Flow",
                    f"{cashflow_score}/15"
                )

                c4.metric(
                    "Financial Health",
                    f"{financial_health_score}/20"
                )

                c5.metric(
                    "Shareholder Quality",
                    f"{shareholder_score}/10"
                )

                c6.metric(
                    "Valuation",
                    f"{valuation_score}/20"
                )

                # =================================================
                # VALUATION DASHBOARD
                # =================================================

                st.divider()
                st.header("💰 Valuation Engine")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Market Capitalization",
                    money(market_cap)
                )

                c2.metric(
                    "Enterprise Value",
                    money(enterprise_value)
                )

                c3.metric(
                    "P/E Ratio",
                    multiple(pe_ratio)
                )

                c4.metric(
                    "Price / Sales",
                    multiple(price_to_sales)
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "EV / Sales",
                    multiple(ev_to_sales)
                )

                c2.metric(
                    "EV / EBITDA",
                    multiple(ev_to_ebitda)
                )

                c3.metric(
                    "EV / Free Cash Flow",
                    multiple(ev_to_fcf)
                )

                c4.metric(
                    "Price / Free Cash Flow",
                    multiple(price_to_fcf)
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "FCF Yield",
                    percent(fcf_yield)
                )

                c2.metric(
                    "Earnings Yield",
                    percent(earnings_yield)
                )

                c3.metric(
                    "Return on Invested Capital",
                    percent(roic)
                )

                c4.metric(
                    "Valuation Score",
                    f"{valuation_score}/20"
                )

                if valuation_score >= 16:
                    valuation_assessment = (
                        "Attractive under this model"
                    )

                elif valuation_score >= 11:
                    valuation_assessment = (
                        "Reasonable under this model"
                    )

                elif valuation_score >= 6:
                    valuation_assessment = (
                        "Demanding under this model"
                    )

                else:
                    valuation_assessment = (
                        "Very expensive or metrics unavailable"
                    )

                st.info(
                    f"Valuation assessment: "
                    f"{valuation_assessment}"
                )

                st.caption(
                    "Valuation figures may reflect FMP's latest "
                    "available financial period rather than a "
                    "continuously updated intraday market price. "
                    "Always verify the valuation date before making "
                    "a decision."
                )

                # =================================================
                # FINANCIAL STATEMENTS
                # =================================================

                st.divider()
                st.header("Financial Statements")

                st.subheader("📊 Income Statement")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric("Revenue", money(revenue))
                c2.metric("Gross Profit", money(gross_profit))
                c3.metric(
                    "Operating Income",
                    money(operating_income)
                )
                c4.metric("Net Income", money(net_income))

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Gross Margin",
                    percent(gross_margin)
                )

                c2.metric(
                    "Operating Margin",
                    percent(operating_margin)
                )

                c3.metric(
                    "Net Margin",
                    percent(net_margin)
                )

                c4.metric(
                    "Diluted EPS",
                    f"${eps:.2f}" if eps is not None else "N/A"
                )

                st.subheader("🏦 Balance Sheet")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Cash + Short-Term Investments",
                    money(total_cash)
                )

                c2.metric(
                    "Total Debt",
                    money(total_debt)
                )

                c3.metric(
                    "Net Cash / (Debt)",
                    money(net_cash)
                )

                c4.metric(
                    "Total Assets",
                    money(total_assets)
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Total Liabilities",
                    money(total_liabilities)
                )

                c2.metric(
                    "Shareholders' Equity",
                    money(shareholders_equity)
                )

                c3.metric(
                    "Current Ratio",
                    multiple(current_ratio)
                )

                st.subheader("💵 Cash Flow")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Operating Cash Flow",
                    money(operating_cf)
                )

                c2.metric(
                    "Capital Expenditures",
                    money(capex)
                )

                c3.metric(
                    "Free Cash Flow",
                    money(free_cash_flow)
                )

                c4.metric(
                    "FCF Margin",
                    percent(fcf_margin)
                )

                # =================================================
                # FINANCIAL INTELLIGENCE
                # =================================================

                st.divider()
                st.header("🧠 Financial Intelligence")

                st.subheader("Growth")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Revenue Growth",
                    percent(revenue_growth)
                )

                c2.metric(
                    "3-Year Revenue CAGR",
                    percent(revenue_cagr_3y)
                )

                c3.metric(
                    "Diluted EPS Growth",
                    percent(eps_growth)
                )

                st.subheader("Profitability Trends")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Operating Margin",
                    percent(operating_margin)
                )

                c2.metric(
                    "Prior Operating Margin",
                    percent(previous_operating_margin)
                )

                c3.metric(
                    "Operating Margin Trend",
                    operating_margin_trend
                )

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Net Margin",
                    percent(net_margin)
                )

                c2.metric(
                    "Prior Net Margin",
                    percent(previous_net_margin)
                )

                c3.metric(
                    "Net Margin Trend",
                    net_margin_trend
                )

                st.subheader("Cash Flow Quality")

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "FCF Growth",
                    percent(fcf_growth)
                )

                c2.metric(
                    "Debt / Operating Cash Flow",
                    multiple(debt_to_ocf)
                )

                c3.metric(
                    "Stock-Based Compensation",
                    money(stock_compensation)
                )

                c4.metric(
                    "SBC as % of Revenue",
                    percent(stock_comp_percent_revenue)
                )

                st.subheader("Capital Efficiency")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Return on Invested Capital",
                    percent(roic)
                )

                c2.metric(
                    "Return on Equity",
                    percent(roe)
                )

                c3.metric(
                    "Return on Assets",
                    percent(roa)
                )

                st.subheader("Shareholder Quality")

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Diluted Shares",
                    number_of_shares(latest_shares)
                )

                c2.metric(
                    "Annual Share Change",
                    percent(share_change)
                )

                c3.metric(
                    "Dilution Assessment",
                    dilution_status
                )

                # =================================================
                # HISTORICAL TABLE AND CHARTS
                # =================================================

                st.divider()
                st.header("📈 Historical Financials")

                balance_by_year = {
                    str(item.get("fiscalYear")): item
                    for item in balance_data
                }

                cashflow_by_year = {
                    str(item.get("fiscalYear")): item
                    for item in cashflow_data
                }

                historical_rows = []

                for year_income in income_data:

                    fiscal_year = str(
                        year_income.get("fiscalYear")
                    )

                    year_balance = balance_by_year.get(
                        fiscal_year,
                        {}
                    )

                    year_cashflow = cashflow_by_year.get(
                        fiscal_year,
                        {}
                    )

                    year_revenue = year_income.get("revenue")
                    year_operating_income = year_income.get(
                        "operatingIncome"
                    )
                    year_net_income = year_income.get(
                        "netIncome"
                    )

                    year_fcf = year_cashflow.get(
                        "freeCashFlow"
                    )

                    if year_fcf is None:
                        year_ocf = year_cashflow.get(
                            "operatingCashFlow"
                        )
                        year_capex = year_cashflow.get(
                            "capitalExpenditure"
                        )

                        if (
                            year_ocf is not None
                            and year_capex is not None
                        ):
                            year_fcf = (
                                year_ocf - abs(year_capex)
                            )

                    historical_rows.append(
                        {
                            "Fiscal Year": fiscal_year,
                            "Revenue": year_revenue,
                            "Operating Income":
                                year_operating_income,
                            "Net Income": year_net_income,
                            "Free Cash Flow": year_fcf,
                            "Operating Margin":
                                safe_divide(
                                    year_operating_income,
                                    year_revenue
                                ),
                            "Net Margin":
                                safe_divide(
                                    year_net_income,
                                    year_revenue
                                ),
                            "Cash":
                                year_balance.get(
                                    "cashAndCashEquivalents"
                                ),
                            "Debt":
                                year_balance.get("totalDebt"),
                            "Diluted EPS":
                                get_first_value(
                                    year_income,
                                    ["epsDiluted", "eps"]
                                ),
                            "Diluted Shares":
                                year_income.get(
                                    "weightedAverageShsOutDil"
                                )
                        }
                    )

                history_df = pd.DataFrame(
                    historical_rows
                )

                display_df = history_df.copy()

                display_df["Operating Margin"] = (
                    display_df["Operating Margin"]
                    .apply(percent)
                )

                display_df["Net Margin"] = (
                    display_df["Net Margin"]
                    .apply(percent)
                )

                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                chart_df = history_df.copy()

                chart_df["Fiscal Year"] = (
                    chart_df["Fiscal Year"].astype(str)
                )

                chart_df = chart_df.sort_values(
                    "Fiscal Year"
                )

                chart_df = chart_df.set_index(
                    "Fiscal Year"
                )

                st.subheader("Revenue Trend")

                st.line_chart(
                    chart_df[["Revenue"]]
                )

                st.subheader(
                    "Operating Income and Net Income"
                )

                st.line_chart(
                    chart_df[
                        [
                            "Operating Income",
                            "Net Income"
                        ]
                    ]
                )

                st.subheader("Free Cash Flow Trend")

                st.line_chart(
                    chart_df[["Free Cash Flow"]]
                )

                st.subheader("Margin Trend")

                st.line_chart(
                    chart_df[
                        [
                            "Operating Margin",
                            "Net Margin"
                        ]
                    ]
                )

                # =================================================
                # IMPORTANT MODEL NOTES
                # =================================================

                st.divider()

                st.warning(
                    "The score is a rules-based research model, "
                    "not a buy or sell recommendation. Valuation "
                    "thresholds differ by industry, business model, "
                    "interest-rate environment, cyclicality, and "
                    "growth durability. Banks, insurers, REITs, "
                    "early-stage companies, and commodity producers "
                    "often require specialized valuation methods."
                )

                st.caption(
                    "Financial data source: Financial Modeling Prep. "
                    "The application's Python engine calculates the "
                    "displayed trends and scores. This dashboard is "
                    "for research and educational purposes and is "
                    "not personalized financial advice."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The financial-data request timed out. "
                    "Try the ticker again."
                )

            except requests.exceptions.RequestException as error:

                st.error(
                    "A network error occurred while contacting "
                    "Financial Modeling Prep."
                )

                st.code(str(error))

            except Exception as error:

                st.error(
                    "Unable to complete the investment analysis."
                )

                st.code(str(error))