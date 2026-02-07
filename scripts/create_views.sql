-- A view with monthly funnel (unique users count bz event type) and conversion rate
-- Used in fix_sample_size.py
CREATE VIEW vw_MonthlyFunnel AS
SELECT 
    MONTH(event_timestamp) AS month,
    COUNT(DISTINCT CASE WHEN event_type = 'view' THEN [user_id] END) as num_view,
    COUNT(DISTINCT CASE WHEN event_type = 'add_to_basket' THEN [user_id] END) as num_add_to_basket,
    COUNT(DISTINCT CASE WHEN event_type = 'checkout' THEN [user_id] END) as num_checkout,
    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN [user_id] END) as num_purchase,
    CAST(COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN [user_id] END) AS FLOAT) / 
        NULLIF(COUNT(DISTINCT CASE WHEN event_type = 'checkout' THEN [user_id] END), 0) AS conversion_rate
FROM EventLogs
GROUP BY MONTH(event_timestamp);
GO

-- A view with monthly revenue statistics (mean and variance)
-- Used in fix_sample_size.py
CREATE VIEW vw_MonthlyRevenueStats AS 
    WITH RevenueByMonthUser (month, user_id, num_view, user_revenue) AS (
        SELECT 
            MONTH(event_timestamp) AS month,
            [user_id],
            COUNT(CASE WHEN event_type = 'view' THEN [user_id] END) as num_view,
            ISNULL(SUM(CASE WHEN event_type = 'purchase' THEN [revenue] END), 0) as user_revenue
        FROM EventLogs
        GROUP BY MONTH(event_timestamp), [user_id]
    ) 
    SELECT 
        month,
        COUNT(num_view) AS num_users,
        SUM(user_revenue)/NULLIF(COUNT(num_view),0) AS mean_revenue,
        VAR(user_revenue) AS var_revenue
    FROM RevenueByMonthUser
    GROUP BY month;
GO

CREATE VIEW vw_PowerBI_DailyFunnel AS
SELECT 
    date,
    experiment_id,
    test_group,
    MAX(CASE WHEN event_type = 'view' THEN unique_users END) AS views,
    MAX(CASE WHEN event_type = 'add_to_basket' THEN unique_users END) AS baskets,
    MAX(CASE WHEN event_type = 'checkout' THEN unique_users END) AS checkouts,
    MAX(CASE WHEN event_type = 'purchase' THEN unique_users END) AS purchases,
    MAX(CASE WHEN event_type = 'purchase' THEN total_revenue END) AS revenue,
    CAST(MAX(CASE WHEN event_type = 'purchase' THEN unique_users END) AS FLOAT) / 
        NULLIF(MAX(CASE WHEN event_type = 'checkout' THEN unique_users END), 0) AS conversion_rate,
    MAX(CASE WHEN event_type = 'purchase' THEN total_revenue END) / 
        NULLIF(MAX(CASE WHEN event_type = 'view' THEN unique_users END), 0) AS arpu,
    SUM(MAX(CASE WHEN event_type = 'purchase' THEN unique_users END)) 
        OVER (PARTITION BY experiment_id, test_group ORDER BY date) AS cumulative_purchases,
    SUM(MAX(CASE WHEN event_type = 'checkout' THEN unique_users END)) 
        OVER (PARTITION BY experiment_id, test_group ORDER BY date) AS cumulative_checkouts
FROM DailyMetrics
WHERE date BETWEEN '2025-06-01' AND '2025-06-30'
GROUP BY date, experiment_id, test_group;
GO

-- Group comparison view for Power BI



CREATE VIEW vw_PowerBI_GroupComparison AS
SELECT 
    a.date,
    a.experiment_id,
    a.conversion_rate AS group_a_cr,
    b.conversion_rate AS group_b_cr,
    (b.conversion_rate - a.conversion_rate) / NULLIF(a.conversion_rate, 0) * 100 AS cr_lift_pct,
    a.arpu AS group_a_arpu,
    b.arpu AS group_b_arpu,
    (b.arpu - a.arpu) / NULLIF(a.arpu, 0) * 100 AS arpu_lift_pct
FROM vw_PowerBI_DailyFunnel a
JOIN vw_PowerBI_DailyFunnel b 
    ON a.date = b.date 
    AND a.experiment_id = b.experiment_id
WHERE a.test_group = 'A' AND b.test_group = 'B'
AND a.date BETWEEN '2025-06-01' AND '2025-06-30';
GO

CREATE VIEW vw_PowerBI_Daily AS
SELECT 
    DailyMetrics.date,
    MAX(MonthlyCumulativeUniqueUsers.cumulative_unique_users) AS cumulative_unique_users,
    DailyMetrics.experiment_id,
    DailyMetrics.test_group,
    MAX(CASE WHEN event_type = 'view' THEN unique_users END) AS views,
    MAX(CASE WHEN event_type = 'add_to_basket' THEN unique_users END) AS baskets,
    MAX(CASE WHEN event_type = 'checkout' THEN unique_users END) AS checkouts,
    MAX(CASE WHEN event_type = 'purchase' THEN unique_users END) AS purchases,
    MAX(CASE WHEN event_type = 'purchase' THEN total_revenue END) AS revenue,
    CAST(MAX(CASE WHEN event_type = 'purchase' THEN unique_users END) AS FLOAT) / 
        NULLIF(MAX(CASE WHEN event_type = 'checkout' THEN unique_users END), 0) AS conversion_rate,
    MAX(CASE WHEN event_type = 'purchase' THEN total_revenue END) / 
        NULLIF(MAX(CASE WHEN event_type = 'view' THEN unique_users END), 0) AS arpu,
    SUM(MAX(CASE WHEN event_type = 'purchase' THEN unique_users END)) 
        OVER (PARTITION BY DailyMetrics.experiment_id, DailyMetrics.test_group ORDER BY DailyMetrics.date) 
        AS cumulative_purchases,
    SUM(MAX(CASE WHEN event_type = 'checkout' THEN unique_users END)) 
        OVER (PARTITION BY DailyMetrics.experiment_id, DailyMetrics.test_group ORDER BY DailyMetrics.date) 
        AS cumulative_checkouts,
    SUM(MAX(CASE WHEN event_type = 'purchase' THEN total_revenue END)) 
        OVER (PARTITION BY DailyMetrics.experiment_id, DailyMetrics.test_group ORDER BY DailyMetrics.date) 
        AS cumulative_revenue
FROM DailyMetrics
LEFT JOIN MonthlyCumulativeUniqueUsers 
    ON DailyMetrics.date = MonthlyCumulativeUniqueUsers.date 
    AND DailyMetrics.experiment_id = MonthlyCumulativeUniqueUsers.experiment_id 
    AND DailyMetrics.test_group = MonthlyCumulativeUniqueUsers.test_group
WHERE DailyMetrics.date BETWEEN '2025-06-01' AND '2025-06-30'
GROUP BY DailyMetrics.date, DailyMetrics.experiment_id, DailyMetrics.test_group;
GO