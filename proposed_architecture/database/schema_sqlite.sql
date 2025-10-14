-- SQLite Schema for Evaluation System
-- Adapted from PostgreSQL schema for SQLite compatibility

-- Use cases table
CREATE TABLE IF NOT EXISTS use_cases (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    name TEXT NOT NULL,
    team_email TEXT NOT NULL,
    state TEXT NOT NULL,
    config_file_path TEXT,  -- Local path or S3 key
    dataset_file_path TEXT,  -- Local path or S3 key
    quality_issues TEXT,  -- JSON stored as TEXT
    evaluation_results TEXT,  -- JSON stored as TEXT
    metadata TEXT DEFAULT '{}',  -- JSON stored as TEXT
    created_at TEXT DEFAULT (datetime('now')),  -- ISO8601 timestamp
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL,  -- e.g., 'azure_openai', 'bedrock'
    config TEXT NOT NULL,  -- JSON: endpoint, version, etc.
    is_active INTEGER DEFAULT 1,  -- SQLite uses INTEGER for boolean
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- State transitions table
CREATE TABLE IF NOT EXISTS state_transitions (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    from_state TEXT,
    to_state TEXT NOT NULL,
    triggered_by TEXT NOT NULL,  -- 'system', 'user', 'email'
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE
);

-- Evaluation results table
CREATE TABLE IF NOT EXISTS evaluation_results (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    result_file_path TEXT,  -- S3 key for detailed results
    summary TEXT,  -- JSON: accuracy, precision, recall, etc.
    status TEXT NOT NULL,  -- 'running', 'completed', 'failed'
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id)
);

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    id TEXT PRIMARY KEY,
    use_case_id TEXT,
    activity_type TEXT NOT NULL,  -- 'email_sent', 'quality_check', 'evaluation', etc.
    description TEXT NOT NULL,
    details TEXT,  -- JSON for additional info
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE SET NULL
);

-- S3 file tracking table (NEW)
CREATE TABLE IF NOT EXISTS s3_files (
    id TEXT PRIMARY KEY,
    use_case_id TEXT,
    file_type TEXT NOT NULL,  -- 'config', 'dataset', 'results', 'backup'
    s3_bucket TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    local_path TEXT,  -- Local cache path if downloaded
    file_size INTEGER,
    checksum TEXT,  -- MD5 or SHA256
    uploaded_at TEXT DEFAULT (datetime('now')),
    metadata TEXT,  -- JSON for additional info
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE
);

-- Database backup tracking table (NEW)
CREATE TABLE IF NOT EXISTS backup_history (
    id TEXT PRIMARY KEY,
    backup_type TEXT NOT NULL,  -- 'full', 'incremental'
    s3_bucket TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    file_size INTEGER,
    checksum TEXT,
    backup_time TEXT DEFAULT (datetime('now')),
    status TEXT NOT NULL,  -- 'completed', 'failed'
    notes TEXT
);

-- Indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_use_cases_state ON use_cases(state);
CREATE INDEX IF NOT EXISTS idx_use_cases_team_email ON use_cases(team_email);
CREATE INDEX IF NOT EXISTS idx_use_cases_created_at ON use_cases(created_at);

CREATE INDEX IF NOT EXISTS idx_state_transitions_use_case ON state_transitions(use_case_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_created_at ON state_transitions(created_at);

CREATE INDEX IF NOT EXISTS idx_evaluation_results_use_case ON evaluation_results(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_status ON evaluation_results(status);

CREATE INDEX IF NOT EXISTS idx_activity_log_use_case ON activity_log(use_case_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_type ON activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);

CREATE INDEX IF NOT EXISTS idx_s3_files_use_case ON s3_files(use_case_id);
CREATE INDEX IF NOT EXISTS idx_s3_files_type ON s3_files(file_type);
CREATE INDEX IF NOT EXISTS idx_s3_files_s3_key ON s3_files(s3_key);

-- Triggers to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_use_cases_timestamp
AFTER UPDATE ON use_cases
BEGIN
    UPDATE use_cases SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_models_timestamp
AFTER UPDATE ON models
BEGIN
    UPDATE models SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Insert default models (optional)
INSERT OR IGNORE INTO models (id, name, model_type, config, is_active) VALUES
    ('default-gpt4', 'GPT-4', 'azure_openai', '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-4"}', 1),
    ('default-claude', 'Claude-3', 'bedrock', '{"model_id": "anthropic.claude-3-sonnet-20240229-v1:0", "region": "us-east-1"}', 1);
