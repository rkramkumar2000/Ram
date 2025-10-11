"""Example prompt format for LLM SQL generation."""

EXAMPLE_PROMPT = """
System: You are a careful SQL DDL generator. Output only valid MySQL DDL statements in a single code block. Do not output explanations.

User:
Table name: customers
Existing columns (in repo): [{"name":"id","datatype":"INT","nullable":false,"primary":true},{"name":"name","datatype":"VARCHAR(255)","nullable":true}]
Columns from Google Sheet: [{"name":"id"},{"name":"name"},{"name":"email","datatype":"VARCHAR(255)","nullable":true},{"name":"created_at"}]

Rules:
1) If the table does not exist -> generate CREATE TABLE.
2) If exists -> generate ALTER TABLE statements to ADD missing columns only.
3) Infer datatypes for columns without datatype (created_at -> DATETIME).
4) Use IF NOT EXISTS or conditional checks to avoid errors.
5) Output only SQL inside a single ```sql ... ``` code fence.

Example output:
```sql
ALTER TABLE customers
  ADD COLUMN email VARCHAR(255) NULL,
  ADD COLUMN created_at DATETIME NULL;
```
"""