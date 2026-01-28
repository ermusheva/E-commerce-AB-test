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

def load_data(config)->pd.DataFrame:
    #  DB Connection parameters
    connection_string = (
        f"mssql+pyodbc://{config['DB PARAMS']['USERNAME']}:{config['DB PARAMS']['PASSWORT']}@{config['DB PARAMS']['SERVER']}/{config['DB PARAMS']['DATABASE']}"
        f"?driver={config['DB PARAMS']['DRIVER']}"
    )
    engine = create_engine(connection_string, fast_executemany=True)
    
    # Load data
    first_test_month = int(datetime.strptime(config['DATA']['TEST_START_DATE'], "%d-%m-%Y").month)
    sql_str_for_events = "SELECT * FROM [dbo].[EventsByUserGroupMonth] WHERE month = " + str(first_test_month)
    df_events_by_user_group_month = pd.read_sql(sql_str_for_events, con=engine)
    return df_events_by_user_group_month



if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(".//scripts//config.ini")
    df_events_by_user_group_month = load_data(config)

    # A/B test for CR = Unique number of users with purchase / Unique number of users with checkout
    group_cr = df_events_by_user_group_month.pivot_table(
        columns='event_type', 
        index= 'test_group',
        values = 'user_id', 
        aggfunc = lambda x: len(x.unique()),
        fill_value=0)
    
    group_cr['cr'] = group_cr['purchase'] / group_cr['checkout']
    print(group_cr.head())

    p_value = local_stat.proportions_z_test(group_cr.loc['A']['cr'], group_cr.loc['B']['cr'], group_cr.loc['A']['view'], group_cr.loc['B']['view'])
    if p_value < float(config['EXPERIMENT']['ALPHA']):
        print(f"A/B test passed successfully. \nCan reject null-hypothesis as P-value for CR test {p_value:.2}. \nSamples A and B represent significantly difference.")
    else:
        print(f"A/B test doesn't pass! \nNull-hypothesis can NOT be rejected as P-value for CR test {p_value:.4}. \nSamples A and B from experiment do not represent significantly difference.")

    
        