import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import configparser
import scipy as sp

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

    first_test_month = int(datetime.strptime(config['DATA']['TEST_START_DATE'], "%d-%m-%Y").month)
    
    df_events_by_user_group_month = df_events_by_user_group_month[df_events_by_user_group_month['month'].
                                                                  between(first_test_month, first_test_month+1)].copy()

    revenue_by_groups = df_events_by_user_group_month.groupby('test_group')['total_revenue'].sum() 
    experiment_data = df_events_by_user_group_month.pivot_table(
        index='test_group',
        columns='event_type',
        values='count_value',
        aggfunc= 'sum',
        fill_value=0
    )
    experiment_data['cr'] = experiment_data['purchase'] / experiment_data['checkout']
    experiment_data['arpu'] = revenue_by_groups / experiment_data['view']

    # Write to csv
    experiment_data.to_csv('..//assets//experiment_basic_data.csv', float_format="%.2f",index=True)
    