import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine
import random
from datetime import datetime, timedelta
import configparser
import os
import matplotlib.pyplot as plt
import scipy as sp

def sample_sizing(history_var, mde, alpha=0.05, power=0.8):
    z_alpha = sp.stats.norm.ppf(1-alpha/2)
    z_beta = sp.stats.norm.ppf(power)
    n = 2*history_var*((z_alpha+z_beta)**2)/(mde**2)
    return n

# Size of sample for ARPU
def arpu_sample_sizing(df_events_by_user_group_month):
    # We use all users who 'viewed'
    user_monthly_revenue = df_events_by_user_group_month.groupby(['month', 'user_id'])['total_revenue'].sum()
    user_monthly_revenue = user_monthly_revenue.reset_index()
    print(user_monthly_revenue.head())
    
    monthly_revenue_stats = user_monthly_revenue.groupby('month')['total_revenue'].agg(['mean', 'var'])
    history_revenue_var = monthly_revenue_stats['var'].mean()
    history_revenue_mean = monthly_revenue_stats['mean'].mean()
    print(f"History mean revenue {history_revenue_mean:.4}")
    print(f"Variance of history revenue {history_revenue_var:.8}")
    rel_revenue_mde = 0.1
    revenue_mde = rel_revenue_mde*history_revenue_mean
    print(f"Absolut MDE for revenue {revenue_mde:.8}")
    rev_sampling_size = int(sample_sizing(history_revenue_var, revenue_mde))
    print(f"Expected {rev_sampling_size} users for ARPU")
    return [history_revenue_mean, history_revenue_var, revenue_mde, rev_sampling_size]

def cr_sample_sizing(monthly_cr):
    monthly_cr['var'] = monthly_cr['cr']*(1 - monthly_cr['cr'])
    history_cr_var = monthly_cr['var'].mean()
    history_cr_mean = monthly_cr['cr'].mean()
    print(f"History mean CR {history_cr_mean:.2}")
    print(f"Variance of history CR {history_cr_var:.4}")
    rel_cr_mde = 0.05 # relevant CR mde
    cr_mde = rel_cr_mde*history_cr_mean
    print(f"Absolut MDE for cr {cr_mde:.2}")
    cr_sampling_size = int(sample_sizing(history_cr_var, cr_mde))
    print(f"Expected {cr_sampling_size} users for CR")
    return [history_cr_mean, history_cr_var, cr_mde, cr_sampling_size]

if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("config.ini")

    #  DB Connection parameters
    connection_string = (
        f"mssql+pyodbc://{config['DB PARAMS']['USERNAME']}:{config['DB PARAMS']['PASSWORT']}@{config['DB PARAMS']['SERVER']}/{config['DB PARAMS']['DATABASE']}"
        f"?driver={config['DB PARAMS']['DRIVER']}"
    )
    engine = create_engine(connection_string, fast_executemany=True)
    
    # Load data
    sql_str_for_events = "SELECT * FROM [dbo].[EventsByUserGroupMonth]"
    df_events_by_user_group_month = pd.read_sql(sql_str_for_events, con=engine)

    last_history_month = int(datetime.strptime(config['DATA']['HISTORY_END_DATE'], "%d-%m-%Y").month)
    
    df_events_by_user_group_month = df_events_by_user_group_month[df_events_by_user_group_month['month'].
                                                                  between(last_history_month-2, last_history_month)].copy()
    arpu_stat = arpu_sample_sizing(df_events_by_user_group_month)


    # Number of users for CR1 
    monthly_cr = df_events_by_user_group_month.pivot_table(
        columns='event_type', 
        index= 'month',
        values = 'count_value', 
        aggfunc= 'sum',
        fill_value=0)
    monthly_cr['cr'] = monthly_cr['purchase'] / monthly_cr['view']
    print('CR 1 = Unique users with purchase / Unique users with view')
    cr1_stat = cr_sample_sizing(monthly_cr)
    
    #Number of users for CR2
    print('CR 2 = Unique users with purchase / Unique users with checkout')
    monthly_cr['cr'] = monthly_cr['purchase'] / monthly_cr['checkout']
    cr2_stat = cr_sample_sizing(monthly_cr)

    mean_views = monthly_cr['view'].mean()
    metric_stats = [arpu_stat,  cr1_stat, cr2_stat]
    metric_stats = pd.DataFrame(metric_stats, columns=['history_mean', 'history_var', 'mde', 'size'])
    metric_stats['num_months'] = (2*metric_stats['size']) / mean_views
    metric_stats = metric_stats.set_axis(["ARPU", "CR1", "CR2"], axis='index')
    
    # Write to csv
    metric_stats.to_csv('..//assets//metrics_stats.csv', float_format="%.2f",index=True)
    