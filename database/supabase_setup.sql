-- ============================================
-- HealthLog AI - Supabase Database Setup
-- ============================================
-- Run this in Supabase SQL Editor to create all tables
-- Go to: https://supabase.com/dashboard/project/YOUR_PROJECT/sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id TEXT UNIQUE,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- ============================================
-- MEAL LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS meal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_path TEXT,
    description TEXT,
    calories INTEGER DEFAULT 0,
    protein REAL DEFAULT 0,
    carbs REAL DEFAULT 0,
    fat REAL DEFAULT 0,
    fiber REAL DEFAULT 0,
    meal_type TEXT CHECK (meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')),
    ai_analysis JSONB DEFAULT '{}',
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_meal_logs_user_id ON meal_logs(user_id);
CREATE INDEX idx_meal_logs_logged_at ON meal_logs(logged_at);

ALTER TABLE meal_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- SYMPTOM LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS symptom_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symptom TEXT NOT NULL,
    severity INTEGER CHECK (severity >= 1 AND severity <= 10),
    notes TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_symptom_logs_user_id ON symptom_logs(user_id);
CREATE INDEX idx_symptom_logs_logged_at ON symptom_logs(logged_at);

ALTER TABLE symptom_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- MEDICATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    reminder_times JSONB DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_medications_user_id ON medications(user_id);

ALTER TABLE medications ENABLE ROW LEVEL SECURITY;

-- ============================================
-- MEDICATION LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS medication_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    medication_id UUID NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    taken_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    skipped BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_medication_logs_user_id ON medication_logs(user_id);
CREATE INDEX idx_medication_logs_taken_at ON medication_logs(taken_at);

ALTER TABLE medication_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- DAILY SCORES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS daily_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),
    mood_level INTEGER CHECK (mood_level >= 1 AND mood_level <= 10),
    sleep_hours REAL CHECK (sleep_hours >= 0 AND sleep_hours <= 24),
    water_intake INTEGER CHECK (water_intake >= 0),
    exercise_minutes INTEGER CHECK (exercise_minutes >= 0),
    notes TEXT,
    UNIQUE(user_id, date)
);

CREATE INDEX idx_daily_scores_user_id ON daily_scores(user_id);
CREATE INDEX idx_daily_scores_date ON daily_scores(date);

ALTER TABLE daily_scores ENABLE ROW LEVEL SECURITY;

-- ============================================
-- ROW LEVEL SECURITY POLICIES
-- Users can only access their own data
-- ============================================

-- Users policies
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text OR auth.role() = 'service_role');

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Meal logs policies
CREATE POLICY "Users can view own meals" ON meal_logs
    FOR SELECT USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

CREATE POLICY "Users can insert own meals" ON meal_logs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- Symptom logs policies
CREATE POLICY "Users can view own symptoms" ON symptom_logs
    FOR SELECT USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

CREATE POLICY "Users can insert own symptoms" ON symptom_logs
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- Medications policies
CREATE POLICY "Users can manage own medications" ON medications
    FOR ALL USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- Medication logs policies
CREATE POLICY "Users can manage own medication logs" ON medication_logs
    FOR ALL USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- Daily scores policies
CREATE POLICY "Users can manage own daily scores" ON daily_scores
    FOR ALL USING (auth.uid()::text = user_id::text OR auth.role() = 'service_role');

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function to get medication adherence rate
CREATE OR REPLACE FUNCTION get_medication_adherence(p_user_id UUID, p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    total_logs BIGINT,
    taken_count BIGINT,
    skipped_count BIGINT,
    adherence_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_logs,
        COUNT(*) FILTER (WHERE NOT skipped) as taken_count,
        COUNT(*) FILTER (WHERE skipped) as skipped_count,
        CASE 
            WHEN COUNT(*) > 0 THEN ROUND((COUNT(*) FILTER (WHERE NOT skipped)::NUMERIC / COUNT(*)) * 100, 1)
            ELSE 0
        END as adherence_rate
    FROM medication_logs
    WHERE user_id = p_user_id 
    AND taken_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- DONE!
-- ============================================
-- Your database is now ready for HealthLog AI
