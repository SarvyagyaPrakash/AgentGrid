-- DDL schema for AgentGrid Database Tables

-- Cameras Table
CREATE TABLE IF NOT EXISTS cameras (
    camera_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    rtsp_url TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event Log Table
CREATE TABLE IF NOT EXISTS event_log (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(255) REFERENCES cameras(camera_id) ON DELETE CASCADE,
    agent VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    confidence DOUBLE PRECISION,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agent Configs Table
CREATE TABLE IF NOT EXISTS agent_configs (
    camera_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (camera_id, agent_name)
);
