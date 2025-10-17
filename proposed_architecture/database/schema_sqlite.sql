-- SQLite Schema for Evaluation System
-- Adapted from PostgreSQL schema for SQLite compatibility
-- Updated to support two-level state management: Use Case + Model

-- ============================================================================
-- Stakeholder Management Tables
-- ============================================================================

-- Stakeholders table - Reusable across use cases
CREATE TABLE IF NOT EXISTS stakeholders (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT,  -- General role: 'data_scientist', 'ml_engineer', 'reviewer'
    department TEXT,
    notification_enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ============================================================================
-- Use Case Tables
-- ============================================================================

-- Use cases table
CREATE TABLE IF NOT EXISTS use_cases (
    id TEXT PRIMARY KEY,  -- UUID stored as TEXT
    name TEXT NOT NULL,
    state TEXT NOT NULL,  -- UseCaseState enum (template_generation, awaiting_config, etc.)
    config_file_path TEXT,  -- Local path or S3 key
    dataset_file_path TEXT,  -- Local path or S3 key (deprecated - moved to model level)
    metadata TEXT DEFAULT '{}',  -- JSON stored as TEXT
    created_at TEXT DEFAULT (datetime('now')),  -- ISO8601 timestamp
    updated_at TEXT DEFAULT (datetime('now'))
    -- Note: team_email removed - use use_case_stakeholders table instead
);

-- Use case stakeholders junction table (many-to-many)
CREATE TABLE IF NOT EXISTS use_case_stakeholders (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    role_in_use_case TEXT NOT NULL,  -- Specific role: 'Project Owner', 'Contributor', 'Reviewer'
    is_primary_contact INTEGER DEFAULT 0,  -- 1 for primary contact
    permissions TEXT DEFAULT '{}',  -- JSON: {'can_upload': true, 'can_approve': false}
    added_at TEXT DEFAULT (datetime('now')),
    added_by TEXT,  -- Who added this stakeholder
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    UNIQUE(use_case_id, stakeholder_id)  -- No duplicate stakeholders per use case
);

-- Stakeholder notification history table
CREATE TABLE IF NOT EXISTS stakeholder_notifications (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    stakeholder_id TEXT NOT NULL,
    model_id TEXT,  -- Optional: if notification is model-specific
    notification_type TEXT NOT NULL,  -- 'qc_failed', 'eval_complete', 'awaiting_config', etc.
    sent_at TEXT DEFAULT (datetime('now')),
    status TEXT NOT NULL,  -- 'sent', 'failed', 'bounced'
    email_subject TEXT,
    error_message TEXT,  -- If sending failed
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES model_evaluations(id) ON DELETE CASCADE
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
-- Model Configuration Table
-- ============================================================================

-- Models table (ML model configurations - reusable across use cases)
-- Uses composite primary key (model_id, version) for versioning
CREATE TABLE IF NOT EXISTS models (
    model_id TEXT NOT NULL,  -- Logical model ID: 'gpt-4', 'claude-3-sonnet'
    version TEXT NOT NULL,   -- Version: 'v1.0', 'v2.0', '2024-04-09', etc.
    name TEXT NOT NULL,      -- Display name: 'GPT-4 Turbo', 'Claude-3-Sonnet'
    model_type TEXT NOT NULL,  -- 'azure_openai', 'bedrock', 'local'
    provider TEXT,           -- 'openai', 'anthropic', 'meta', etc.
    config TEXT NOT NULL,    -- JSON: endpoint, api_key_ref, region, parameters, etc.
    is_active INTEGER DEFAULT 1,
    is_latest INTEGER DEFAULT 0,  -- Flag for latest version of this model_id
    description TEXT,
    changelog TEXT,          -- What changed in this version
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    PRIMARY KEY (model_id, version),
    UNIQUE(name, version)  -- Ensure unique display name per version
);

-- ============================================================================
-- Model Evaluation Tables (Two-level state management)
-- ============================================================================

-- Model evaluations table - Links a model version to a use case for evaluation
CREATE TABLE IF NOT EXISTS model_evaluations (
    id TEXT PRIMARY KEY,
    use_case_id TEXT NOT NULL,
    model_id TEXT NOT NULL,     -- Logical model ID (part of composite FK)
    model_version TEXT NOT NULL, -- Model version (part of composite FK)
    current_state TEXT NOT NULL, -- ModelEvaluationState enum
    dataset_file_path TEXT,      -- Dataset specific to this evaluation
    predictions_file_path TEXT,  -- Model predictions file
    quality_issues TEXT,         -- JSON array of quality issues
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}',  -- JSON for additional info
    FOREIGN KEY (use_case_id) REFERENCES use_cases(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id, model_version) REFERENCES models(model_id, version) ON DELETE RESTRICT,
    UNIQUE(use_case_id, model_id, model_version)  -- One evaluation per model version per use case
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
-- Evaluation Results Table
-- ============================================================================

-- Evaluation results table - Stores actual evaluation metrics and results
CREATE TABLE IF NOT EXISTS evaluation_results (
    id TEXT PRIMARY KEY,
    model_evaluation_id TEXT NOT NULL,  -- Links to model_evaluations (NOT models!)
    status TEXT NOT NULL,  -- 'queued', 'running', 'completed', 'failed'
    result_file_path TEXT,  -- S3 key or local path for detailed results

    -- Metrics (JSON or individual columns - using JSON for flexibility)
    metrics TEXT,  -- JSON: {"accuracy": 0.95, "precision": 0.92, "recall": 0.89, "f1": 0.90}

    -- Additional evaluation data
    predictions_count INTEGER,  -- Number of predictions evaluated
    correct_predictions INTEGER,  -- Number of correct predictions

    -- Timing
    started_at TEXT,
    completed_at TEXT,
    duration_seconds INTEGER,  -- Calculated: completed_at - started_at

    -- Error handling
    error_message TEXT,
    error_traceback TEXT,

    -- Metadata
    evaluator_version TEXT,  -- Version of evaluation code used
    metadata TEXT DEFAULT '{}',  -- JSON for custom metrics or info
    created_at TEXT DEFAULT (datetime('now')),

    FOREIGN KEY (model_evaluation_id) REFERENCES model_evaluations(id) ON DELETE CASCADE
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

-- Stakeholder indexes
CREATE INDEX IF NOT EXISTS idx_stakeholders_email ON stakeholders(email);
CREATE INDEX IF NOT EXISTS idx_stakeholders_role ON stakeholders(role);

-- Use case stakeholder indexes
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_use_case ON use_case_stakeholders(use_case_id);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_stakeholder ON use_case_stakeholders(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_use_case_stakeholders_primary ON use_case_stakeholders(use_case_id, is_primary_contact);

-- Stakeholder notification indexes
CREATE INDEX IF NOT EXISTS idx_stakeholder_notifications_use_case ON stakeholder_notifications(use_case_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_notifications_stakeholder ON stakeholder_notifications(stakeholder_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_notifications_model ON stakeholder_notifications(model_id);
CREATE INDEX IF NOT EXISTS idx_stakeholder_notifications_type ON stakeholder_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_stakeholder_notifications_status ON stakeholder_notifications(status);

-- Use case indexes
CREATE INDEX IF NOT EXISTS idx_use_cases_state ON use_cases(state);
CREATE INDEX IF NOT EXISTS idx_use_cases_created_at ON use_cases(created_at);

-- Use case state history indexes
CREATE INDEX IF NOT EXISTS idx_use_case_state_history_use_case ON use_case_state_history(use_case_id);
CREATE INDEX IF NOT EXISTS idx_use_case_state_history_timestamp ON use_case_state_history(timestamp);

-- Model configuration indexes
CREATE INDEX IF NOT EXISTS idx_models_model_id ON models(model_id);
CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_type ON models(model_type);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);
CREATE INDEX IF NOT EXISTS idx_models_latest ON models(model_id, is_latest);

-- Model evaluation indexes
CREATE INDEX IF NOT EXISTS idx_model_evaluations_use_case ON model_evaluations(use_case_id);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_model ON model_evaluations(model_id);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_model_version ON model_evaluations(model_id, model_version);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_state ON model_evaluations(current_state);
CREATE INDEX IF NOT EXISTS idx_model_evaluations_use_case_model ON model_evaluations(use_case_id, model_id);

-- Model state history indexes
CREATE INDEX IF NOT EXISTS idx_model_state_history_model ON model_state_history(model_id);
CREATE INDEX IF NOT EXISTS idx_model_state_history_timestamp ON model_state_history(timestamp);
CREATE INDEX IF NOT EXISTS idx_model_state_history_state ON model_state_history(to_state);

-- Quality check indexes
CREATE INDEX IF NOT EXISTS idx_quality_check_model ON quality_check_results(model_id);
CREATE INDEX IF NOT EXISTS idx_quality_check_passed ON quality_check_results(passed);

-- Evaluation results indexes
CREATE INDEX IF NOT EXISTS idx_evaluation_results_model_eval ON evaluation_results(model_evaluation_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_status ON evaluation_results(status);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_created ON evaluation_results(created_at);

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

CREATE TRIGGER IF NOT EXISTS update_stakeholders_timestamp
AFTER UPDATE ON stakeholders
BEGIN
    UPDATE stakeholders SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_use_cases_timestamp
AFTER UPDATE ON use_cases
BEGIN
    UPDATE use_cases SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_models_timestamp
AFTER UPDATE ON models
BEGIN
    UPDATE models SET updated_at = datetime('now')
    WHERE model_id = NEW.model_id AND version = NEW.version;
END;

CREATE TRIGGER IF NOT EXISTS update_model_evaluations_timestamp
AFTER UPDATE ON model_evaluations
BEGIN
    UPDATE model_evaluations SET updated_at = datetime('now') WHERE id = NEW.id;
END;

-- Trigger to automatically set is_latest flag for models
-- When a new version is inserted, unset is_latest for all older versions
CREATE TRIGGER IF NOT EXISTS update_model_latest_flag
AFTER INSERT ON models
WHEN NEW.is_latest = 1
BEGIN
    -- Unset is_latest for all other versions of this model_id
    UPDATE models
    SET is_latest = 0
    WHERE model_id = NEW.model_id
      AND version != NEW.version;
END;

-- ============================================================================
-- Default Data (Optional)
-- ============================================================================

-- Insert default models with versioning (optional)
INSERT OR IGNORE INTO models (model_id, version, name, model_type, provider, config, is_active, is_latest, description, changelog) VALUES
    -- GPT-4 Turbo versions
    ('gpt-4-turbo', 'v1.0', 'GPT-4-Turbo v1.0', 'azure_openai', 'openai',
     '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-4-turbo", "api_version": "2024-02-01"}',
     1, 0, 'GPT-4 Turbo with vision capabilities', 'Initial version'),
    ('gpt-4-turbo', 'v2.0', 'GPT-4-Turbo v2.0', 'azure_openai', 'openai',
     '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-4-turbo", "api_version": "2024-04-01", "temperature": 0.7}',
     1, 1, 'GPT-4 Turbo with improved parameters', 'Updated temperature, newer API version'),

    -- Claude 3 Sonnet versions
    ('claude-3-sonnet', 'v1.0', 'Claude-3-Sonnet v1.0', 'bedrock', 'anthropic',
     '{"model_id": "anthropic.claude-3-sonnet-20240229-v1:0", "region": "us-east-1"}',
     1, 1, 'Claude 3 Sonnet - balanced performance', 'Initial version'),

    -- GPT-3.5 Turbo versions
    ('gpt-3.5-turbo', 'v1.0', 'GPT-3.5-Turbo v1.0', 'azure_openai', 'openai',
     '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-35-turbo"}',
     1, 0, 'Fast and cost-effective model', 'Initial version'),
    ('gpt-3.5-turbo', 'v1.1', 'GPT-3.5-Turbo v1.1', 'azure_openai', 'openai',
     '{"endpoint": "https://your-endpoint.openai.azure.com", "deployment": "gpt-35-turbo", "max_tokens": 4096}',
     1, 1, 'Fast and cost-effective model', 'Increased max_tokens to 4096');

-- Insert default stakeholder for demo/testing
INSERT OR IGNORE INTO stakeholders (id, email, name, role, notification_enabled) VALUES
    ('stakeholder_demo', 'demo@example.com', 'Demo User', 'data_scientist', 1);

-- Insert default use case for demo/testing
INSERT OR IGNORE INTO use_cases (id, name, state, created_at, updated_at) VALUES
    ('default_use_case', 'Demo Use Case', 'awaiting_config', datetime('now'), datetime('now'));

-- Link default stakeholder to default use case
INSERT OR IGNORE INTO use_case_stakeholders (id, use_case_id, stakeholder_id, role_in_use_case, is_primary_contact) VALUES
    ('ucs_demo', 'default_use_case', 'stakeholder_demo', 'Project Owner', 1);

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

-- View: Use cases with primary contact
CREATE VIEW IF NOT EXISTS v_use_cases_with_contact AS
SELECT
    u.id,
    u.name,
    u.state,
    u.config_file_path,
    u.created_at,
    u.updated_at,
    s.id as primary_contact_id,
    s.email as primary_contact_email,
    s.name as primary_contact_name,
    s.role as primary_contact_role
FROM use_cases u
LEFT JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id AND ucs.is_primary_contact = 1
LEFT JOIN stakeholders s ON ucs.stakeholder_id = s.id;

-- View: All stakeholders per use case
CREATE VIEW IF NOT EXISTS v_use_case_team AS
SELECT
    u.id as use_case_id,
    u.name as use_case_name,
    u.state as use_case_state,
    s.id as stakeholder_id,
    s.email,
    s.name as stakeholder_name,
    s.role as stakeholder_general_role,
    ucs.role_in_use_case,
    ucs.is_primary_contact,
    ucs.permissions,
    ucs.added_at
FROM use_cases u
JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id
JOIN stakeholders s ON ucs.stakeholder_id = s.id
ORDER BY u.name, ucs.is_primary_contact DESC, s.name;

-- View: Model evaluations with use case, model config, and primary contact
CREATE VIEW IF NOT EXISTS v_model_evaluations AS
SELECT
    me.id as evaluation_id,
    me.current_state,
    me.created_at,
    me.updated_at,
    u.id as use_case_id,
    u.name as use_case_name,
    u.state as use_case_state,
    me.model_id,
    me.model_version,
    m.name as model_name,
    m.model_type,
    m.provider,
    m.is_latest,
    s.email as primary_contact_email,
    s.name as primary_contact_name
FROM model_evaluations me
JOIN use_cases u ON me.use_case_id = u.id
JOIN models m ON me.model_id = m.model_id AND me.model_version = m.version
LEFT JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id AND ucs.is_primary_contact = 1
LEFT JOIN stakeholders s ON ucs.stakeholder_id = s.id;

-- View: Latest state transitions per model evaluation
CREATE VIEW IF NOT EXISTS v_latest_model_states AS
SELECT
    msh.model_id as evaluation_id,
    msh.to_state as current_state,
    msh.triggered_by,
    msh.timestamp,
    me.use_case_id,
    me.model_id,
    me.model_version,
    m.name as model_name
FROM model_state_history msh
JOIN model_evaluations me ON msh.model_id = me.id
JOIN models m ON me.model_id = m.model_id AND me.model_version = m.version
WHERE msh.id IN (
    SELECT id
    FROM model_state_history
    WHERE model_id = msh.model_id
    ORDER BY timestamp DESC
    LIMIT 1
);

-- View: Models needing action (blocked states) with primary contact
CREATE VIEW IF NOT EXISTS v_models_needing_action AS
SELECT
    me.id as evaluation_id,
    me.model_id,
    me.model_version,
    m.name as model_name,
    me.current_state,
    u.name as use_case_name,
    s.email as primary_contact_email,
    s.name as primary_contact_name,
    me.updated_at
FROM model_evaluations me
JOIN use_cases u ON me.use_case_id = u.id
JOIN models m ON me.model_id = m.model_id AND me.model_version = m.version
LEFT JOIN use_case_stakeholders ucs ON u.id = ucs.use_case_id AND ucs.is_primary_contact = 1
LEFT JOIN stakeholders s ON ucs.stakeholder_id = s.id
WHERE me.current_state IN (
    'awaiting_data_fix',
    'quality_check_failed',
    'evaluation_failed'
)
ORDER BY me.updated_at DESC;

-- View: Evaluation results with model and use case info
CREATE VIEW IF NOT EXISTS v_evaluation_results AS
SELECT
    er.id as result_id,
    er.status as eval_status,
    er.metrics,
    er.predictions_count,
    er.correct_predictions,
    er.started_at,
    er.completed_at,
    er.duration_seconds,
    me.id as evaluation_id,
    me.current_state as evaluation_state,
    me.model_id,
    me.model_version,
    u.id as use_case_id,
    u.name as use_case_name,
    m.name as model_name,
    m.provider,
    m.is_latest
FROM evaluation_results er
JOIN model_evaluations me ON er.model_evaluation_id = me.id
JOIN use_cases u ON me.use_case_id = u.id
JOIN models m ON me.model_id = m.model_id AND me.model_version = m.version;

-- View: Latest version of each model
CREATE VIEW IF NOT EXISTS v_latest_models AS
SELECT
    model_id,
    version,
    name,
    model_type,
    provider,
    config,
    description,
    created_at,
    updated_at
FROM models
WHERE is_latest = 1;

-- View: Model version history
CREATE VIEW IF NOT EXISTS v_model_version_history AS
SELECT
    model_id,
    version,
    name,
    model_type,
    provider,
    is_latest,
    is_active,
    changelog,
    created_at
FROM models
ORDER BY model_id, created_at DESC;
