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
import data_exchange


def sample_sizing(history_var, mde, alpha=0.05, power=0.8):
    z_alpha = sp.stats.norm.ppf(1-alpha/2)
    z_beta = sp.stats.norm.ppf(power)
    n = 2*history_var*((z_alpha+z_beta)**2)/(mde**2)
    return n

# Size of sample for ARPU
def arpu_sample_sizing(engine, first_history_month, last_history_month, alpha=0.05, power=0.8):
    sql_str_for_events = "SELECT * FROM [dbo].[vw_MonthlyRevenueStats] WHERE month BETWEEN " + str(first_history_month) + " AND " + str(last_history_month)
    df_revenue_stats_by_month = pd.read_sql(sql_str_for_events, con=engine)
    
    history_revenue_mean = df_revenue_stats_by_month['mean_revenue'].mean()
    history_revenue_var = df_revenue_stats_by_month['var_revenue'].mean()
    print(f"History mean revenue {history_revenue_mean.mean():.4}")
    print(f"Variance of history revenue {history_revenue_var:.8}")
    rel_revenue_mde = 0.1
    revenue_mde = rel_revenue_mde*history_revenue_mean
    print(f"Absolut MDE for revenue {revenue_mde:.8}")
    rev_sampling_size = int(sample_sizing(history_revenue_var, revenue_mde, alpha, power))
    print(f"Expected {rev_sampling_size} users for ARPU")

    mean_views = df_revenue_stats_by_month['num_users'].mean()
    print(f"Mean number of unique users per month {mean_views:.6}")
    revenue_duration = (2*rev_sampling_size) / mean_views
    print(f"Expected duration of experiment {revenue_duration:.2} months")
    return [history_revenue_mean, history_revenue_var, revenue_mde, rev_sampling_size, revenue_duration]

def cr_sample_sizing(engine, first_history_month, last_history_month, alpha=0.05, power=0.8):
    sql_str_for_events = "SELECT * FROM [dbo].[vw_MonthlyFunnel] WHERE month BETWEEN " + str(first_history_month) + " AND " + str(last_history_month)
    df_cr_stats_by_month = pd.read_sql(sql_str_for_events, con=engine)

    history_cr_mean = df_cr_stats_by_month['conversion_rate'].mean()
    history_cr_var = history_cr_mean*(1-history_cr_mean)
    print(f"History mean CR {history_cr_mean:.2}")
    print(f"Variance of history CR {history_cr_var:.4}")
    rel_cr_mde = 0.05 # relevant CR mde
    cr_mde = rel_cr_mde*history_cr_mean
    print(f"Absolut MDE for cr {cr_mde:.2}")
    cr_sampling_size = int(sample_sizing(history_cr_var, cr_mde, alpha, power))
    print(f"Expected {cr_sampling_size} users for CR")

    mean_views = df_cr_stats_by_month['num_view'].mean()
    print(f"Mean number of unique users per month {mean_views:.6}")
    cr_duration = (2*cr_sampling_size) / mean_views
    print(f"Expected duration of experiment {cr_duration:.2} months")
    return [history_cr_mean, history_cr_var, cr_mde, cr_sampling_size, cr_duration]

if __name__ == "__main__":

    config, engine = data_exchange.connect_to_db()
    last_history_month = int(datetime.strptime(config['DATA']['HISTORY_END_DATE'], "%d-%m-%Y").month)
    first_history_month = last_history_month-2
    

    # ARPU = Total revenue / Unique users with view
    arpu_stat = arpu_sample_sizing(engine, 
                                   first_history_month, 
                                   last_history_month, 
                                   float(config['EXPERIMENT']['ALPHA']), 
                                   float(config['EXPERIMENT']['POWER']))


    # Number of users for CR1 
    cr_stat = cr_sample_sizing(engine, 
                                   first_history_month, 
                                   last_history_month, 
                                   float(config['EXPERIMENT']['ALPHA']), 
                                   float(config['EXPERIMENT']['POWER']))
    metric_stats = [arpu_stat,  cr_stat]
    metric_stats = pd.DataFrame(metric_stats, columns=['history_mean', 'history_var', 'mde', 'size', 'duration_months'])
    metric_stats = metric_stats.set_axis(["ARPU", "CR"], axis='index')
    
    # Write to csv
    metric_stats.to_csv('.//assets//metrics_stats.csv', float_format="%.2f",index=True, mode='w')

        