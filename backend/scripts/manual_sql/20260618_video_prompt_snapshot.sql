ALTER TABLE video_tasks
ADD COLUMN IF NOT EXISTS prompt_snapshot_json TEXT;

ALTER TABLE video_tasks
DROP COLUMN IF EXISTS system_prompt_snapshot,
DROP COLUMN IF EXISTS task_prompt_snapshot,
DROP COLUMN IF EXISTS user_prompt,
DROP COLUMN IF EXISTS prompt_template_refs_json;
