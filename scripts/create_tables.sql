-- Transactional Event Log
CREATE TABLE EventLogs (
    event_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id VARCHAR(50),
    event_type VARCHAR(50),
    event_timestamp DATETIME NULL,
    device VARCHAR(20),      -- can change per session
    revenue DECIMAL(18, 2)   -- only for event_type='purchase'
);
GO

-- Metadata for the experiment
CREATE TABLE Experiments (
    experiment_id INT IDENTITY(1,1) PRIMARY KEY,
    experiment_name VARCHAR(100),
    hypothesis TEXT,
    status VARCHAR(20) -- 'running', 'completed', 'archived'
);
GO

-- Which user was in which group for which test
CREATE TABLE UserAssignments (
    user_id VARCHAR(50),
    experiment_id INT,
    test_group CHAR(1), -- 'A' or 'B'
    assigned_at DATETIME,
    PRIMARY KEY (user_id, experiment_id),
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
GO

-- Flexible results table (stores any metric)
CREATE TABLE ExperimentMetrics (
    metric_id INT IDENTITY(1,1) PRIMARY KEY,
    experiment_id INT,
    metric_name VARCHAR(50), -- 'CR', 'ARPU'
    control_value FLOAT,
    variant_value FLOAT,
    lift FLOAT,
    p_value FLOAT,
    is_significant BIT,
    analysis_date DATETIME, -- When analysis was run
    sample_size_a INT, -- Group A size
    sample_size_b INT, -- Group B size
    test_duration_days INT, --Experiment length
    notes TEXT, -- Additional context
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
GO

-- Aggregated daily metrics for each test
CREATE TABLE DailyMetrics (
    date DATE,
    experiment_id INT,
    test_group CHAR(1), -- 'A' or 'B'
    event_type VARCHAR(50), -- 'view', 'add_to_basket', 'checkout', 'purchase'
    event_count INT,
    unique_users INT,
    total_revenue DECIMAL(18, 2), -- NULL for non-purchase events
    created_at DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (date, experiment_id, test_group, event_type),
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
GO

CREATE TABLE MonthlyCumulativeUniqueUsers  (
    date DATE,
    experiment_id INT,
    test_group CHAR(1), -- 'A' or 'B'
    event_type VARCHAR(50), -- 'view', 'add_to_basket', 'checkout', 'purchase'
    cumulative_unique_users INT,
    PRIMARY KEY (date, experiment_id, test_group, event_type),
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);
GO