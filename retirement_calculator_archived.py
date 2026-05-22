"""
Retirement Projections Calculator - Interactive Web Version
Streamlit app with Plotly charts for bambootrading.com.au
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retirement Calculator | Bamboo Trading",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main {background-color: #1C1C2E;}
    h1 {color: #32CD32 !important;}
    h2, h3 {color: #E0E0E0 !important;}
    .stSlider > div > div > div {background-color: #32CD32;}
    [data-testid="stMetricValue"] {font-size: 28px; color: #32CD32;}
    [data-testid="stMetricLabel"] {color: #E0E0E0;}
    .stDownloadButton > button {
        background-color: #32CD32;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ── AGE PENSION CONSTANTS (Sep 2025; Centrelink indexes 20 Mar / 20 Sep) ─────
PENSION_AGE = 67
MAX_PENSION_ANNUAL = {'single': 30000, 'couple': 45000}  # incl pension & energy supplements
ASSETS_TEST_LOWER = {
    ('single', True):  314000,
    ('single', False): 566000,
    ('couple', True):  470000,
    ('couple', False): 722000,
}
ASSETS_TAPER_RATE = 0.078        # $3/ft per $1k = 7.8%/yr
INCOME_FREE_AREA = {'single': 5616, 'couple': 9880}
INCOME_TAPER_RATE = 0.50
DEEMING_THRESHOLD = {'single': 62600, 'couple': 103800}
DEEMING_LOWER, DEEMING_UPPER = 0.0025, 0.0225

# ── HELPERS ──────────────────────────────────────────────────────────────────
def min_drawdown_rate(age):
    if age < 65:    return 0.04
    elif age <= 74: return 0.05
    elif age <= 79: return 0.06
    elif age <= 84: return 0.07
    elif age <= 89: return 0.09
    elif age <= 94: return 0.11
    else:           return 0.14

def calc_age_pension(financial_assets, other_assets, other_income, status, homeowner):
    """Annual Age Pension entitlement — lower of assets test and income test."""
    max_p = MAX_PENSION_ANNUAL[status]

    total_assets = financial_assets + other_assets
    excess_a = max(0, total_assets - ASSETS_TEST_LOWER[(status, homeowner)])
    pension_a = max(0, max_p - excess_a * ASSETS_TAPER_RATE)

    deem_t = DEEMING_THRESHOLD[status]
    if financial_assets <= deem_t:
        deemed = financial_assets * DEEMING_LOWER
    else:
        deemed = deem_t * DEEMING_LOWER + (financial_assets - deem_t) * DEEMING_UPPER
    excess_i = max(0, deemed + other_income - INCOME_FREE_AREA[status])
    pension_i = max(0, max_p - excess_i * INCOME_TAPER_RATE)

    return min(pension_a, pension_i)

def grow_pool(balance, contrib, return_dec, fee_dec, tax_on_profit):
    profit = balance * return_dec
    tax = profit * tax_on_profit
    fees = balance * fee_dec
    return max(0, balance + (profit - tax) + contrib - fees)

# ── TITLE ────────────────────────────────────────────────────────────────────
st.title("🎯 Retirement Projections Calculator")
st.markdown("*Adjust sliders to see real-time retirement projections (Growth + Drawdown)*")
st.markdown("---")

# ── SIDEBAR INPUTS ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📊 Input Parameters")

    with st.expander("👤 Personal & household", expanded=True):
        current_age = st.slider("Your age", 18, 100, 50, 1)
        retirement_age = st.slider("Retirement age", max(current_age + 1, 50), 100, 65, 1)
        status_label = st.radio("Household", ["Single", "Couple"], horizontal=True)
        is_couple = status_label == "Couple"
        status = 'couple' if is_couple else 'single'
        homeowner = st.checkbox("Own your home", value=True,
            help="Principal home is excluded from Age Pension assets test")
        partner_age = st.slider("Partner's age", 18, 100, current_age, 1) if is_couple else None

    with st.expander("💼 Income & assets", expanded=True):
        current_salary = st.number_input(
            "Your salary ($/yr, gross)", 0, 1000000, 100000, 5000, format="%d"
        )
        initial_balance = st.number_input(
            "Your super balance ($)", 0, 10000000, 200000, 10000, format="%d"
        )
        if is_couple:
            partner_salary = st.number_input(
                "Partner's salary ($/yr, gross)", 0, 1000000, 80000, 5000, format="%d"
            )
            partner_balance_input = st.number_input(
                "Partner's super balance ($)", 0, 10000000, 150000, 10000, format="%d"
            )
        else:
            partner_salary = 0
            partner_balance_input = 0

        non_super = st.number_input(
            "Non-super investments ($)", 0, 10000000, 0, 10000, format="%d",
            help="Bank, term deposits, ETFs, shares — counted for Age Pension"
        )
        other_assets = st.number_input(
            "Other assets ($)", 0, 10000000, 0, 10000, format="%d",
            help="Cars, boats, investment property net equity (excludes principal home)"
        )
        other_income_today = st.number_input(
            "Other income in retirement ($/yr, today's $)", 0, 500000, 0, 1000, format="%d",
            help="Net rent, trust distributions etc. (excludes interest — that's deemed)"
        )

    with st.expander("💰 Contributions"):
        salary_sacrifice = st.number_input(
            "Your salary sacrifice ($/yr)", 0, 100000, 0, 1000, format="%d"
        )
        non_concessional = st.number_input(
            "Your non-concessional ($/yr)", 0, 200000, 0, 5000, format="%d"
        )
        if is_couple:
            partner_sacrifice = st.number_input(
                "Partner's salary sacrifice ($/yr)", 0, 100000, 0, 1000, format="%d"
            )
            partner_nc = st.number_input(
                "Partner's non-concessional ($/yr)", 0, 200000, 0, 5000, format="%d"
            )
        else:
            partner_sacrifice = 0
            partner_nc = 0

    with st.expander("📈 Returns & fees"):
        nominal_return_growth = st.slider("Return - growth phase (%)", 0.0, 30.0, 7.0, 0.5)
        nominal_return_retirement = st.slider("Return - retirement phase (%)", 0.0, 30.0, 5.0, 0.5)
        inflation = st.slider("Inflation (%)", 0.0, 10.0, 3.0, 0.5)
        fee_pct = st.slider("Investment fees (% p.a.)", 0.0, 3.0, 0.6, 0.1)
        fee_dollar = st.number_input(
            "Fixed admin fees ($/yr)", 0, 50000, 0, 100, format="%d"
        )

    with st.expander("🏖️ Retirement spending"):
        spending_strategy = st.radio(
            "Strategy", ["Constant", "Life Stage"], horizontal=True,
            help="Life Stage: spending tapers from higher early-years to lower later-years"
        )
        annual_spending = st.number_input(
            "Annual spending ($/yr, today's $)", 0, 500000, 80000, 5000, format="%d"
        )
        if spending_strategy == "Life Stage":
            late_spending = st.number_input(
                "Later-years spending ($/yr, today's $)", 0, 500000, 60000, 5000, format="%d"
            )
            taper_start_age = st.slider(
                "Taper start age", retirement_age, 100, min(retirement_age + 15, 80), 1
            )
            taper_years = st.slider("Years to taper", 1, 30, 10, 1)
        else:
            late_spending = annual_spending
            taper_start_age = retirement_age
            taper_years = 1
        retirement_duration = st.slider("Years in retirement", 10, 50, 30, 1)

    with st.expander("🎯 Lump-sum goals & estate"):
        n_goals = st.slider("Number of lump-sum goals", 0, 3, 0, 1,
            help="One-off withdrawals (holidays, car, renovations). Today's $.")
        goals = []
        for i in range(n_goals):
            cols = st.columns(2)
            default_g_age = min(retirement_age + 5 + i * 5, 90)
            default_g_age = max(default_g_age, current_age + 1)
            with cols[0]:
                g_age = st.number_input(
                    f"Goal {i+1} age", current_age, 100, default_g_age, key=f"g_age_{i}"
                )
            with cols[1]:
                g_amt = st.number_input(
                    f"Goal {i+1} amount ($)", 0, 1000000, 20000, 5000, key=f"g_amt_{i}"
                )
            goals.append((g_age, g_amt))
        estate_target = st.number_input(
            "Estate target ($, today's $)", 0, 10000000, 0, 50000, format="%d",
            help="Reference line — desired wealth to leave to beneficiaries"
        )

    with st.expander("🏛️ Age Pension"):
        include_age_pension = st.checkbox("Include Age Pension", value=True)
        st.caption(
            f"Eligibility age: {PENSION_AGE}. "
            f"Max single ${MAX_PENSION_ANNUAL['single']:,} / couple ${MAX_PENSION_ANNUAL['couple']:,} p.a. "
            f"Rates as at Sep 2025."
        )

# ── CALCULATIONS ─────────────────────────────────────────────────────────────
g_dec = nominal_return_growth / 100
r_dec = nominal_return_retirement / 100
inf_dec = inflation / 100
fee_dec = fee_pct / 100

ages = []
your_balances, partner_balances, nonsuper_balances, total_balances = [], [], [], []
contributions_list = []
withdrawals_super, withdrawals_nonsuper = [], []
age_pension_list, goal_withdrawals, spending_list = [], [], []
phase_labels = []

your_bal = float(initial_balance)
partner_bal = float(partner_balance_input)
nonsuper_bal = float(non_super)
your_sal = float(current_salary)
p_sal = float(partner_salary)
your_sac = float(salary_sacrifice)
p_sac = float(partner_sacrifice)
your_nc = float(non_concessional)
p_nc = float(partner_nc)

# Phase 1: Growth
for age in range(current_age, retirement_age + 1):
    if age > current_age:
        your_sal *= (1 + inf_dec)
        p_sal *= (1 + inf_dec)
        your_sac *= (1 + inf_dec)
        p_sac *= (1 + inf_dec)
        your_nc *= (1 + inf_dec)
        p_nc *= (1 + inf_dec)

    your_emp = your_sal * 0.12 * 0.85
    your_total = your_emp + your_sac * 0.85 + your_nc
    your_bal = grow_pool(your_bal, your_total, g_dec, fee_dec, tax_on_profit=0.15)

    if is_couple:
        p_emp = p_sal * 0.12 * 0.85
        p_total = p_emp + p_sac * 0.85 + p_nc
        partner_bal = grow_pool(partner_bal, p_total, g_dec, fee_dec, tax_on_profit=0.15)
    else:
        p_total = 0

    nonsuper_bal = grow_pool(nonsuper_bal, 0, g_dec, fee_dec, tax_on_profit=0.0)
    your_bal = max(0, your_bal - fee_dollar)

    ages.append(age)
    your_balances.append(your_bal)
    partner_balances.append(partner_bal)
    nonsuper_balances.append(nonsuper_bal)
    total_balances.append(your_bal + partner_bal + nonsuper_bal)
    contributions_list.append(your_total + p_total)
    withdrawals_super.append(0)
    withdrawals_nonsuper.append(0)
    age_pension_list.append(0)
    goal_withdrawals.append(0)
    spending_list.append(0)
    phase_labels.append('Growth')

balance_at_retirement = your_bal + partner_bal + nonsuper_bal

# Phase 2: Drawdown
def desired_spend_today_dollars(age):
    if spending_strategy == "Constant":
        return annual_spending
    if age < taper_start_age:
        return annual_spending
    if age >= taper_start_age + taper_years:
        return late_spending
    pct = (age - taper_start_age) / taper_years
    return annual_spending + pct * (late_spending - annual_spending)

for year in range(retirement_duration):
    age = retirement_age + 1 + year
    p_age = (partner_age + (age - current_age)) if partner_age is not None else None
    years_from_now = age - current_age

    today_spend = desired_spend_today_dollars(age)
    nominal_spend = today_spend * (1 + inf_dec) ** years_from_now
    nominal_other_income = other_income_today * (1 + inf_dec) ** years_from_now

    goal_amt = sum(amt * (1 + inf_dec) ** (g_age - current_age)
                   for g_age, amt in goals if g_age == age)

    eligible = False
    if include_age_pension:
        if is_couple:
            yng_age = min(age, p_age) if p_age is not None else age
            eligible = yng_age >= PENSION_AGE
        else:
            eligible = age >= PENSION_AGE

    if eligible:
        financial_assets = your_bal + partner_bal + nonsuper_bal
        ap = calc_age_pension(
            financial_assets, other_assets, nominal_other_income,
            status, homeowner
        )
    else:
        ap = 0

    net_need = max(0, nominal_spend + goal_amt - ap - nominal_other_income)

    total_super = your_bal + partner_bal
    min_super_wd = total_super * min_drawdown_rate(age)
    super_wd = max(net_need, min_super_wd)
    super_wd = min(super_wd, total_super)

    if total_super > 0:
        share = your_bal / total_super
        your_bal = max(0, your_bal - super_wd * share)
        partner_bal = max(0, partner_bal - super_wd * (1 - share))

    remaining = max(0, net_need - super_wd)
    nonsuper_wd = min(remaining, nonsuper_bal)
    nonsuper_bal = max(0, nonsuper_bal - nonsuper_wd)

    your_bal = grow_pool(your_bal, 0, r_dec, fee_dec, tax_on_profit=0.0)
    partner_bal = grow_pool(partner_bal, 0, r_dec, fee_dec, tax_on_profit=0.0)
    nonsuper_bal = grow_pool(nonsuper_bal, 0, r_dec, fee_dec, tax_on_profit=0.0)
    your_bal = max(0, your_bal - fee_dollar)

    ages.append(age)
    your_balances.append(your_bal)
    partner_balances.append(partner_bal)
    nonsuper_balances.append(nonsuper_bal)
    total_balances.append(your_bal + partner_bal + nonsuper_bal)
    contributions_list.append(0)
    withdrawals_super.append(super_wd)
    withdrawals_nonsuper.append(nonsuper_wd)
    age_pension_list.append(ap)
    goal_withdrawals.append(goal_amt)
    spending_list.append(nominal_spend)
    phase_labels.append('Drawdown')

final_balance = total_balances[-1]
funds_depleted = final_balance == 0
depletion_age = next(
    (ages[i] for i, b in enumerate(total_balances)
     if b == 0 and phase_labels[i] == 'Drawdown'),
    None
)

df = pd.DataFrame({
    'Age': ages,
    'Phase': phase_labels,
    'Your_Super': your_balances,
    'Partner_Super': partner_balances,
    'Non_Super': nonsuper_balances,
    'Total_Wealth': total_balances,
    'Contributions': contributions_list,
    'Spending': spending_list,
    'Age_Pension': age_pension_list,
    'Super_Withdrawal': withdrawals_super,
    'NonSuper_Withdrawal': withdrawals_nonsuper,
    'Goal_Withdrawal': goal_withdrawals,
})

# ── CHARTS ───────────────────────────────────────────────────────────────────
tab_wealth, tab_income, tab_data = st.tabs(["📊 Wealth", "💵 Income sources", "📋 Data"])

with tab_wealth:
    fig = go.Figure()
    growth_df = df[df['Phase'] == 'Growth']
    drawdown_df = df[df['Phase'] == 'Drawdown']

    palettes = [
        ('Growth', growth_df, '#32CD32', '#228B22', '#4682B4'),
        ('Drawdown', drawdown_df, '#FFA500', '#FF8C00', '#CD853F'),
    ]
    for phase, df_phase, your_color, partner_color, nonsuper_color in palettes:
        if len(df_phase) == 0:
            continue
        fig.add_trace(go.Bar(
            x=df_phase['Age'], y=df_phase['Your_Super'],
            name=f"Your Super ({phase})",
            marker_color=your_color,
            hovertemplate='<b>Age %{x}</b><br>Your Super: $%{y:,.0f}<extra></extra>'
        ))
        if is_couple and df_phase['Partner_Super'].sum() > 0:
            fig.add_trace(go.Bar(
                x=df_phase['Age'], y=df_phase['Partner_Super'],
                name=f"Partner Super ({phase})",
                marker_color=partner_color,
                hovertemplate='<b>Age %{x}</b><br>Partner Super: $%{y:,.0f}<extra></extra>'
            ))
        if df_phase['Non_Super'].sum() > 0:
            fig.add_trace(go.Bar(
                x=df_phase['Age'], y=df_phase['Non_Super'],
                name=f"Non-Super ({phase})",
                marker_color=nonsuper_color,
                hovertemplate='<b>Age %{x}</b><br>Non-Super: $%{y:,.0f}<extra></extra>'
            ))

    fig.add_vline(x=retirement_age, line_dash="dash", line_color="white", line_width=2,
                  annotation_text="Retirement", annotation_position="top")

    for i, (g_age, _) in enumerate(goals):
        fig.add_vline(x=g_age, line_dash="dot", line_color="#FFD700", line_width=1,
                      annotation_text=f"Goal {i+1}",
                      annotation_position="bottom")

    if estate_target > 0:
        end_offset = ages[-1] - current_age
        nominal_estate = estate_target * (1 + inf_dec) ** end_offset
        fig.add_hline(
            y=nominal_estate, line_dash="dash", line_color="#FFFFFF", line_width=2,
            annotation_text=f"Estate target (${estate_target:,.0f} today)",
            annotation_position="right"
        )

    fig.update_layout(
        barmode='stack',
        title={
            'text': (
                f"Wealth: Growth → Drawdown<br>"
                f"<sub>Retire at {retirement_age} with ${balance_at_retirement:,.0f}  |  "
                f"Returns: {nominal_return_growth:.1f}% / {nominal_return_retirement:.1f}%  |  "
                f"Inflation: {inflation:.1f}%  |  Fees: {fee_pct:.1f}%</sub>"
            ),
            'x': 0.5, 'xanchor': 'center', 'font': {'size': 18, 'color': '#E0E0E0'}
        },
        xaxis_title="Age", yaxis_title="Wealth ($)",
        hovermode='x unified',
        plot_bgcolor='#1C1C2E', paper_bgcolor='#1C1C2E',
        font=dict(color='#E0E0E0', size=12),
        height=620,
        legend=dict(
            orientation="v", yanchor="top", y=0.98, xanchor="left", x=0.01,
            bgcolor='rgba(28, 28, 46, 0.9)', bordercolor='#32CD32', borderwidth=1,
            font=dict(size=10, color='#E0E0E0')
        ),
        xaxis=dict(gridcolor='#6B6B8B', dtick=5),
        yaxis=dict(gridcolor='#6B6B8B', tickformat='$,.0f'),
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_income:
    fig2 = go.Figure()
    dd = df[df['Phase'] == 'Drawdown']
    if len(dd) > 0:
        fig2.add_trace(go.Bar(
            x=dd['Age'], y=dd['Age_Pension'],
            name="Age Pension", marker_color='#9370DB',
            hovertemplate='<b>Age %{x}</b><br>Age Pension: $%{y:,.0f}<extra></extra>'
        ))
        fig2.add_trace(go.Bar(
            x=dd['Age'], y=dd['Super_Withdrawal'],
            name="Super Withdrawal", marker_color='#FFA500',
            hovertemplate='<b>Age %{x}</b><br>Super: $%{y:,.0f}<extra></extra>'
        ))
        if dd['NonSuper_Withdrawal'].sum() > 0:
            fig2.add_trace(go.Bar(
                x=dd['Age'], y=dd['NonSuper_Withdrawal'],
                name="Non-Super Withdrawal", marker_color='#4682B4',
                hovertemplate='<b>Age %{x}</b><br>Non-Super: $%{y:,.0f}<extra></extra>'
            ))
        if dd['Goal_Withdrawal'].sum() > 0:
            fig2.add_trace(go.Bar(
                x=dd['Age'], y=dd['Goal_Withdrawal'],
                name="Lump-sum goals", marker_color='#FF6347',
                hovertemplate='<b>Age %{x}</b><br>Goal: $%{y:,.0f}<extra></extra>'
            ))
        fig2.add_trace(go.Scatter(
            x=dd['Age'], y=dd['Spending'],
            name="Desired spending", mode='lines',
            line=dict(color='#FFFFFF', width=2, dash='dash'),
            hovertemplate='<b>Age %{x}</b><br>Spending: $%{y:,.0f}<extra></extra>'
        ))

    fig2.update_layout(
        barmode='stack',
        title={
            'text': "Income sources in retirement (nominal $)",
            'x': 0.5, 'xanchor': 'center', 'font': {'size': 18, 'color': '#E0E0E0'}
        },
        xaxis_title="Age", yaxis_title="Annual income ($)",
        hovermode='x unified',
        plot_bgcolor='#1C1C2E', paper_bgcolor='#1C1C2E',
        font=dict(color='#E0E0E0'),
        height=520,
        legend=dict(
            orientation="v", yanchor="top", y=0.98, xanchor="left", x=0.01,
            bgcolor='rgba(28, 28, 46, 0.9)', bordercolor='#32CD32', borderwidth=1,
            font=dict(size=10, color='#E0E0E0')
        ),
        xaxis=dict(gridcolor='#6B6B8B'),
        yaxis=dict(gridcolor='#6B6B8B', tickformat='$,.0f'),
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab_data:
    st.dataframe(
        df.style.format({
            'Your_Super': '${:,.0f}', 'Partner_Super': '${:,.0f}',
            'Non_Super': '${:,.0f}', 'Total_Wealth': '${:,.0f}',
            'Contributions': '${:,.0f}', 'Spending': '${:,.0f}',
            'Age_Pension': '${:,.0f}', 'Super_Withdrawal': '${:,.0f}',
            'NonSuper_Withdrawal': '${:,.0f}', 'Goal_Withdrawal': '${:,.0f}',
        }),
        use_container_width=True,
        height=500,
    )

# ── SUMMARY METRICS ──────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Balance at Retirement", f"${balance_at_retirement:,.0f}")
with col2:
    st.metric("Peak Wealth", f"${max(total_balances):,.0f}")
with col3:
    st.metric("Final Balance", f"${final_balance:,.0f}")
with col4:
    if funds_depleted:
        st.metric("⚠️ Status", f"Depleted at {depletion_age}")
    else:
        st.metric("✅ Status", "Funds Last")

total_ap = sum(age_pension_list)
years_with_ap = sum(1 for a in age_pension_list if a > 0)
if include_age_pension and total_ap > 0:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Years on Age Pension", f"{years_with_ap}")
    with col2:
        st.metric("Total Age Pension received", f"${total_ap:,.0f}")
    with col3:
        avg_ap = total_ap / years_with_ap if years_with_ap > 0 else 0
        st.metric("Avg Age Pension / yr", f"${avg_ap:,.0f}")

# ── STATUS MESSAGE ───────────────────────────────────────────────────────────
if funds_depleted:
    st.error(
        f"⚠️ **Funds depleted at age {depletion_age}** — consider working longer, "
        f"reducing spending, or relying more on Age Pension"
    )
else:
    st.success(
        f"✅ **Funds last full retirement** — ${final_balance:,.0f} remaining at age {ages[-1]}"
    )

if estate_target > 0:
    end_offset = ages[-1] - current_age
    nominal_estate = estate_target * (1 + inf_dec) ** end_offset
    if final_balance >= nominal_estate:
        st.info(
            f"🎁 **Estate target met** — ${final_balance:,.0f} ≥ "
            f"${nominal_estate:,.0f} (${estate_target:,.0f} in today's $)"
        )
    else:
        st.warning(
            f"🎁 **Estate target not met** — ${final_balance:,.0f} < "
            f"${nominal_estate:,.0f} (${estate_target:,.0f} in today's $)"
        )

# ── DOWNLOAD CSV ─────────────────────────────────────────────────────────────
st.markdown("---")
csv = df.to_csv(index=False)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
st.download_button(
    label="📥 Download Detailed CSV",
    data=csv,
    file_name=f"retirement_projections_{timestamp}.csv",
    mime="text/csv",
    help="Download full year-by-year breakdown"
)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 12px;'>
    <p>Retirement Projections Calculator | Bamboo Trading</p>
    <p>Assumptions: 12% SG | 15% tax (accumulation) / 0% tax (pension) |
       Age Pension rates as at Sep 2025 (indexed Mar/Sep) |
       Non-super assumed tax-free in growth (franking offset simplification)</p>
    <p>Projections are illustrative only. Actual results depend on market returns,
       tax law changes, and personal circumstances.</p>
</div>
""", unsafe_allow_html=True)
