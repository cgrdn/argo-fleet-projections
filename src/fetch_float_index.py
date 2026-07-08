
import pandas as pd
import argopy

# load all meds floats
idx = argopy.ArgoIndex()
meds = idx.query.dac('meds').to_dataframe()
# subset for active floats
now = pd.Timestamp('now')
ix = meds.loc[meds.date > pd.Timestamp('2025-06-01')]

# create a new dataframe with unique floats as index
df = pd.DataFrame(
    {
        'WMO':ix.wmo.unique(),
        'Deployment Date':[meds.loc[meds.wmo == wmo, 'date'].min() for wmo in ix.wmo.unique()],
        'Last Date':[meds.loc[meds.wmo == wmo, 'date'].max() for wmo in ix.wmo.unique()],
        'Model':[ix.loc[ix.wmo == wmo, 'profiler'].iloc[0] for wmo in ix.wmo.unique()],
        'Last Cycle':[ix.loc[ix.wmo == wmo, 'date'].max() for wmo in ix.wmo.unique()],
        'Mean Latitude':[ix.loc[ix.wmo == wmo, 'latitude'].mean() for wmo in ix.wmo.unique()],
        'Mean Longitude':[ix.loc[ix.wmo == wmo, 'longitude'].mean() for wmo in ix.wmo.unique()],
    }
)

df.to_csv('../data/meds_active_floats.csv', index=False)