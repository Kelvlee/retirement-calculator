"""
Retirement Projections Calculator - Interactive Web Version
Streamlit app with Plotly charts for bambootrading.com.au
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import numpy as np

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retirement Calculator | Bamboo Trading",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main {background-color: #1C1C2E;}
    h1 {color: #32CD32 !important; font-size: clamp(1.4rem, 5vw, 2.2rem) !important;}
    h2, h3 {color: #E0E0E0 !important;}
    .stSlider > div > div > div {background-color: #32CD32;}
    [data-testid="stMetricValue"] {font-size: clamp(18px, 4vw, 28px); color: #32CD32;}
    [data-testid="stMetricLabel"] {color: #E0E0E0; font-size: clamp(11px, 3vw, 14px);}
    .stDownloadButton > button {
        background-color: #32CD32;
        color: white;
        font-weight: bold;
        width: 100%;
        padding: 0.6rem 1rem;
    }
    /* Sidebar inputs: larger touch targets on mobile */
    .stSlider, .stNumberInput {margin-bottom: 0.75rem;}
    /* Stack 4-column metrics to 2x2 on small screens */
    @media (max-width: 640px) {
        [data-testid="column"] {
            width: 50% !important;
            flex: 0 0 50% !important;
            min-width: 50% !important;
        }
        [data-testid="stMetricValue"] {font-size: 16px;}
        [data-testid="stMetricLabel"] {font-size: 11px;}
        h1 {font-size: 1.4rem !important;}
        /* Full-width download button */
        .stDownloadButton {width: 100%;}
    }
</style>
""", unsafe_allow_html=True)

