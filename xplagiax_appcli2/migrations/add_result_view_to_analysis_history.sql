-- Adds the result_view column used by the "analysiss" history to reopen an
-- analysis in its document (result.html) view instead of plain text.
-- Safe to run once; the application also self-heals this column at runtime.
ALTER TABLE analysis_history ADD COLUMN result_view VARCHAR(512) NULL;
