-- SQLite Schema for Evaluation System
-- Adapted from PostgreSQL schema for SQLite compatibility
-- Updated to support two-level state management: Use Case + Model

-- ============================================================================
-- Use Case Tables
-- ============================================================================

-- Use cases table
CREATE TABLE IF NOT EXISTS use_cases (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    name TEXT NOT NULL,
    team_email TEXT NOT NULL,
    state TEXT NOT NULL,  -- UseCaseState enum (template_generation, awaiting_config, etc.)
    config_file_path TEXT,  -- Local path or S3 key
    dataset_file_path TEXT,  -- Local path or S3 key (deprecated - moved to model level)
    metadata TEXT DEFAULT '{}',  -- JSON stored as TEXT
    created_at TEXT DEFAULT (datetime('now')),  -- ISO8601 timestamp
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Use case state transitions table (for use case lifecycle)
CREATE TABLE IF NOT EXISTS use_case_state_history (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    from_state TEXT,  -- Previous state (NULL for initial)
    to_state TEXT NOT NULL,  -- New state
    triggered_by TEXT NOT NULL,  -- 'system', 'user', user_id
    trigger_reason TEXT NOT NULL,  -- Why transition happened
    notes TEXT,
    additional_data TEXT,  -- JSON for extra context
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE
);

-- ============================================================================
-- Model Evaluation Tables (NEW - Two-level state management)
-- ============================================================================

-- Model evaluations table - Each model has independent state
CREATE TABLE IF NOT EXISTS model_evaluations (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    current_state TEXT NOT NULL,  -- ModelEvaluationState enum (registered, quality_check_pending, etc.)
    dataset_file_path TEXT,  -- Dataset specific to this model
    predictions_file_path TEXT,  -- Model predictions file
    quality_issues TEXT,  -- JSON array of quality issues
    evaluation_results TEXT,  -- JSON of evaluation metrics
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',  -- JSON for additional info
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    UNIQUE(use_case_id, model_name, version)  -- One version per model per use case
);

-- Model state history table - Track all state transitions for each model
CREATE TABLE IF NOT EXISTS model_state_history (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    from_state TEXT,  -- Previous state (NULL for initial)
    to_state TEXT NOT NULL,  -- New state
    triggered_by TEXT NOT NULL,  -- Who/what triggered transition
    trigger_reason TEXT NOT NULL,  -- Why transition happened
    file_uploaded TEXT,  -- File path if upload triggered transition
    quality_issues_count INTEGER,  -- Number of issues if QC related
    error_message TEXT,  -- Error details if failure
    additional_data TEXT,  -- JSON for extra context
    timestamp TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id) ON DELETE CASCADE
);

-- Quality check results table - Store detailed QC results per model
CREATE TABLE IF NOT EXISTS quality_check_results (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    passed INTEGER NOT NULL,  -- 1 for pass, 0 for fail
    issues_count INTEGER DEFAULT 0,
    issues_detail TEXT,  -- JSON array of issue objects
    checked_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id) ON DELETE CASCADE
);

-- ============================================================================
-- Shared Reference Tables
-- ============================================================================

-- Models table (ML model configurations - shared across use cases)
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    model_type TEXT NOT NULL,  -- e.g., 'azure_openai', 'bedrock'
    config TEXT NOT NULL,  -- JSON: endpoint, version, etc.
    is_active INTEGER DEFAULT 1,  -- SQLite uses INTEGER for boolean
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Evaluation results table (deprecated - moved to model_evaluations.evaluation_results)
-- Kept for backward compatibility
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
    model_id TEXT,  -- NEW: Can log activities per model
    activity_type TEXT NOT NULL,  -- 'email_sent', 'quality_check', 'evaluation', etc.
    description TEXT NOT NULL,
    details TEXT,  -- JSON for additional info
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE SET NULL,
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id) ON DELETE SET NULL
);

-- S3 file tracking table
CREATE TABLE IF NOT EXISTS s3_files (
    id TEXT PRIMARY KEY,
    use_case_id TEXT,
    model_id TEXT,  -- NEW: Files can be associated with specific models
    file_type TEXT NOT NULL,  -- 'config', 'dataset', 'results', 'backup'
    s3_bucket TEXT NOT NULL,
    s3_key TEXT NOT NULL,
    local_path TEXT,  -- Local cache path if downloaded
    file_size INTEGER,
    checksum TEXT,  -- MD5 or SHA256
    uploaded_at TEXT DEFAULT (datetime('now')),
    metadata TEXT,  -- JSON for additional info
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id) ON DELETE CASCADE
);

-- Database backup tracking table
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

-- Task queue table (for SimpleTaskQueue)
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    args TEXT,  -- JSON array
    kwargs TEXT,  -- JSON object
    status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed', 'retrying'
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    priority INTEGER DEFAULT 0  -- Higher = more important
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Use case indexes
CREATE INDEX IF NOT EXISTS idx_use_cases_state ON use_cases(state);
CREATE INDEX IF NOT EXISTS idx_use_cases_team_email ON use_cases(team_email);
CREATE INDEX IF NOT EXISTS idx_use_cases_created_at ON use_cases(created_at);

