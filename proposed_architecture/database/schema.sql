-- PostgreSQL database schema for evaluation system

-- Use cases table
CREATE TABLE IF NOT EXISTS use_cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    team_email VARCHAR(255) NOT NULL,
    state VARCHAR(50) NOT NULL,
    config_file_path VARCHAR(500),
    dataset_file_path VARCHAR(500),
    quality_issues JSONB,
    evaluation_results JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Models table
CREATE TABLE IF NOT EXISTS models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(use_case_id, model_name, version)
);

-- State transitions audit log
CREATE TABLE IF NOT EXISTS state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    from_state VARCHAR(50),
    to_state VARCHAR(50) NOT NULL,
    triggered_by VARCHAR(100),
    trigger_reason TEXT,
    metadata JSONB DEFAULT '{}',
    transitioned_at TIMESTAMP DEFAULT NOW()
);

-- Evaluation results table
CREATE TABLE IF NOT EXISTS evaluation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    team VARCHAR(10) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    classification_metrics JSONB,
    agreement_rate FLOAT,
    metadata JSONB DEFAULT '{}',
    evaluated_at TIMESTAMP DEFAULT NOW()
);

-- Activity log table
CREATE TABLE IF NOT EXISTS activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    use_case_id UUID REFERENCES use_cases(id) ON DELETE CASCADE,
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_use_cases_state ON use_cases(state);
CREATE INDEX IF NOT EXISTS idx_use_cases_team_email ON use_cases(team_email);
CREATE INDEX IF NOT EXISTS idx_use_cases_created_at ON use_cases(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_use_cases_updated_at ON use_cases(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_models_use_case_id ON models(use_case_id);

CREATE INDEX IF NOT EXISTS idx_state_transitions_use_case ON state_transitions(use_case_id);
CREATE INDEX IF NOT EXISTS idx_state_transitions_time ON state_transitions(transitioned_at DESC);

CREATE INDEX IF NOT EXISTS idx_evaluation_results_use_case ON evaluation_results(use_case_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_results_model ON evaluation_results(model_id);

CREATE INDEX IF NOT EXISTS idx_activity_log_use_case ON activity_log(use_case_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_time ON activity_log(created_at DESC);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_use_cases_updated_at ON use_cases;
CREATE TRIGGER update_use_cases_updated_at
    BEFORE UPDATE ON use_cases
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE use_cases IS 'Main table storing evaluation use cases';
COMMENT ON COLUMN use_cases.state IS 'Current state in workflow state machine';
COMMENT ON COLUMN use_cases.quality_issues IS 'JSON array of quality issues found during validation';
COMMENT ON COLUMN use_cases.evaluation_results IS 'JSON object containing evaluation metrics';

COMMENT ON TABLE models IS 'Models being evaluated for each use case';

COMMENT ON TABLE state_transitions IS 'Audit trail of all state transitions';

COMMENT ON TABLE evaluation_results IS 'Detailed evaluation results per model and team';

COMMENT ON TABLE activity_log IS 'General activity log for tracking all actions';
