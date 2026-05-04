

-- create databas(service) + schema(user) =  freepdb1 : PDBADMIN

--Create a new DBeaver connection as SYSTEM (not PDBADMIN) and run the grants:
GRANT CREATE TABLE TO PDBADMIN;
GRANT UNLIMITED TABLESPACE TO PDBADMIN;


-- Run this once per environment (local, cloud) to set up schema
-- Connect to freepdb1 as PDBADMIN before running

CREATE TABLE game_sessions (
    session_id      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    play_started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    final_score     NUMBER(10, 0)            NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT SYS_EXTRACT_UTC(SYSTIMESTAMP) NOT NULL,
    CONSTRAINT chk_score_non_negative CHECK (final_score >= 0)
);

CREATE INDEX idx_game_sessions_started ON game_sessions (play_started_at);