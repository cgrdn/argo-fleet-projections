
from collections.abc import Iterable

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme(context='paper', style='ticks')

# -----------------------------------------------------------------------------
# project procurement by float type, scenario, year
# -----------------------------------------------------------------------------

# load finance information
resources = pd.read_csv('../data/financial_scenarios.csv').set_index('Scenario')
costs = pd.read_csv('../data/float_costs_2026.csv').set_index('Float')

# cost increase per year
inflation_rate = 5 # percent / year

# study time period
now = pd.Timestamp('now')
years = np.arange(now.year+1, now.year+6)

# slice together finance info and cost increase to project float cost
projection = pd.DataFrame({'Year':years}).set_index('Year')
for f in costs.index:
    projection[f] = costs.loc[f].item() * (1 + inflation_rate/100) ** np.arange(0, years.shape[0])

# floats on the shelf
existing_stock = {'Core': 28, 'BGC':10, 'Polar':4, 'Deep':1}
# define max age in years for each flaot type
max_age = {'Core':5,'BGC':4.5,'Deep':3.5,'Polar':2.5}

# estimate procurement based on scenario and float cost
procurement = pd.Series(0, index=pd.MultiIndex.from_product([resources.columns, resources.index, years], names=['Float', 'Scenario', 'Year']))
# procured floats that will die
attrition = pd.Series(0, index=procurement.index)

for f, s, y in procurement.index:
    existing_floats = existing_stock[f] if y == 2027 and s != 'In Water' else 0
    procurement.loc[(f, s, y)] = np.floor(resources.loc[s, f] / projection.loc[y, f] + existing_floats)
    if y - years[0] > max_age[f]:
        attrition.loc[(f, s, y)] = procurement.loc[(f, s, years[y - years > max_age[f]])].sum() - attrition.loc[(f, s, years[years < y])].sum()

# -----------------------------------------------------------------------------
# project our number of active floats over next years
# -----------------------------------------------------------------------------

# load active floats
df = pd.read_csv('../data/meds_active_floats.csv')
df['Deployment Date'] = df['Deployment Date'].apply(pd.Timestamp)

# calculate float age
now = pd.Timestamp('now')
df['Active Float Age (Years)'] = [(now - deploy).days/365 for deploy in df['Deployment Date']]

# count number of floats under a certain age
def age_count(df, date, max_age=5):
    age = pd.Series([date - deploy for deploy in df['Deployment Date']])
    max_age = pd.Series([pd.Timedelta(days=365*a) for a in max_age]) if isinstance(max_age, Iterable) else pd.Timedelta(days=365*max_age)

    return (age < max_age).sum()

# classify floats into procurement categories
network = {'NOVA':'Core', 'ARVOR':'Core', 'Teledyne':'Core', 'PROVOR':'BGC', 'ARVOR-D':'Deep'}
df['Network'] = [network[m.split(' ')[0]] for m in df['Model']]
# polar if above/below 60/-60 deg latitude
df.loc[df['Mean Latitude'].abs() > 60, 'Network'] = 'Polar'
# map max age for each float to dataframe
df['Max Age'] = [max_age[n] for n in df.Network]

active_floats = pd.Series(index=pd.MultiIndex.from_product([resources.columns, years], names=['Float', 'Year']))
for f, y in active_floats.index:
    active_floats.loc[(f, y)] = age_count(df.loc[df['Network'] == f], pd.Timestamp(f'{y}-01-01'), max_age=max_age[f])

# project out by float type
project = pd.concat(resources.index.shape[0]*[active_floats], keys=resources.index)
project.index.reorder_levels(procurement.index.names)
project = project.add(procurement.groupby(['Float', 'Scenario']).cumsum()).subtract(attrition.groupby(['Float', 'Scenario']).cumsum())
project = project.reset_index(name='Active Floats')

# -----------------------------------------------------------------------------
# Plot Scenarios
# -----------------------------------------------------------------------------

fig, axes = plt.subplots(1, 2)
sns.histplot(df['Active Float Age (Years)'], bins=range(10), ax=axes[0])
axes[0].set_title(f'{df.shape[0]} Active Floats', loc='left')
axes[0].set_xticks(range(10))
deployment_years = [d.year + 0.5 for d in df['Deployment Date']]
bins = np.arange(2017, 2028)
sns.histplot(deployment_years, bins=bins, ax=axes[1])
axes[1].set_xticks(bins[::2])
axes[1].set_xticks(bins[1::2], minor=True)
axes[1].set_xlabel('Deployment Date')
fig.set_size_inches(8, 4)
fig.savefig(f'../figures/existing_fleet_age_hist.png', dpi=300, bbox_inches='tight')

scenarios = []
for s in resources.index:
    scenarios.append(s)

    fig, ax = plt.subplots()
    sns.lineplot(
        data=project.loc[project['Scenario'].isin(scenarios)].groupby(['Scenario', 'Year']).sum(), 
        x='Year', y='Active Floats', hue='Scenario', 
        hue_order=resources.index,
        marker='o', markersize=8,
        palette='colorblind', ax=ax
    )

    ax.set_title('Argo Canada Fleet Projections', loc='left')
    ax.set_xticks(years)
    ax.set_ylim(-10, 610)
    ax.legend(loc=2)

    fig.set_size_inches(4, 4)
    fig.savefig(f'../figures/total_floats_{s.lower().replace(' ', '_')}.png', dpi=300, bbox_inches='tight')

g = sns.relplot(
    data=project, col='Float', x='Year', y='Active Floats', hue='Scenario', 
    hue_order=resources.index, col_order=resources.columns, col_wrap=2, 
    marker='o', markersize=8, palette='colorblind',
    kind='line', estimator=None, height=3.5, facet_kws=dict(despine=False)
)
g.set_titles(col_template='')
g.set_titles(col_template='{col_name}', loc='left')
g.axes[0].set_xticks(years)
g.figure.savefig(f'../figures/float_type_scenarios.png', dpi=300, bbox_inches='tight')

plt.close('all')