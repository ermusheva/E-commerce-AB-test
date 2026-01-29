import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine
import random
from datetime import datetime, timedelta
import configparser
import os
import matplotlib.pyplot as plt
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
        cr = 0.65
        rev_mult = 1.041

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

def get_pivoted_df_by_event_type(df, event_name, value_col='event_type', agg_func='sum'):
    # Filter for the specific event
    filtered_df = df[df['event_type'] == event_name]
    
    pivoted = filtered_df.pivot_table(
        index='date',
        columns='test_group',
        values=value_col, 
        aggfunc=agg_func,
        fill_value=0
    )
    return pivoted.rename(columns={value_col : 'value'})

def plot_chart(df, title, ylabel, filename):
    dates = df.index
    x = np.arange(len(dates))
    width = 0.35
    
    plt.bar(x - width/2, df['A'], width, label='Group A', color='#94A3B8')
    plt.bar(x + width/2, df['B'], width, label='Group B', color="#8B5CF6")
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(ylabel)
    plt.xticks(x[::15], [d.strftime('%m-%d') for d in dates[::15]])
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def pivot_plot_df_events(df_events, df_users):
    df_events['event_timestamp'] = pd.to_datetime(df_events['event_timestamp'])
    df_cleaned_events = df_events.dropna(subset=['event_timestamp']).copy()
    df_cleaned_events['date'] = df_cleaned_events['event_timestamp'].dt.date
    df_cleaned_events = df_cleaned_events.merge(df_users, on='user_id')
    df_count_view = get_pivoted_df_by_event_type(df_cleaned_events, 'view', agg_func='count')
    df_count_add_to_basket = get_pivoted_df_by_event_type(df_cleaned_events, 'add_to_basket', agg_func='count')
    df_count_checkout = get_pivoted_df_by_event_type(df_cleaned_events, 'checkout', agg_func='count')
    df_count_purchase = get_pivoted_df_by_event_type(df_cleaned_events, 'purchase', agg_func='count')
    df_value_purchase = get_pivoted_df_by_event_type(df_cleaned_events, 'purchase', value_col='revenue', agg_func='sum')

    print("Daily Views (First 5 rows):")
    print(df_count_view.head())
    print("Daily Revenue (First 5 rows):")
    print(df_value_purchase.head())

    plot_chart(df_count_view, 'Daily Views', 'Count', './/assets//count_views.png')
    plot_chart(df_count_add_to_basket, 'Daily Add to Basket', 'Count', './/assets//count_baskets.png')
    plot_chart(df_count_checkout, 'Daily Checkouts', 'Count', './/assets//count_checkouts.png')
    plot_chart(df_count_purchase, 'Daily Purchases', 'Count', './/assets//count_purchase.png')
    plot_chart(df_value_purchase, 'Daily Revenue', 'Revenue ($)', './/assets//revenue.png')
    
    
 

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
    
    # Plot daily data 
    pivot_plot_df_events(df_events, df_users)
    
    # Insert to DB
    df_users.to_sql('UserAssignments', con=engine, if_exists='replace', index=False)
    df_events.to_sql('EventLogs', con=engine, if_exists='replace', index=False)

    # Populate DailyMetrics table
    print("Data uploaded successfully.")
    
    

  