# ── TITLE ────────────────────────────────────────────────────────────────────
st.title("🎯 Retirement Projections Calculator")
st.markdown("*Adjust sliders to see real-time retirement projections (Growth + Drawdown)*")
st.markdown("""
<div style='background:#2A2A3E; border-left:3px solid #32CD32; padding:8px 12px; border-radius:4px; font-size:13px; color:#B0B0C0; margin-bottom:8px;'>
📱 <b>Mobile:</b> Tap <b>☰</b> (top-left) to open inputs &nbsp;|&nbsp; 🖥️ <b>Desktop:</b> Use the left sidebar
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── SIDEBAR INPUTS ───────────────────────────────────────────────────────────
with st.sidebar:
    st.header("📊 Input Parameters")

    # Growth Phase
    st.subheader("🌱 Growth Phase")
    current_age = st.slider("Current Age", 18, 100, 50, 1)
    retirement_age = st.slider("Retirement Age", max(current_age + 1, 50), 100, 65, 1)
    initial_balance = st.number_input(
        "Initial Super Balance ($)",
        min_value=0, max_value=10000000, value=200000, step=10000,
        format="%d"
    )
    current_salary = st.number_input(
        "Current Salary ($)",
        min_value=0, max_value=1000000, value=100000, step=5000,
        format="%d"
    )

    st.subheader("💰 Contributions")
    salary_sacrifice = st.number_input(
        "Salary Sacrifice ($/year)",
        min_value=0, max_value=100000, value=0, step=1000,
        format="%d"
    )
    non_concessional = st.number_input(
        "Non-Concessional ($/year)",
        min_value=0, max_value=200000, value=0, step=5000,
        format="%d"
    )

    st.subheader("📈 Assumptions")
    nominal_return_growth = st.slider("Nominal Return - Growth Phase (%)", 0.0, 30.0, 7.0, 0.5)
    nominal_return_retirement = st.slider("Nominal Return - Retirement Phase (%)", 0.0, 30.0, 5.0, 0.5)
    inflation = st.slider("Inflation (%)", 0.0, 10.0, 3.0, 0.5)

    st.subheader("🏖️ Drawdown Phase")
    annual_spending = st.number_input(
        "Annual Spending in Retirement ($)",
        min_value=0, max_value=500000, value=132000, step=5000,
        format="%d"
    )
    retirement_duration = st.slider("Years in Retirement", 10, 80, 20, 1)

# ── MIN DRAWDOWN RATES ───────────────────────────────────────────────────────
def min_drawdown_rate(age):
    if age < 65:   return 0.04
    elif age <= 74: return 0.05
    elif age <= 79: return 0.06
    elif age <= 84: return 0.07
    elif age <= 89: return 0.09
    elif age <= 94: return 0.11
    else:           return 0.14

# ── CALCULATIONS ─────────────────────────────────────────────────────────────
# Convert percentages
nominal_return_growth_decimal = nominal_return_growth / 100
nominal_return_retirement_decimal = nominal_return_retirement / 100
inflation_decimal = inflation / 100

# Initialize arrays
ages = []
balances = []
contributions_list = []
withdrawals_list = []
withdrawals_spending_list = []
withdrawals_minimum_list = []
phase_labels = []
employer_contribs = []
sacrifice_contribs = []
nonconc_contribs = []

# Phase 1: Growth
balance = initial_balance
current_sal = current_salary
current_sac = salary_sacrifice
current_nc = non_concessional

for age in range(current_age, retirement_age + 1):
    # Grow salary and contributions by inflation (except first year)
    if age > current_age:
        current_sal *= (1 + inflation_decimal)
        current_sac *= (1 + inflation_decimal)
        current_nc *= (1 + inflation_decimal)

    # Calculate contributions (15% tax on concessional)
    employer = current_sal * 0.12 * 0.85  # SG 12%, after 15% tax
    sacrifice = current_sac * 0.85  # After 15% tax
    total_contrib = employer + sacrifice + current_nc

    # Calculate profit and tax (15% on profits in accumulation)
    profit = balance * nominal_return_growth_decimal
    tax = profit * 0.15
    net_profit = profit - tax

    # Update balance
    balance = balance + net_profit + total_contrib

    # Store data
    ages.append(age)
    balances.append(balance)
    contributions_list.append(total_contrib)
    withdrawals_list.append(0)
    withdrawals_spending_list.append(0)
    withdrawals_minimum_list.append(0)
    phase_labels.append('Growth')
    employer_contribs.append(employer)
    sacrifice_contribs.append(sacrifice)
    nonconc_contribs.append(current_nc)

balance_at_retirement = balance

# Phase 2: Drawdown
first_withdrawal = annual_spending * (1 + inflation_decimal) ** (retirement_age - current_age)
withdrawal = first_withdrawal

for year in range(retirement_duration):
    age = retirement_age + 1 + year

    # Minimum drawdown: mandatory floor based on age (applied to opening balance)
    min_rate = min_drawdown_rate(age)
    w_minimum = balance * min_rate

    # Total withdrawal = max of desired spending or mandatory minimum
    total_withdrawal = max(withdrawal, w_minimum)

    # Split for chart: minimum is the floor, spending is the excess above it
    chart_minimum = w_minimum
    chart_spending = total_withdrawal - w_minimum  # 0 if spending < minimum

    # Apply return then subtract withdrawal (no tax in pension phase)
    closing = balance * (1 + nominal_return_retirement_decimal) - total_withdrawal
    closing = max(closing, 0)

    # Store data
    ages.append(age)
    balances.append(closing)
    contributions_list.append(0)
    withdrawals_list.append(total_withdrawal)
    withdrawals_spending_list.append(chart_spending)
    withdrawals_minimum_list.append(chart_minimum)
    phase_labels.append('Drawdown')
    employer_contribs.append(0)
    sacrifice_contribs.append(0)
    nonconc_contribs.append(0)

    balance = closing
    withdrawal *= (1 + inflation_decimal)

final_balance = balances[-1]
funds_depleted = final_balance == 0
depletion_age = None
if funds_depleted:
    for i, bal in enumerate(balances):
        if bal == 0:
            depletion_age = ages[i]
            break

# Create DataFrame
df = pd.DataFrame({
    'Age': ages,
    'Balance': balances,
    'Contributions': contributions_list,
    'Withdrawals': withdrawals_list,
    'Withdrawals_Spending': withdrawals_spending_list,
    'Withdrawals_Minimum': withdrawals_minimum_list,
    'Phase': phase_labels,
    'Employer_SG': employer_contribs,
    'Salary_Sacrifice': sacrifice_contribs,
    'Non_Concessional': nonconc_contribs
})

# ── PLOTLY CHART ─────────────────────────────────────────────────────────────
fig = go.Figure()

# Separate growth and drawdown data
growth_df = df[df['Phase'] == 'Growth']
drawdown_df = df[df['Phase'] == 'Drawdown']

# Growth phase - Super Balance (green)
fig.add_trace(go.Bar(
    x=growth_df['Age'],
    y=growth_df['Balance'],
    name="Super Balance (Growth)",
    marker_color='#32CD32',
    hovertemplate='<b>Age %{x}</b><br>Balance: $%{y:,.0f}<extra></extra>'
))

# Growth phase - Employer contributions (stacked on top)
if growth_df['Employer_SG'].sum() > 0:
    fig.add_trace(go.Bar(
        x=growth_df['Age'],
        y=growth_df['Employer_SG'],
        name="Employer SG (12%)",
        marker_color='#4682B4',
        base=growth_df['Balance'],
        hovertemplate='<b>Age %{x}</b><br>Employer: $%{y:,.0f}<extra></extra>'
    ))

# Growth phase - Salary Sacrifice (stacked)
if growth_df['Salary_Sacrifice'].sum() > 0:
    fig.add_trace(go.Bar(
        x=growth_df['Age'],
        y=growth_df['Salary_Sacrifice'],
        name="Salary Sacrifice",
        marker_color='#FFD700',
        base=growth_df['Balance'] + growth_df['Employer_SG'],
        hovertemplate='<b>Age %{x}</b><br>Sacrifice: $%{y:,.0f}<extra></extra>'
    ))

# Growth phase - Non-Concessional (stacked)
if growth_df['Non_Concessional'].sum() > 0:
    fig.add_trace(go.Bar(
        x=growth_df['Age'],
        y=growth_df['Non_Concessional'],
        name="Non-Concessional",
        marker_color='#FF6347',
        base=growth_df['Balance'] + growth_df['Employer_SG'] + growth_df['Salary_Sacrifice'],
        hovertemplate='<b>Age %{x}</b><br>Non-Concessional: $%{y:,.0f}<extra></extra>'
    ))

# Drawdown phase - Balance (yellow/gold)
if len(drawdown_df) > 0:
    fig.add_trace(go.Bar(
        x=drawdown_df['Age'],
        y=drawdown_df['Balance'],
        name="Super Balance (Drawdown)",
        marker_color='#FFA500',
        hovertemplate='<b>Age %{x}</b><br>Balance: $%{y:,.0f}<extra></extra>'
    ))

    # Drawdown phase - Minimum withdrawal (mandatory floor, stacked first)
    fig.add_trace(go.Bar(
        x=drawdown_df['Age'],
        y=drawdown_df['Withdrawals_Minimum'],
        name="Annual Withdrawal - Minimum",
        marker_color='#FF8C00',
        base=drawdown_df['Balance'],
        hovertemplate='<b>Age %{x}</b><br>Minimum: $%{y:,.0f}<extra></extra>'
    ))

    # Drawdown phase - Spending withdrawal (excess above minimum)
    fig.add_trace(go.Bar(
        x=drawdown_df['Age'],
        y=drawdown_df['Withdrawals_Spending'],
        name="Annual Withdrawal - Spending",
        marker_color='#CC7000',
        base=drawdown_df['Balance'] + drawdown_df['Withdrawals_Minimum'],
        hovertemplate='<b>Age %{x}</b><br>Spending: $%{y:,.0f}<extra></extra>'
    ))

# Add vertical line at retirement
fig.add_vline(
    x=retirement_age,
    line_dash="dash",
    line_color="white",
    line_width=2,
    annotation_text="Retirement",
    annotation_position="top"
)

# Layout styling
fig.update_layout(
    barmode='stack',
    title={
        'text': f"Retirement Projection: Growth → Drawdown<br><sub>Retire at {retirement_age}  |  Balance: ${balance_at_retirement:,.0f}  |  Inflation: {inflation:.1f}%</sub>",
        'x': 0.5,
        'xanchor': 'center',
        'font': {'size': 20, 'color': '#E0E0E0'}
    },
    xaxis_title="Age",
    yaxis_title="Portfolio Value ($)",
    hovermode='x unified',
    plot_bgcolor='#1C1C2E',
    paper_bgcolor='#1C1C2E',
    font=dict(color='#E0E0E0', size=12),
    height=550,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=-0.35,
        xanchor="center",
        x=0.5,
        bgcolor='rgba(28, 28, 46, 0.95)',
        bordercolor='#32CD32',
        borderwidth=1,
        font=dict(size=10, color='#E0E0E0'),
        tracegroupgap=4
    ),
    margin=dict(b=160),
    xaxis=dict(
        gridcolor='#6B6B8B',
        gridwidth=0.5,
        dtick=10,
        tickfont=dict(size=11)
    ),
    yaxis=dict(
        gridcolor='#6B6B8B',
        gridwidth=0.5
    )
)

# Display chart
st.plotly_chart(fig, use_container_width=True)

# ── SUMMARY METRICS ──────────────────────────────────────────────────────────
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Balance at Retirement", f"${balance_at_retirement:,.0f}")

with col2:
    st.metric("Peak Balance", f"${max(balances):,.0f}")

with col3:
    st.metric("Final Balance", f"${final_balance:,.0f}")

with col4:
    if funds_depleted:
        st.metric("⚠️ Status", f"Depleted at {depletion_age}")
    else:
        st.metric("✅ Status", "Funds Last")

# ── STATUS MESSAGE ───────────────────────────────────────────────────────────
if funds_depleted:
    st.error(f"⚠️ **Funds Depleted at Age {depletion_age}** - Consider adjusting spending or working longer")
else:
    st.success(f"✅ **Funds Last Full Retirement** - ${final_balance:,.0f} remaining at age {ages[-1]}")

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
    <p>Assumptions: 12% SG, 15% tax on contributions & profits (accumulation phase), 0% tax (pension phase)</p>
</div>
""", unsafe_allow_html=True)
