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
import local_statistics as local_stat
import data_exchange


if __name__ == "__main__":
    
    config, engine = data_exchange.connect_to_db()
        
    # A/A test for CR = Unique number of users with purchase / Unique number of users with checkout
    start_date = datetime.strptime(config['DATA']['HISTORY_START_DATE'], "%d-%m-%Y").strftime("%Y-%m-%d")
    end_date = datetime.strptime(config['DATA']['HISTORY_END_DATE'], "%d-%m-%Y").strftime("%Y-%m-%d")
    
    sql_str = f"SELECT * FROM dbo.GetBasicStatByGroup('{start_date}', '{end_date}')"
    group_cr = pd.read_sql(sql_str, con=engine)
    group_cr = group_cr.set_index('test_group')
    
    p_value = local_stat.proportions_z_test(
        group_cr.loc['A']['conversion_rate'], 
        group_cr.loc['B']['conversion_rate'], 
        group_cr.loc['A']['view_count'], 
        group_cr.loc['B']['view_count'])
    if p_value > float(config['EXPERIMENT']['ALPHA']):
        print(f"\nA/A test for CR passed. \nCan't reject null-hypothesis as P-value for CR test {p_value:.2}. \nSamples A and B on history data do not represent significantly difference.")
    else:
        print(f"\nA/A test for CR doesn't pass! Re-sample data! \nNull-hypothesis can be rejected as P-value for CR test {p_value:.4}. \nSamples A and B on history data represent significantly difference.")
    
    # A/A test for revenue
    sql_str = f"SELECT * FROM dbo.GetTotalRevenueByUser('{start_date}', '{end_date}')"
    group_revenue = pd.read_sql(sql_str, con=engine)
    group_a_values = group_revenue[group_revenue['test_group'] == 'A']['revenue_sum']
    group_b_values = group_revenue[group_revenue['test_group'] == 'B']['revenue_sum']
    u_stat, p_value = sp.stats.mannwhitneyu(group_a_values, group_b_values, alternative='two-sided')
    if p_value > float(config['EXPERIMENT']['ALPHA']):
        print(f"\nA/A test for revenue passed. \nCan't reject null-hypothesis as P-value for ARPU test {p_value:.2}. \nSamples A and B on history data do not represent significantly difference.")
    else:
        print(f"\nA/A test for revenue doesn't pass! Re-sample data! \nNull-hypothesis can be rejected as P-value for ARPU test {p_value:.4}. \nSamples A and B on history data represent significantly difference.")

    # Simple Ratio Mismatch
    srm_p_value = local_stat.check_srm(group_cr.loc['A']['view_count'], group_cr.loc['B']['view_count'])
    if srm_p_value > 0.01:
        print(f"\nNo SRM Detected. \nP-value for Chi-Square Goodness of Fit is {srm_p_value:.2}")
    else:
        print(f"\nSRM Detected! Check for bugs.\n P-value for Chi-Square Goodness of Fit is {srm_p_value:.2}")
