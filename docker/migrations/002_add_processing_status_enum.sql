-- Migration: Add ProcessingStatus enum type to database
-- This creates the enum type needed for the processing_queue table

-- Create the enum type if it doesn't exist
DO $$ BEGIN
    CREATE TYPE processingstatus AS ENUM ('pending', 'extracting', 'summarizing', 'embedding', 'completed', 'failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- If the type already exists, add any missing values
-- This handles the case where the enum exists but is incomplete
DO $$ BEGIN
    ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'extracting';
    ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'summarizing';
    ALTER TYPE processingstatus ADD VALUE IF NOT EXISTS 'embedding';
EXCEPTION
    WHEN duplicate_object THEN null;
    WHEN invalid_schema_name THEN null;
END $$;
