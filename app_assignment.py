# ─────────────────────────────────────────────────────────────────────────────
# Week 11 Demo — Spending Dashboard
# app_demo.py
# 
# ─────────────────────────────────────────────────────────────────────────────

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


# ── Load data ─────────────────────────────────────────────────────────────────
# @st.cache_data loads the files once and reuses them on every rerun.

@st.cache_data
def load_data():
    transactions = pd.read_csv('data/transactions.csv', parse_dates=['date'])
    categories   = pd.read_csv('data/categories.csv')
    merchants    = pd.read_csv('data/merchants.csv')

    #Join category names — same left join pattern from Week 8.
    df = pd.merge(transactions, categories, on='category_id', how='left')
    df = pd.merge(df, merchants, on='merchant_id', how='left')
    return df



df = load_data()


# ── Filter to expenses only ───────────────────────────────────────────────────
# The dashboard focuses on spending, so we filter to Expense rows up front.
# Amounts are stored as negative values — .abs() converts them to positive.

expenses = df[df['transaction_type'] == 'Expense'].copy()
expenses['amount'] = expenses['amount'].abs()


# ── Page title ────────────────────────────────────────────────────────────────
st.title('Spending Dashboard')
st.sidebar.header('Filters')

all_categories = sorted(expenses['category_name'].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    'Category',
    options=all_categories,
    default=all_categories
)

years = sorted(expenses['date'].dt.year.unique().tolist())
selected_year = st.sidebar.selectbox(
    'Year', years
)
# Guard: if the user deselects everything, show a warning and stop.
if not selected_categories:
    st.warning('Please select at least one category.')
    st.stop()


# ── Filter by selected categories ────────────────────────────────────────────
filtered = expenses[expenses['category_name'].isin(selected_categories) 
                    & (expenses['date'].dt.year == selected_year)]

st.subheader(f'Analysis by Hannah Hodek — {selected_year}')
st.write('Total expense transactions:', len(filtered))


# ── Sidebar filter ────────────────────────────────────────────────────────────
# st.multiselect returns a list of the selected values.
# default=all_categories means everything is selected when the app first loads.


# ── Raw data table ────────────────────────────────────────────────────────────
st.header('Transactions')
st.dataframe(filtered)


# ── Summary table ─────────────────────────────────────────────────────────────
summary = (
    filtered
    .groupby('category_name')['amount']
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

st.header('Spending by Category')
st.dataframe(summary)


# ── Stacked bar chart: monthly spending by category ───────────────────────────
# resample('ME') groups rows into monthly buckets — the time series pattern
# from Week 9. pivot() reshapes the result so each category is its own column,
# which is exactly what a stacked bar chart needs.

st.header('Monthly Spending by Category')

monthly = (
    filtered
    .groupby([pd.Grouper(key='date', freq='ME'), 'category_name'])['amount']
    .sum()
    .reset_index()
)

monthly_pivot = monthly.pivot(
    index='date',
    columns='category_name',
    values='amount'
).fillna(0)

# Convert the index to datetime first, then format clean month labels
# (e.g. "Jan 2022") to satisfy static type checking.
monthly_pivot.index = pd.to_datetime(monthly_pivot.index).strftime('%b %Y')

fig, ax = plt.subplots(figsize=(12, 5))
monthly_pivot.plot(kind='bar', stacked=True, ax=ax, colormap='tab10', width=0.8)

ax.set_title('Monthly Spending by Category')
ax.set_xlabel('')
ax.set_ylabel('Total Spending ($)')
ax.legend(title='Category', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=8)

# Rotate x-axis labels so month names don't overlap
plt.xticks(rotation=45, ha='right', fontsize=7)
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)

#Merchant Summary table
merchant_summary = (
   filtered
   .groupby('merchant_name')['amount']
   .sum()
   .sort_values(ascending=False)
   .reset_index()
)

st.header('Spending by Merchant')

fig, ax = plt.subplots(figsize=(8, max(4, len(merchant_summary) * 0.3)))

sns.barplot(data=merchant_summary, x='amount', y='merchant_name', ax=ax)
ax.set_title('Spending by Merchant')
ax.set_xlabel('Total ($)')
ax.set_ylabel('')
plt.tight_layout()
st.pyplot(fig)
plt.close(fig)