import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import configparser
import scipy as sp
import data_exchange

    

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

def plot_bar(df, title, ylabel, filename):
    dates = df.index
    x = np.arange(len(dates))
    width = 0.35
    
    plt.bar(x - width/2, df['A'], width, label='Group A', color='#1F3A5F')
    plt.bar(x + width/2, df['B'], width, label='Group B', color="#C2410C")
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(ylabel)
    plt.xticks(x[::5], [d.strftime('%m-%d') for d in dates[::5]])
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def plot_chart(df, title, ylabel, filename):
    dates = df.index
    x = np.arange(len(dates))
    
    plt.plot(x, df['A'], label='Group A', color='#1F3A5F')
    plt.plot(x, df['B'], label='Group B', color="#C2410C")
    
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel(ylabel)
    plt.xticks(x[::5], [d.strftime('%m-%d') for d in dates[::5]])
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

def visualize_daily_metrics(engine, start_date, end_date):
    query = f"SELECT * FROM DailyMetrics WHERE date BETWEEN '{start_date}' AND '{end_date}' ORDER BY date"
    df = pd.read_sql(query, con=engine)
    df['date'] = pd.to_datetime(df['date']).dt.date

    df_count_view = get_pivoted_df_by_event_type(df, 'view', value_col='event_count', agg_func='sum')
    df_count_add_to_basket = get_pivoted_df_by_event_type(df, 'add_to_basket', value_col='event_count', agg_func='sum')
    df_count_checkout = get_pivoted_df_by_event_type(df, 'checkout', value_col='event_count', agg_func='sum')
    df_count_purchase = get_pivoted_df_by_event_type(df, 'purchase', value_col='event_count', agg_func='sum')
    df_value_purchase = get_pivoted_df_by_event_type(df, 'purchase', value_col='total_revenue', agg_func='sum')
    
    df_unique_checkout = get_pivoted_df_by_event_type(df, 'checkout', value_col='unique_users', agg_func='sum')
    df_unique_purchase = get_pivoted_df_by_event_type(df, 'purchase', value_col='unique_users', agg_func='sum')
    df_cr = df_unique_purchase / df_unique_checkout
    df_cr = df_cr.fillna(0)

    plot_bar(df_count_view, 'Daily Views', 'Count', './/assets//count_views.png')
    plot_bar(df_count_add_to_basket, 'Daily Add to Basket', 'Count', './/assets//count_baskets.png')
    plot_bar(df_count_checkout, 'Daily Checkouts', 'Count', './/assets//count_checkouts.png')
    plot_bar(df_count_purchase, 'Daily Purchases', 'Count', './/assets//count_purchase.png')
    plot_bar(df_value_purchase, 'Daily Revenue', 'Revenue ($)', './/assets//revenue.png')
    plot_bar(df_cr, 'Daily Conversion Rate', 'Conversion Rate', './/assets//daily_cr.png')
    plot_chart(df_cr, 'Daily Conversion Rate', 'Conversion Rate', './/assets//daily_cr_line.png')

def populate_daily_metrics(engine, experiment_id):
    with engine.connect() as conn:
        conn.execute(text(f"DELETE FROM DailyMetrics WHERE experiment_id = {experiment_id}"))
        conn.execute(text("""
            INSERT INTO DailyMetrics (date, experiment_id, test_group, event_type, event_count, unique_users, total_revenue, created_at)
            SELECT
                CAST(e.event_timestamp AS DATE) AS date,
                u.experiment_id,
                u.test_group,
                e.event_type,
                COUNT(u.user_id) AS event_count,
                COUNT(DISTINCT u.user_id) AS unique_users,
                ISNULL(SUM(e.revenue), 0) AS total_revenue,
                GETDATE() AS created_at
            FROM EventLogs AS e
            JOIN UserAssignments AS u ON e.user_id = u.user_id
            WHERE e.event_timestamp IS NOT NULL
            GROUP BY CAST(e.event_timestamp AS DATE), u.test_group, u.experiment_id, e.event_type
        """))
        conn.execute(text(f"DELETE FROM MonthlyCumulativeUniqueUsers WHERE experiment_id = {experiment_id}"))
        conn.execute(text("""
                          WITH UserFirstSeenInMonth AS (
                SELECT 
                    e.user_id,
                    a.test_group, 
                    a.experiment_id,
                    e.event_type,
                    MONTH(e.event_timestamp) AS event_month,
                    MIN(CAST(e.event_timestamp AS DATE)) AS first_seen_date
                FROM EventLogs AS e
                LEFT JOIN UserAssignments AS a 
                ON e.user_id = a.user_id
                WHERE e.event_timestamp IS NOT NULL
                GROUP BY e.user_id, MONTH(e.event_timestamp), a.test_group, a.experiment_id, e.event_type
            )
            INSERT INTO MonthlyCumulativeUniqueUsers (date, test_group, experiment_id, event_type, cumulative_unique_users)
            SELECT 
                first_seen_date AS date,
                test_group,
                experiment_id,
                event_type,
                SUM(COUNT(user_id)) OVER (PARTITION BY event_month, test_group, experiment_id, event_type ORDER BY first_seen_date) AS cumulative_unique_users
            FROM UserFirstSeenInMonth
            GROUP BY first_seen_date, event_month, test_group, experiment_id, event_type
            """)        )
        conn.commit()
        print("DailyMetrics table populated successfully.")


def plot_revenue_histogram(engine, start_date, end_date):
    sql_str = f"SELECT * FROM dbo.GetTotalRevenueByUser('{start_date}', '{end_date}')"
    df = pd.read_sql(sql_str, con=engine)

    
    # plt.figure(figsize=(10, 6))
    plt.hist(df['revenue_sum'], bins=20, color='#94A3B8')
    plt.title('Experiment Revenue Distribution')
    plt.xlabel('Revenue by user($)')
    plt.ylabel('Frequency')
    plt.tight_layout()
    plt.savefig('.//assets//experiment_revenue_histogram.png')
    plt.close()

if __name__ == "__main__":
    config, engine = data_exchange.connect_to_db()
    
    # Populate DailyMetrics table
    sql_str_for_experiment_id = "SELECT MAX([experiment_id]) FROM [EcommABtestDB].[dbo].[Experiments]"
    experiment_id = int(pd.read_sql(sql_str_for_experiment_id, con=engine).iloc[0,0])
    populate_daily_metrics(engine, experiment_id)
    
    # Collect the main experiment statistics 
    # as number of unique users with event, conversion rate, total revenue by group
    start_date = (datetime.strptime(config['DATA']['TEST_START_DATE'], "%d-%m-%Y")).strftime("%Y-%m-%d")
    end_date = datetime.strptime(config['DATA']['TEST_END_DATE'], "%d-%m-%Y").strftime("%Y-%m-%d")
    sql_str = f"SELECT * FROM dbo.GetBasicStatByGroup('{start_date}', '{end_date}')"
    experiment_data = pd.read_sql(sql_str, con=engine)
    experiment_data.to_csv('.//assets//experiment_basic_data.csv', float_format="%.2f",index=False, mode='w')

    #Save plots in assets folder
    visualize_daily_metrics(engine, start_date, end_date)
    plot_revenue_histogram(engine, start_date, end_date)
    print("Plots saved successfully.")
    