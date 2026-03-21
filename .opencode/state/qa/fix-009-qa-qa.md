# QA Verification: FIX-009

## Summary
QA verification for FIX-009: Align write_markdown interface with spec contract.

## Acceptance Criteria Results

| Acceptance Criterion | Result |
|---|---|
| Mode parameter with create_or_overwrite/no_overwrite | PASS |
| Parameter names align with spec (write_target) | PASS |
| Atomic write and SHA256 verification preserved | PASS |

## Detailed Verification

### Criterion 1: Mode parameter with create_or_overwrite and no_overwrite options

- **markdown.py (lines 33-43, 87-88)**: Handler signature includes `mode: str = "create_or_overwrite"`, with validation at line 87-88 that rejects invalid modes.
- **__init__.py (lines 413-418)**: Schema defines `"mode"` parameter with enum `["create_or_overwrite", "no_overwrite"]` and default `"create_or_overwrite"`.
- **executor.py (lines 428, 460-464, 505)**: Node agent `write_file` method accepts mode parameter and implements no_overwrite logic, returning `"created": not file_existed` flag.

**Result: PASS**

### Criterion 2: Parameter names align with spec (write_target instead of repo_id)

- **markdown.py**: Function signature (lines 33-43) uses `node`, `write_target`, `relative_path`, `content`, `mode` - matching spec.
- **__init__.py (lines 397-420)**: Schema parameters are `"node"`, `"write_target"`, `"relative_path"`, `"content"`, `"mode"` - matching spec.
- The old parameters `node_id` and `repo_id` have been replaced with `node` and `write_target`.

**Result: PASS**

### Criterion 3: Existing atomic write and SHA256 verification logic is preserved

- **executor.py (lines 469-471)**: SHA256 hash computed before write: `sha256_hash = hashlib.sha256(content_bytes).hexdigest()`
- **executor.py (lines 473-490)**: Atomic write via temp file + `os.replace()`:
  ```python
  with tempfile.NamedTemporaryFile(...) as tmp_file:
      tmp_path = tmp_file.name
      tmp_file.write(content)
  os.replace(tmp_path, validated_path)
  ```
- **executor.py (lines 499-506)**: Response includes verification metadata: `sha256_hash`, `verified`, `content_hash_algorithm`, `bytes_written`, and `created` flag.
- **markdown.py (lines 181-186, 213-223)**: Hub handler passes mode to node client and returns all verification metadata to caller.

**Result: PASS**

## Overall: PASS

The FIX-009 implementation correctly:
1. Added `mode` parameter with both options and proper validation
2. Renamed parameters to align with spec (`write_target` instead of `repo_id`)
3. Preserved the existing atomic write with SHA256 verification