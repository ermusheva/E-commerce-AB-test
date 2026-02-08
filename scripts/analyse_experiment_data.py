import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine, text
import random
from datetime import datetime, timedelta
import configparser
import os
import matplotlib.pyplot as plt
import scipy as sp
import local_statistics as local_stat
import data_exchange


def save_experiment_results(engine, experiment_id, metric_name, control_val, variant_val, p_val, alpha, sample_a, sample_b, duration):
    lift = (variant_val - control_val) / control_val if control_val != 0 else 0
    
    # Clean up previous results for this metric/experiment to avoid duplicates
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM ExperimentMetrics WHERE experiment_id = {experiment_id} AND metric_name = '{metric_name}'"))
        conn.commit()
    
    results_df = pd.DataFrame([{
        'experiment_id': experiment_id,
        'metric_name': metric_name,
        'control_value': control_val,
        'variant_value': variant_val,
        'lift': lift,
        'p_value': p_val,
        'is_significant': 1 if p_val < alpha else 0,
        'analysis_date': datetime.now(),
        'sample_size_a': sample_a,
        'sample_size_b': sample_b,
        'test_duration_days': duration,
        'notes': f"Alpha: {alpha}"
    }])
    results_df.to_sql('ExperimentMetrics', con=engine, if_exists='append', index=False)
    print(f"Saved {metric_name} results to ExperimentMetrics.")

if __name__ == "__main__":

    config, engine = data_exchange.connect_to_db()
    
    # Get experiment info
    sql_str_for_experiment_id = "SELECT MAX([experiment_id]) FROM [dbo].[Experiments]"
    try:
        experiment_id = int(pd.read_sql(sql_str_for_experiment_id, con=engine).iloc[0,0])
    except:
        experiment_id = 1
        print("Warning: Could not fetch experiment_id, defaulting to 1")

    test_start = datetime.strptime(config['DATA']['TEST_START_DATE'], "%d-%m-%Y")
    test_end = datetime.strptime(config['DATA']['TEST_END_DATE'], "%d-%m-%Y")
    duration_days = (test_end - test_start).days
    alpha = float(config['EXPERIMENT']['ALPHA'])

    # A/B test for CR = Unique number of users with purchase / Unique number of users with checkout
    start_date = test_start.strftime("%Y-%m-%d")
    end_date = test_end.strftime("%Y-%m-%d")
    sql_str = f"SELECT * FROM dbo.GetBasicStatByGroup('{start_date}', '{end_date}')"
    group_cr = pd.read_sql(sql_str, con=engine)
    group_cr = group_cr.set_index('test_group')
    
    p_value = local_stat.proportions_z_test(
        group_cr.loc['A']['conversion_rate'], 
        group_cr.loc['B']['conversion_rate'], 
        group_cr.loc['A']['view_count'], 
        group_cr.loc['B']['view_count'])
    
    if p_value < alpha:
        print(f"\nA/B test passed successfully. \nCan reject null-hypothesis as P-value for CR test {p_value:.2}. \nSamples A and B represent significantly difference.")
    else:
        print(f"\nA/B test doesn't pass! \nNull-hypothesis can NOT be rejected as P-value for CR test {p_value:.4}. \nSamples A and B from experiment do not represent significantly difference.")

    
    save_experiment_results(engine, experiment_id, 'CR', 
                            group_cr.loc['A']['conversion_rate'], 
                            group_cr.loc['B']['conversion_rate'], 
                            p_value, alpha, 
                            group_cr.loc['A']['view_count'], 
                            group_cr.loc['B']['view_count'], 
                            duration_days)
    
    
    # A/B test for revenue
    sql_str = f"SELECT * FROM dbo.GetTotalRevenueByUser('{start_date}', '{end_date}')"
    group_revenue = pd.read_sql(sql_str, con=engine)
    group_a_values = group_revenue[group_revenue['test_group'] == 'A']['revenue_sum']
    group_b_values = group_revenue[group_revenue['test_group'] == 'B']['revenue_sum']
    u_stat, p_value = sp.stats.mannwhitneyu(group_a_values, group_b_values, alternative='two-sided')
    
    if p_value < alpha:
        print(f"\nA/B test for revenue passed. \nCan reject null-hypothesis as P-value for ARPU test {p_value:.2}. \nSamples A and B on history data represent significantly difference.")
    else:
        print(f"\nA/B test for revenue doesn't pass! \nNull-hypothesis can NOT be rejected as P-value for ARPU test {p_value:.4}. \nSamples A and B on history data don't represent significantly difference.")
    
    
    save_experiment_results(engine, experiment_id, 'ARPU', 
                            group_a_values.mean(), 
                            group_b_values.mean(), 
                            p_value, alpha, 
                            len(group_a_values), 
                            len(group_b_values), 
                            duration_days)
    
    
        