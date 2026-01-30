-- A function to get basic statistics by group on time period from @StartDate to @EndDate
-- Used in collect_experiment_data.py, validate_experiment.py, analyze_experiment_results.py
CREATE FUNCTION dbo.GetBasicStatByGroup (
    @StartDate DATETIME,
    @EndDate DATETIME
)
RETURNS TABLE
AS
RETURN 
(SELECT UserAssignments.test_group,
    COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'view' THEN UserAssignments.[user_id] END) AS view_count,
    COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'add_to_basket' THEN UserAssignments.[user_id] END) AS add_to_basket_count,
    COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'checkout' THEN UserAssignments.[user_id] END) AS checkout_count,
    COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'purchase' THEN UserAssignments.[user_id] END) AS purchase_count,
    CAST(COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'purchase' THEN UserAssignments.[user_id] END) AS FLOAT) / 
    NULLIF(COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'checkout' THEN UserAssignments.[user_id] END), 0) AS conversion_rate,
    SUM(CASE WHEN EventLogs.event_type = 'purchase' THEN ISNULL(EventLogs.revenue, 0) END) / 
    NULLIF(COUNT(DISTINCT CASE WHEN EventLogs.event_type = 'view' THEN UserAssignments.[user_id] END), 0) AS arpu
  FROM [EcommABtestDB].[dbo].[EventLogs]
  LEFT JOIN [EcommABtestDB].[dbo].[UserAssignments]
  ON [EventLogs].[user_id] = [UserAssignments].[user_id]
  WHERE event_timestamp BETWEEN @StartDate AND @EndDate
  GROUP BY UserAssignments.test_group
);
GO

-- A function to get total revenue by user on time period from @StartDate to @EndDate
-- Used in validate_experiment.py, analyze_experiment_results.py, collect_experiment_data.py
CREATE FUNCTION dbo.GetTotalRevenueByUser (
    @StartDate DATETIME,
    @EndDate DATETIME
)
RETURNS TABLE
AS
RETURN 
(
    SELECT UserAssignments.test_group
        , UserAssignments.user_id
        , SUM(ISNULL(EventLogs.revenue, 0)) AS revenue_sum
    FROM [EcommABtestDB].[dbo].[EventLogs]
    LEFT JOIN [EcommABtestDB].[dbo].[UserAssignments]
    ON [EventLogs].[user_id] = [UserAssignments].[user_id]
    WHERE EventLogs.event_timestamp BETWEEN @StartDate AND @EndDate
    GROUP BY UserAssignments.test_group, UserAssignments.[user_id]
);
GO