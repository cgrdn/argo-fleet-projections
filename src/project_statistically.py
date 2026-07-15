
import numpy as np
import pandas as pd

def p_failure(age, median, c=0):
    k = 1 # steepness of the curve
    p = 1 / (1 + np.exp(-k * (age - median))) + c
    
    return p

def deploy_floats(df, n_floats, date, type):

    new_data = {
        'Deployment Date':[date for i in range(n_floats)],
        'Networks':[type for i in range(n_floats)]
    }
    new_deployments = pd.DataFrame(new_data, columns=df.columns)

    return pd.concat(df, new_deployments, ignore_index=True)

def kill_floats(df):

    now = pd.Timestamp('now')
    # define max age in years for each flaot type
    median_death = {'Core':5,'BGC':4.5,'Deep':3.5,'Polar':2.5}
    survive = [np.random.rand() > p_failure((now - row['Deployment Date']).days/365, median_death[row['Network']]) for _,row in df.iterrows()]

    return df.loc[survive]

# load active floats
df = pd.read_csv('../data/meds_active_floats.csv')
df['Deployment Date'] = df['Deployment Date'].apply(pd.Timestamp)
# classify floats into procurement categories
network = {'NOVA':'Core', 'ARVOR':'Core', 'Teledyne':'Core', 'PROVOR':'BGC', 'ARVOR-D':'Deep'}
df['Network'] = [network[m.split(' ')[0]] for m in df['Model']]
# polar if above/below 60/-60 deg latitude
df.loc[df['Mean Latitude'].abs() > 60, 'Network'] = 'Polar'

# load procurement for each scenario
procurement = pd.read_csv('../data/procurement.csv').set_index(['Float', 'Scenario', 'Year']).squeeze()

