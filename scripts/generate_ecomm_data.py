import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine
import random
from datetime import datetime, timedelta
import configparser
import os
import data_exchange

def generate_experiment_descr(test_name, test_h0)  -> pd.DataFrame:
    experiment_descr = [test_name, test_h0, 'running']
    df_experiment_descr = pd.DataFrame([experiment_descr], columns=['experiment_name', 'hypothesis', 'status'])
    return df_experiment_descr

def generate_users(num_users: int, experiment_id:int) -> pd.DataFrame:
    user_ids = [str(fake.unique.uuid4()) for _ in range(num_users)]
    df_users = pd.DataFrame({
        'user_id': user_ids,
        'experiment_id' : experiment_id,
        'test_group': ['A' if (hash(id) % 2)<1 else 'B' for id in user_ids],
        'assigned_at': datetime.today()
    })
    return df_users

def generate_session(uid, group, start_date, end_date, is_test_period=False)->list:
    """Generates a sequence of events with varying devices and conditional revenue
    Return list of ['user_id', 'event_type', 'event_timestamp', 'device', 'revenue']-list
    """
    events = []
    ts = fake.date_time_between(start_date=start_date, end_date=end_date)
    # Device can change between sessions
    session_device = np.random.choice(['mobile', 'desktop', 'tablet'], p=[0.6, 0.3, 0.1])
    
    # Uplift logic for test period
    cr = 0.6
    rev_mult = 1.0
    if is_test_period and group == 'B':
        cr = 0.63
        rev_mult = 1.04

    # View
    events.append([uid, 'view', ts, session_device, None])
    
    # Funnel progression
    if random.random() < 0.4:
        events.append([uid, 'add_to_basket', ts + timedelta(minutes=2), session_device, None])
        if random.random() < 0.5:
            events.append([uid, 'checkout', ts + timedelta(minutes=5), session_device, None])
            if random.random() < cr:
                rev = np.random.lognormal(3.5, 0.8) * rev_mult
                events.append([uid, 'purchase', ts + timedelta(minutes=7), session_device, round(rev, 2)])
    return events


def generate_events(df_users: pd.DataFrame, 
                    start_history_date: datetime, end_history_date:datetime,
                    start_test_date: datetime, end_test_date:datetime)->pd.DataFrame:
    # Generate History and Test
    events = list([])
    num_history_days = (end_history_date - start_history_date).days
    num_test_days = (end_test_date - end_history_date).days
    for _, row in df_users.iterrows():
        # events are randomly distributed by days in period, 
        # number of generated events should scale proportionally with the length of period
        for i in range(round(num_history_days/10)):
            history_session = generate_session(row['user_id'], row['test_group'], start_history_date, end_history_date, False)
            events = history_session + events
        for i in range(round(num_test_days/10)):
            test_session = generate_session(row['user_id'], row['test_group'], start_test_date, end_test_date, True)
            events = test_session + events  

    return pd.DataFrame(events, columns=['user_id', 'event_type', 'event_timestamp', 'device', 'revenue'])

if __name__ == "__main__":
    fake = Faker()
    np.random.seed(42)
    config, engine = data_exchange.connect_to_db()

    df_experiment = generate_experiment_descr(config['EXPERIMENT']['NAME'], config['EXPERIMENT']['H0'])
    df_experiment.to_sql('Experiments', con=engine, if_exists='append', index=False)
    sql_str_for_experiment_id = "SELECT MAX([experiment_id]) FROM [EcommABtestDB].[dbo].[Experiments]"
    experiment_id = int(pd.read_sql(sql_str_for_experiment_id, con=engine).iloc[0,0])
    
    df_users = generate_users(int(config['DATA']['NUM_USERS']), experiment_id)
    
    len_a =  (df_users['test_group'] == 'A').sum()
    print((f"Unique users in group A {len_a} and in group B {len(df_users) - len_a}"))
    
    df_events = generate_events(df_users, datetime.strptime(config['DATA']['HISTORY_START_DATE'], "%d-%m-%Y"), datetime.strptime(config['DATA']['HISTORY_END_DATE'], "%d-%m-%Y"),
                                datetime.strptime(config['DATA']['TEST_START_DATE'], "%d-%m-%Y"), datetime.strptime(config['DATA']['TEST_END_DATE'], "%d-%m-%Y"))
    
    # Insert to DB
    df_users.to_sql('UserAssignments', con=engine, if_exists='replace', index=False)
    df_events.to_sql('EventLogs', con=engine, if_exists='replace', index=False)

    # Populate DailyMetrics table
    print("Data uploaded successfully.")
    
    

  
