ALTER TABLE image_tasks
ADD COLUMN IF NOT EXISTS prompt_snapshot_json TEXT;

-- MVP 新结构只读 prompt_snapshot_json；确认旧数据不需要保留后可执行下面的清理。
ALTER TABLE image_tasks
DROP COLUMN IF EXISTS edit_instruction,
DROP COLUMN IF EXISTS system_prompt_snapshot,
DROP COLUMN IF EXISTS task_prompt_snapshot,
DROP COLUMN IF EXISTS user_prompt,
DROP COLUMN IF EXISTS prompt_template_refs_json;
