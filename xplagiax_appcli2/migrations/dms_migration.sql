-- DMS Database Migration Script
-- Run this in your MySQL client to add missing columns

-- Add is_trash column to folders table
ALTER TABLE folders ADD COLUMN is_trash BOOLEAN DEFAULT FALSE;

-- Add parent_id column to folders table (for hierarchical structure)
ALTER TABLE folders ADD COLUMN parent_id INT NULL;

-- Add is_trash column to files table
ALTER TABLE files ADD COLUMN is_trash BOOLEAN DEFAULT FALSE;

-- Add folder_id column to files table (for folder assignment)
ALTER TABLE files ADD COLUMN folder_id INT NULL;

-- Add other missing columns that may be needed
ALTER TABLE folders ADD COLUMN expires_at DATETIME NULL;
ALTER TABLE folders ADD COLUMN rules JSON NULL;
ALTER TABLE folders ADD COLUMN metadata_json JSON NULL;

-- Add file-related columns
ALTER TABLE files ADD COLUMN status VARCHAR(50) DEFAULT 'Borrador';
ALTER TABLE files ADD COLUMN is_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE files ADD COLUMN is_evidence BOOLEAN DEFAULT FALSE;
ALTER TABLE files ADD COLUMN expires_at DATETIME NULL;
ALTER TABLE files ADD COLUMN tags JSON NULL;
ALTER TABLE files ADD COLUMN version INT DEFAULT 1;
ALTER TABLE files ADD COLUMN description TEXT NULL;

-- Note: If any column already exists, you will get an error. 
-- You can ignore "Duplicate column name" errors.
