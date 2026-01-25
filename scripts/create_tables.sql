-- Transactional Event Log
CREATE TABLE EventLogs (
    event_id INT IDENTITY(1,1) PRIMARY KEY,
    user_id VARCHAR(50),
    event_type VARCHAR(50),
    event_timestamp DATETIME NULL,
    device VARCHAR(20),      -- can change per session
    revenue DECIMAL(18, 2)   -- only for event_type='purchase'
);

-- Metadata for the experiment
CREATE TABLE Experiments (
    experiment_id INT IDENTITY(1,1) PRIMARY KEY,
    experiment_name VARCHAR(100),
    hypothesis TEXT,
    status VARCHAR(20) -- 'running', 'completed', 'archived'
);

-- Which user was in which group for which test
CREATE TABLE UserAssignments (
    user_id VARCHAR(50),
    experiment_id INT,
    test_group CHAR(1), -- 'A' or 'B'
    assigned_at DATETIME,
    PRIMARY KEY (user_id, experiment_id),
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);

-- Flexible results table (stores any metric)
CREATE TABLE ExperimentMetrics (
    metric_id INT IDENTITY(1,1) PRIMARY KEY,
    experiment_id INT,
    metric_name VARCHAR(50), -- 'CR', 'ARPU', 'Retention', 'Latency'
    control_value FLOAT,
    variant_value FLOAT,
    lift_pct FLOAT,
    p_value FLOAT,
    is_significant BIT,
    FOREIGN KEY (experiment_id) REFERENCES Experiments(experiment_id)
);