-- Use case state history indexes
CREATE INDEX IF NOT EXISTS idx_use_case_state_history_use_case ON use_case_state_history(use_case_id);
CREATE INDEX IF NOT EXISTS idx_use_case_state_history_timestamp ON use_case_state_history(timestamp);

-- Model evaluation indexes
CREATE INDEX IF NOT EXISTS idx_model_evaluations_use_case ON model_evaluations(use_case_id);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_state ON model_evaluations(current_state);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_name ON model_evaluations(model_name);

-- Model state history indexes
CREATE INDEX IF NOT EXISTS idx_model_state_history_model ON model_state_history(model_id);
CREATE INDEX IF NOT EXISTS idx_model_state_history_timestamp ON model_state_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_state_history_state ON model_state_history(to_state);

-- Quality check indexes
CREATE INDEX IF NOT EXISTS idx_quality_check_model ON quality_check_results(model_id);
CREATE INDEX IF NOT EXISTS idx_quality_check_passed ON quality_check_results(passed);

-- Evaluation results indexes
CREATE INDEX IF NOT EXISTS idx_evaluation_results_use_case ON evaluation_results(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_status ON evaluation_results(status);

-- Activity log indexes
CREATE INDEX IF NOT EXISTS idx_activity_log_use_case ON activity_log(use_case_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_model ON activity_log(model_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_type ON activity_log(activity_type);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON activity_log(created_at);

-- S3 files indexes
CREATE INDEX IF NOT EXISTS idx_s3_files_use_case ON s3_files(use_case_id);
CREATE INDEX IF NOT EXISTS idx_s3_files_model ON s3_files(model_id);
CREATE INDEX IF NOT EXISTS idx_s3_files_type ON s3_files(file_type);
CREATE INDEX IF NOT EXISTS idx_s3_files_s3_key ON s3_files(s3_key);

-- Task queue indexes
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority ON tasks(status, priority DESC, created_at);

-- ============================================================================
-- Triggers to Update Timestamps
-- ============================================================================

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

CREATE TRIGGER IF NOT EXISTS update_model_evaluations_timestamp
AFTER UPDATE ON model_evaluations
BEGIN
    UPDATE model_evaluations SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- ============================================================================
-- Default Data (Optional)
-- ============================================================================

-- Insert default models (optional)
INSERT OR IGNORE INTO models (id, name, model_type, config, is_active) VALUES
    ('default-gpt4', 'GPT-4', 'azure_openai', '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-4"}', 1),
    ('default-claude', 'Claude-3', 'bedrock', '{"model_id": "anthropic.claude-3-sonnet-20240229-v1:0", "region": "us-east-1"}', 1);

-- Insert default use case for demo/testing
INSERT OR IGNORE INTO use_cases (id, name, team_email, state, created_at, updated_at) VALUES
    ('default_use_case', 'Demo Use Case', 'demo@example.com', 'awaiting_config', datetime('now'), datetime('now'));

-- ============================================================================
-- Schema Version Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    checksum TEXT NOT NULL,
    execution_time_ms INTEGER,
    description TEXT
);

-- Record initial schema version
INSERT OR IGNORE INTO schema_migrations (version, name, checksum, description) VALUES
    ('1.0.0', 'initial_schema', 'auto-init', 'Initial schema with two-level state management');

-- ============================================================================
-- Views for Convenience (Optional)
-- ============================================================================

-- View: Model evaluations with use case info
CREATE VIEW IF NOT EXISTS v_model_evaluations AS
SELECT
    m.id,
    m.model_name,
    m.version,
    m.current_state,
    m.created_at,
    m.updated_at,
    u.id as use_case_id,
    u.name as use_case_name,
    u.team_email,
    u.state as use_case_state
FROM model_evaluations m
JOIN use_cases u ON m.use_case_id = u.id;

-- View: Latest state transitions per model
CREATE VIEW IF NOT EXISTS v_latest_model_states AS
SELECT
    msh.model_id,
    msh.to_state as current_state,
    msh.triggered_by,
    msh.timestamp,
    m.model_name,
    m.version
FROM model_state_history msh
JOIN model_evaluations m ON msh.model_id = m.id
WHERE msh.id IN (
    SELECT id
    FROM model_state_history
    WHERE model_id = msh.model_id
    ORDER BY timestamp DESC
    LIMIT 1
);

-- View: Models needing action (blocked states)
CREATE VIEW IF NOT EXISTS v_models_needing_action AS
SELECT
    m.id,
    m.model_name,
    m.version,
    m.current_state,
    u.name as use_case_name,
    u.team_email,
    m.updated_at
FROM model_evaluations m
JOIN use_cases u ON m.use_case_id = u.id
WHERE m.current_state IN (
    'awaiting_data_fix',
    'quality_check_failed',
    'evaluation_failed'
)
ORDER BY m.updated_at DESC;
