# Smoke Test

## Ticket

- EXEC-006

## Overall Result

Overall Result: FAIL

## Notes

The smoke-test run stopped on the first failing command. Inspect the recorded output before closeout.

## Commands

### 1. python compileall

- reason: Detected uv.lock; using repo-managed uv runtime; generic Python syntax smoke check
- command: `uv run python -m compileall -q -x (^|/)(\.git|\.opencode|node_modules|dist|build|out|venv|\.venv|__pycache__)(/|$) .`
- exit_code: 0
- duration_ms: 124

#### stdout

~~~~text
<no output>
~~~~

#### stderr

~~~~text
<no output>
~~~~

### 2. pytest

- reason: Detected uv.lock; using repo-managed uv runtime; detected Python test surface
- command: `uv run python -m pytest`
- exit_code: 1
- duration_ms: 2863

#### stdout

~~~~text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0
rootdir: /home/pc/projects/GPTTalker
configfile: pytest.ini (WARNING: ignoring pytest config in pyproject.toml!)
testpaths: tests
plugins: asyncio-1.3.0, anyio-4.12.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 127 items

tests/hub/test_contracts.py F.....F..F.......F..........F...             [ 25%]
tests/hub/test_routing.py ..............                                 [ 36%]
tests/hub/test_security.py F.......F.............F....                   [ 57%]
tests/hub/test_transport.py .............                                [ 67%]
tests/node_agent/test_executor.py ..FF..FFFF.F..........                 [ 85%]
tests/shared/test_logging.py .FF..............F.                         [100%]

=================================== FAILURES ===================================
________ TestDiscoveryTools.test_list_nodes_returns_structured_response ________

self = <tests.hub.test_contracts.TestDiscoveryTools object at 0x7a8b986f1ee0>
mock_node = <MagicMock id='134740254639888'>

    @pytest.mark.asyncio
    async def test_list_nodes_returns_structured_response(self, mock_node):
        """Test that list_nodes returns properly structured response."""
        # Create mock node repository
        mock_node_repo = MagicMock()
        mock_node_repo.list_all = AsyncMock(return_value=[mock_node])
        mock_node_repo.get_health = AsyncMock(
            return_value={
                "health_status": "healthy",
                "health_latency_ms": 10,
                "health_check_count": 5,
                "consecutive_failures": 0,
            }
        )
    
        # Call handler
>       result = await list_nodes_handler(node_repo=mock_node_repo)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/hub/test_contracts.py:177: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
src/hub/tools/discovery.py:33: in list_nodes_handler
    return await list_nodes_impl(node_repo)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

node_repo = <MagicMock id='134739973164400'>

    async def list_nodes_impl(
        node_repo: "NodeRepository",
    ) -> dict[str, Any]:
        """Internal implementation for list_nodes.
    
        Args:
            node_repo: NodeRepository instance.
    
        Returns:
            Node list response with health metadata.
        """
        start = int(time.time() * 1000)
    
        # Get all nodes
        nodes = await node_repo.list_all()
    
        nodes_data = []
        for node in nodes:
            # Get health metadata
            health = await node_repo.get_health(node.node_id)
    
            node_dict = {
                "node_id": node.node_id,
                "name": node.name,
                "hostname": node.hostname,
>               "status": node.status.value,
                          ^^^^^^^^^^^^^^^^^
                "last_seen": node.last_seen.isoformat() if node.last_seen else None,
                "health": {
                    "health_status": (health.get("health_status", NodeHealthStatus.UNKNOWN)).value
                    if health
                    else NodeHealthStatus.UNKNOWN.value,
                    "health_latency_ms": health.get("health_latency_ms") if health else None,
                    "health_error": health.get("health_error") if health else None,
                    "health_check_count": health.get("health_check_count", 0) if health else 0,
                    "consecutive_failures": health.get("consecutive_failures", 0) if health else 0,
                    "last_health_check": health.get("last_health_check").isoformat()
                    if health and health.get("last_health_check")
                    else None,
                    "last_health_attempt": health.get("last_health_attempt").isoformat()
                    if health and health.get("last_health_attempt")
                    else None,
                }
                if health
                else None,
            }
E           AttributeError: 'str' object has no attribute 'value'

src/hub/tools/discovery.py:61: AttributeError
______ TestInspectionTools.test_inspect_repo_tree_requires_node_and_repo _______

self = <tests.hub.test_contracts.TestInspectionTools object at 0x7a8b986f34a0>
mock_node_client = <MagicMock id='134739973176784'>
mock_node = <MagicMock id='134739973640112'>
mock_repo = <MagicMock id='134739973636848'>

    @pytest.mark.asyncio
    async def test_inspect_repo_tree_requires_node_and_repo(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that inspect_repo_tree validates node and repo parameters."""
        # Test with missing node_id
        result = await inspect_repo_tree_handler(
            node_id="",
            repo_id="test-repo-1",
            node_client=mock_node_client,
        )
        assert result["success"] is False
>       assert "not found" in result["error"].lower()
E       AssertionError: assert 'not found' in 'noderepository not available'
E        +  where 'noderepository not available' = <built-in method lower of str object at 0x7a8b986fc2b0>()
E        +    where <built-in method lower of str object at 0x7a8b986fc2b0> = 'NodeRepository not available'.lower

tests/hub/test_contracts.py:273: AssertionError
_________ TestInspectionTools.test_read_repo_file_requires_parameters __________

self = <tests.hub.test_contracts.TestInspectionTools object at 0x7a8b986f2e40>
mock_node_client = <MagicMock id='134739971824944'>

    @pytest.mark.asyncio
    async def test_read_repo_file_requires_parameters(
        self,
        mock_node_client,
    ):
        """Test that read_repo_file validates required parameters."""
        # Test with missing file_path
        result = await read_repo_file_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            file_path="",
            node_client=mock_node_client,
        )
        assert result["success"] is False
>       assert "not found" in result["error"].lower()
E       AssertionError: assert 'not found' in 'noderepository not available'
E        +  where 'noderepository not available' = <built-in method lower of str object at 0x7a8b986fc2b0>()
E        +    where <built-in method lower of str object at 0x7a8b986fc2b0> = 'NodeRepository not available'.lower

tests/hub/test_contracts.py:347: AssertionError
____________ TestWriteTools.test_write_markdown_validates_extension ____________

self = <tests.hub.test_contracts.TestWriteTools object at 0x7a8b987213d0>
mock_node_client = <MagicMock id='134739973516336'>
mock_node = <MagicMock id='134739973577408'>
mock_repo = <MagicMock id='134739973573472'>

    @pytest.mark.asyncio
    async def test_write_markdown_validates_extension(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that write_markdown validates file extensions."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)
    
        mock_write_target_repo = MagicMock()
        mock_write_target_policy = MagicMock()
        mock_write_target_policy.list_write_targets_for_repo = AsyncMock(
            return_value=[mock_write_target]
        )
    
        # Try to write a file with disallowed extension
>       result = await write_markdown_handler(
            node_id="test-node-1",
            repo_id="test-repo-1",
            path="script.py",  # .py not in allowed extensions
            content="# Python script",
            node_client=mock_node_client,
            node_repo=mock_node_repo,
            write_target_repo=mock_write_target_repo,
            write_target_policy=mock_write_target_policy,
        )

tests/hub/test_contracts.py:562: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

node_id = 'test-node-1', repo_id = 'test-repo-1', path = 'script.py'
content = '# Python script', mode = 'create_or_overwrite'
node_client = <MagicMock id='134739973516336'>
node_repo = <MagicMock id='134739973651920'>
write_target_repo = <MagicMock id='134739973269808'>
write_target_policy = <MagicMock id='134739973272496'>

    async def write_markdown_handler(
        node_id: str,
        repo_id: str,
        path: str,
        content: str,
        mode: str = "create_or_overwrite",
        node_client: "HubNodeClient | None" = None,
        node_repo: "NodeRepository | None" = None,
        write_target_repo: "WriteTargetRepository | None" = None,
        write_target_policy: "WriteTargetPolicy | None" = None,
    ) -> dict[str, Any]:
        """Write markdown content to an approved write target.
    
        This tool provides controlled markdown delivery to approved write targets.
        It validates:
        - Node exists and is accessible
        - Write target is registered and approved
        - Write target path is within allowed boundaries
        - File extension is in the allowlist for the target
        - Path doesn't contain traversal attempts
    
        The write is performed atomically with SHA256 verification.
    
        Args:
            node_id: Target node identifier (required).
            repo_id: Repo identifier (required).
            path: File path relative to write target root (required).
            content: Markdown content to write (required).
            mode: Write mode - "create_or_overwrite" (default) or "no_overwrite".
            node_client: HubNodeClient for node communication.
            node_repo: NodeRepository for node lookup.
            write_target_repo: WriteTargetRepository for write target lookup.
            write_target_policy: WriteTargetPolicy for write access validation.
    
        Returns:
            Dict with write result and verification metadata.
        """
        start = int(time.time() * 1000)
    
        # Check dependencies
        if node_client is None:
            return {"success": False, "error": "Node client not available"}
        if node_repo is None:
            return {"success": False, "error": "NodeRepository not available"}
        if write_target_repo is None:
            return {"success": False, "error": "WriteTargetRepository not available"}
        if write_target_policy is None:
            return {"success": False, "error": "WriteTargetPolicy not available"}
    
        # Validate inputs
        if not path:
            return {"success": False, "error": "path parameter is required"}
        if not content:
            return {"success": False, "error": "content parameter is required"}
        if mode not in ("create_or_overwrite", "no_overwrite"):
            return {"success": False, "error": "mode must be 'create_or_overwrite' or 'no_overwrite'"}
    
        # Validate node exists
        node_obj = await node_repo.get(node_id)
        if not node_obj:
            logger.warning("write_markdown_node_not_found", node_id=node_id)
            return {"success": False, "error": f"Node not found: {node_id}"}
    
        # Get write target by ID
        targets = await write_target_policy.list_write_targets_for_repo(repo_id)
        if not targets:
            logger.warning(
                "write_markdown_no_write_target",
                repo_id=repo_id,
                node_id=node_id,
            )
            return {
                "success": False,
                "error": f"No write targets found for repo: {repo_id}",
            }
        allowed_target = targets[0]
    
        # Extract extension and validate
        extension = _get_extension(path)
    
        # Validate extension is allowed for this write target
>       if extension not in allowed_target.allowed_extensions:
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       AttributeError: 'FixtureFunctionDefinition' object has no attribute 'allowed_extensions'

src/hub/tools/markdown.py:114: AttributeError
_________________ TestFailureModes.test_invalid_path_rejected __________________

self = <tests.hub.test_contracts.TestFailureModes object at 0x7a8b987224e0>
mock_node_client = <MagicMock id='134739973169200'>
mock_node = <MagicMock id='134739971944864'>
mock_repo = <MagicMock id='134739971940976'>

    @pytest.mark.asyncio
    async def test_invalid_path_rejected(
        self,
        mock_node_client,
        mock_node,
        mock_repo,
    ):
        """Test that invalid paths are rejected."""
        mock_node_repo = MagicMock()
        mock_node_repo.get = AsyncMock(return_value=mock_node)
    
        mock_repo_repo = MagicMock()
        mock_repo_repo.get = AsyncMock(return_value=mock_repo)
    
        # Try various path traversal attempts
        invalid_paths = [
            "../../../etc/passwd",
            "/absolute/path",
            "foo/../../bar",
            "foo/./bar",
        ]
    
        for invalid_path in invalid_paths:
            result = await read_repo_file_handler(
                node_id="test-node-1",
                repo_id="test-repo-1",
                file_path=invalid_path,
                node_client=mock_node_client,
                node_repo=mock_node_repo,
                repo_repo=mock_repo_repo,
            )
            # Path should either be rejected or validated
>           assert (
                result.get("success") is False
                or "validation failed" in result.get("error", "").lower()
            )
E           AssertionError: assert (True is False or 'validation failed' in '')
E            +  where True = <built-in method get of dict object at 0x7a8b98175080>('success')
E            +    where <built-in method get of dict object at 0x7a8b98175080> = {'bytes_read': 18, 'content': 'Test file content', 'encoding': 'utf-8', 'file_path': 'foo/./bar', ...}.get
E            +  and   '' = <built-in method lower of str object at 0xb3b3f0>()
E            +    where <built-in method lower of str object at 0xb3b3f0> = ''.lower
E            +      where '' = <built-in method get of dict object at 0x7a8b98175080>('error', '')
E            +        where <built-in method get of dict object at 0x7a8b98175080> = {'bytes_read': 18, 'content': 'Test file content', 'encoding': 'utf-8', 'file_path': 'foo/./bar', ...}.get

tests/hub/test_contracts.py:857: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  src.hub.tools.inspection:logging.py:275 read_repo_file_path_validation_failed
WARNING  src.hub.tools.inspection:logging.py:275 read_repo_file_path_validation_failed
WARNING  src.hub.tools.inspection:logging.py:275 read_repo_file_path_validation_failed
____________ TestPathTraversal.test_path_traversal_dotdot_rejected _____________

self = <tests.hub.test_security.TestPathTraversal object at 0x7a8b98722210>

    def test_path_traversal_dotdot_rejected(self):
        """Test that .. path traversal is rejected."""
        base = "/home/user/repo"
    
        # Attempt various .. patterns
        dangerous_paths = [
            "../etc/passwd",
            "../../../../etc/passwd",
            "foo/../../../etc/passwd",
            "foo/bar/../../secrets",
            "../foo/bar",
            "foo/..",
            "....",
            ".../...",
        ]
    
        for path in dangerous_paths:
            with pytest.raises(PathTraversalError) as exc_info:
                PathNormalizer.normalize(path, base)
>           assert "traversal" in str(exc_info.value).lower()
E           assert 'traversal' in "path '../etc/passwd' escapes base directory '/home/user/repo'"
E            +  where "path '../etc/passwd' escapes base directory '/home/user/repo'" = <built-in method lower of str object at 0x7a8b982b1680>()
E            +    where <built-in method lower of str object at 0x7a8b982b1680> = "Path '../etc/passwd' escapes base directory '/home/user/repo'".lower
E            +      where "Path '../etc/passwd' escapes base directory '/home/user/repo'" = str(PathTraversalError("Path '../etc/passwd' escapes base directory '/home/user/repo'"))
E            +        where PathTraversalError("Path '../etc/passwd' escapes base directory '/home/user/repo'") = <ExceptionInfo PathTraversalError("Path '../etc/passwd' escapes base directory '/home/user/repo'") tblen=2>.value

tests/hub/test_security.py:60: AssertionError
__________ TestTargetValidation.test_unregistered_write_target_denied __________

self = <tests.hub.test_security.TestTargetValidation object at 0x7a8b98742930>

    @pytest.mark.asyncio
    async def test_unregistered_write_target_denied(self):
        """Test that unregistered write targets are denied."""
        mock_repo = MagicMock()
        mock_repo.get = AsyncMock(return_value=None)
    
        policy = WriteTargetPolicy(mock_repo)
    
        with pytest.raises(ValueError) as exc_info:
>           await policy.validate_write_access("/unregistered/path/file.md", ".md")

tests/hub/test_security.py:213: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.hub.policy.write_target_policy.WriteTargetPolicy object at 0x7a8b9828d850>
path = '/unregistered/path/file.md', extension = '.md'

    async def validate_write_access(self, path: str, extension: str) -> WriteTargetInfo:
        """Validate write access to a path.
    
        Args:
            path: Absolute path to write to.
            extension: File extension (e.g., '.md').
    
        Returns:
            WriteTargetInfo if path is allowed.
    
        Raises:
            ValueError: If path is unknown or extension not allowed.
        """
>       target = await self._repo.get_by_path(path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: object MagicMock can't be used in 'await' expression

src/hub/policy/write_target_policy.py:38: TypeError
_________ TestSecurityEdgeCases.test_home_directory_expansion_rejected _________

self = <tests.hub.test_security.TestSecurityEdgeCases object at 0x7a8b98564590>

    def test_home_directory_expansion_rejected(self):
        """Test that ~ path expansion is detected and rejected."""
        base = "/home/user/repo"
    
        dangerous_paths = [
            "~/../etc/passwd",
            "~/.ssh/authorized_keys",
            "foo~/bar",
        ]
    
        for path in dangerous_paths:
>           with pytest.raises(PathTraversalError) as exc_info:
E           Failed: DID NOT RAISE <class 'src.shared.exceptions.PathTraversalError'>

tests/hub/test_security.py:539: Failed
_________________________ test_executor_list_directory _________________________

    @pytest.mark.asyncio
    async def test_executor_list_directory():
        """Test listing directory contents with metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            Path(tmpdir, "file1.txt").write_text("content1")
            Path(tmpdir, "file2.py").write_text("content2")
            os.makedirs(Path(tmpdir, "subdir").as_posix())
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           entries = await executor.list_directory(tmpdir)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:41: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b98294d40>
path = '/tmp/tmpe82j8kem', max_entries = 100

    async def list_directory(self, path: str, max_entries: int = 100) -> list[dict]:
        """
        List contents of a directory with metadata.
    
        Args:
            path: Directory path to list
            max_entries: Maximum number of entries to return
    
        Returns:
            List of entry dictionaries with metadata
        """
        validated_path = self._validate_path(path)
    
        if not validated_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
    
        entries = []
        try:
            for entry in validated_path.iterdir():
                try:
                    stat = entry.stat()
                    entries.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "is_dir": entry.is_dir(),
                            "size": stat.st_size if entry.is_file() else None,
                            "modified": datetime.fromtimestamp(
>                               stat.st_mtime, tz=datetime.UTC
                                                  ^^^^^^^^^^^^
                            ).isoformat(),
                        }
                    )
E                   AttributeError: type object 'datetime.datetime' has no attribute 'UTC'

src/node_agent/executor.py:100: AttributeError
___________________ test_executor_list_directory_max_entries ___________________

    @pytest.mark.asyncio
    async def test_executor_list_directory_max_entries():
        """Test respects max_entries limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create more than 2 files
            for i in range(5):
                Path(tmpdir, f"file{i}.txt").write_text(f"content{i}")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           entries = await executor.list_directory(tmpdir, max_entries=2)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:64: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b98446420>
path = '/tmp/tmpz1useolr', max_entries = 2

    async def list_directory(self, path: str, max_entries: int = 100) -> list[dict]:
        """
        List contents of a directory with metadata.
    
        Args:
            path: Directory path to list
            max_entries: Maximum number of entries to return
    
        Returns:
            List of entry dictionaries with metadata
        """
        validated_path = self._validate_path(path)
    
        if not validated_path.is_dir():
            raise ValueError(f"Not a directory: {path}")
    
        entries = []
        try:
            for entry in validated_path.iterdir():
                try:
                    stat = entry.stat()
                    entries.append(
                        {
                            "name": entry.name,
                            "path": str(entry),
                            "is_dir": entry.is_dir(),
                            "size": stat.st_size if entry.is_file() else None,
                            "modified": datetime.fromtimestamp(
>                               stat.st_mtime, tz=datetime.UTC
                                                  ^^^^^^^^^^^^
                            ).isoformat(),
                        }
                    )
E                   AttributeError: type object 'datetime.datetime' has no attribute 'UTC'

src/node_agent/executor.py:100: AttributeError
_____________________ test_executor_search_files_text_mode _____________________

    @pytest.mark.asyncio
    async def test_executor_search_files_text_mode():
        """Test search in text mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.py")
            test_file.write_text("def hello():\n    print('hello')")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           result = await executor.search_files(tmpdir, "hello", mode="text")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:120: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b982966f0>
directory = '/tmp/tmp4nkjo_vr', pattern = 'hello', include_patterns = None
max_results = 1000, timeout = 60, mode = 'text'

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
        max_results: int = 1000,
        timeout: int = 60,
        mode: str = "text",
    ) -> dict[str, Any]:
        """
        Search for pattern in files within a directory using ripgrep.
    
        Args:
            directory: Directory to search in (must be validated path).
            pattern: Regex pattern to search for.
            include_patterns: File patterns to include (e.g., ["*.py"]).
            max_results: Maximum number of matches to return.
            timeout: Search timeout in seconds.
            mode: Search mode - "text", "path", or "symbol".
    
        Returns:
            Dict with results, match count, files searched.
        """
        import shutil
    
        # Validate path first
        validated_dir = self._validate_path(directory)
    
        # Check if ripgrep is available
        rg_path = shutil.which("rg")
        if not rg_path:
>           raise ValueError("ripgrep (rg) is not installed on this node")
E           ValueError: ripgrep (rg) is not installed on this node

src/node_agent/executor.py:194: ValueError
_____________________ test_executor_search_files_path_mode _____________________

    @pytest.mark.asyncio
    async def test_executor_search_files_path_mode():
        """Test search in path mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files with matching names
            Path(tmpdir, "test_hello.py").write_text("pass")
            Path(tmpdir, "other.py").write_text("pass")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           result = await executor.search_files(tmpdir, "hello", mode="path")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:135: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b98294530>
directory = '/tmp/tmprohaqck6', pattern = 'hello', include_patterns = None
max_results = 1000, timeout = 60, mode = 'path'

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
        max_results: int = 1000,
        timeout: int = 60,
        mode: str = "text",
    ) -> dict[str, Any]:
        """
        Search for pattern in files within a directory using ripgrep.
    
        Args:
            directory: Directory to search in (must be validated path).
            pattern: Regex pattern to search for.
            include_patterns: File patterns to include (e.g., ["*.py"]).
            max_results: Maximum number of matches to return.
            timeout: Search timeout in seconds.
            mode: Search mode - "text", "path", or "symbol".
    
        Returns:
            Dict with results, match count, files searched.
        """
        import shutil
    
        # Validate path first
        validated_dir = self._validate_path(directory)
    
        # Check if ripgrep is available
        rg_path = shutil.which("rg")
        if not rg_path:
>           raise ValueError("ripgrep (rg) is not installed on this node")
E           ValueError: ripgrep (rg) is not installed on this node

src/node_agent/executor.py:194: ValueError
____________________ test_executor_search_files_symbol_mode ____________________

    @pytest.mark.asyncio
    async def test_executor_search_files_symbol_mode():
        """Test search in symbol mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.py")
            test_file.write_text("class MyClass:\n    pass")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           result = await executor.search_files(tmpdir, "MyClass", mode="symbol")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:149: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b98296540>
directory = '/tmp/tmpunc_gp3v', pattern = 'MyClass', include_patterns = None
max_results = 1000, timeout = 60, mode = 'symbol'

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
        max_results: int = 1000,
        timeout: int = 60,
        mode: str = "text",
    ) -> dict[str, Any]:
        """
        Search for pattern in files within a directory using ripgrep.
    
        Args:
            directory: Directory to search in (must be validated path).
            pattern: Regex pattern to search for.
            include_patterns: File patterns to include (e.g., ["*.py"]).
            max_results: Maximum number of matches to return.
            timeout: Search timeout in seconds.
            mode: Search mode - "text", "path", or "symbol".
    
        Returns:
            Dict with results, match count, files searched.
        """
        import shutil
    
        # Validate path first
        validated_dir = self._validate_path(directory)
    
        # Check if ripgrep is available
        rg_path = shutil.which("rg")
        if not rg_path:
>           raise ValueError("ripgrep (rg) is not installed on this node")
E           ValueError: ripgrep (rg) is not installed on this node

src/node_agent/executor.py:194: ValueError
____________________ test_executor_search_files_no_matches _____________________

    @pytest.mark.asyncio
    async def test_executor_search_files_no_matches():
        """Test handling no matches gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir, "test.py")
            test_file.write_text("print('hello')")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
>           result = await executor.search_files(tmpdir, "nonexistent_pattern")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/node_agent/test_executor.py:162: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <src.node_agent.executor.OperationExecutor object at 0x7a8b9829d1f0>
directory = '/tmp/tmp_irld4p9', pattern = 'nonexistent_pattern'
include_patterns = None, max_results = 1000, timeout = 60, mode = 'text'

    async def search_files(
        self,
        directory: str,
        pattern: str,
        include_patterns: list[str] | None = None,
        max_results: int = 1000,
        timeout: int = 60,
        mode: str = "text",
    ) -> dict[str, Any]:
        """
        Search for pattern in files within a directory using ripgrep.
    
        Args:
            directory: Directory to search in (must be validated path).
            pattern: Regex pattern to search for.
            include_patterns: File patterns to include (e.g., ["*.py"]).
            max_results: Maximum number of matches to return.
            timeout: Search timeout in seconds.
            mode: Search mode - "text", "path", or "symbol".
    
        Returns:
            Dict with results, match count, files searched.
        """
        import shutil
    
        # Validate path first
        validated_dir = self._validate_path(directory)
    
        # Check if ripgrep is available
        rg_path = shutil.which("rg")
        if not rg_path:
>           raise ValueError("ripgrep (rg) is not installed on this node")
E           ValueError: ripgrep (rg) is not installed on this node

src/node_agent/executor.py:194: ValueError
___________________ test_executor_git_status_recent_commits ____________________

    @pytest.mark.asyncio
    async def test_executor_git_status_recent_commits():
        """Test verifying recent_commits field in git status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize git repo and make a commit
            os.system(f"cd {tmpdir} && git init -q")
            Path(tmpdir, "file.txt").write_text("content")
            os.system(f"cd {tmpdir} && git add . && git commit -q -m 'Initial commit'")
    
            executor = OperationExecutor(allowed_paths=[tmpdir])
            result = await executor.git_status(tmpdir)
    
            assert "recent_commits" in result
            # Should have at least one commit
>           assert len(result["recent_commits"]) >= 1
E           assert 0 >= 1
E            +  where 0 = len([])

tests/node_agent/test_executor.py:202: AssertionError
----------------------------- Captured stderr call -----------------------------
Author identity unknown

*** Please tell me who you are.

Run

  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"

to set your account's default identity.
Omit --global to set the identity only in this repository.

fatal: empty ident name (for <pc@DESKTOP-S1M5C7P.localdomain>) not allowed
_________________________ test_redact_sensitive_nested _________________________

    def test_redact_sensitive_nested():
        """Test redacting nested sensitive fields."""
        data = {
            "user": {
                "name": "john",
                "credentials": {
                    "password": "secret",
                    "token": "abc123",
                },
            },
            "action": "login",
        }
    
        result = redact_sensitive(data)
    
        assert result["user"]["name"] == "john"
>       assert result["user"]["credentials"]["password"] == "[REDACTED]"
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       TypeError: string indices must be integers, not 'str'

tests/shared/test_logging.py:66: TypeError
__________________________ test_redact_sensitive_list __________________________

    def test_redact_sensitive_list():
        """Test redacting in lists."""
        data = {
            "users": [
                {"name": "alice", "password": "secret1"},
                {"name": "bob", "password": "secret2"},
            ],
            "tokens": ["token1", "token2"],
        }
    
        result = redact_sensitive(data)
    
        assert result["users"][0]["password"] == "[REDACTED]"
        assert result["users"][1]["password"] == "[REDACTED]"
>       assert result["tokens"][0] == "[REDACTED]"
E       AssertionError: assert '[' == '[REDACTED]'
E         
E         - [REDACTED]
E         + [

tests/shared/test_logging.py:85: AssertionError
_______________________ test_redact_sensitive_max_depth ________________________

    def test_redact_sensitive_max_depth():
        """Test handling deep nesting gracefully."""
        # Create deeply nested structure
        data = {"level1": {"level2": {"level3": {"level4": {"level5": {"value": "deep"}}}}}}
    
        # Should not raise, should return max depth message
        result = redact_sensitive(data, _depth=20)
>       assert result == "[MAX_DEPTH_EXCEEDED]"
E       AssertionError: assert {'level1': '[MAX_DEPTH_EXCEEDED]'} == '[MAX_DEPTH_EXCEEDED]'

tests/shared/test_logging.py:303: AssertionError
=========================== short test summary info ============================
FAILED tests/hub/test_contracts.py::TestDiscoveryTools::test_list_nodes_returns_structured_response
FAILED tests/hub/test_contracts.py::TestInspectionTools::test_inspect_repo_tree_requires_node_and_repo
FAILED tests/hub/test_contracts.py::TestInspectionTools::test_read_repo_file_requires_parameters
FAILED tests/hub/test_contracts.py::TestWriteTools::test_write_markdown_validates_extension
FAILED tests/hub/test_contracts.py::TestFailureModes::test_invalid_path_rejected
FAILED tests/hub/test_security.py::TestPathTraversal::test_path_traversal_dotdot_rejected
FAILED tests/hub/test_security.py::TestTargetValidation::test_unregistered_write_target_denied
FAILED tests/hub/test_security.py::TestSecurityEdgeCases::test_home_directory_expansion_rejected
FAILED tests/node_agent/test_executor.py::test_executor_list_directory - Attr...
FAILED tests/node_agent/test_executor.py::test_executor_list_directory_max_entries
FAILED tests/node_agent/test_executor.py::test_executor_search_files_text_mode
FAILED tests/node_agent/test_executor.py::test_executor_search_files_path_mode
FAILED tests/node_agent/test_executor.py::test_executor_search_files_symbol_mode
FAILED tests/node_agent/test_executor.py::test_executor_search_files_no_matches
FAILED tests/node_agent/test_executor.py::test_executor_git_status_recent_commits
FAILED tests/shared/test_logging.py::test_redact_sensitive_nested - TypeError...
FAILED tests/shared/test_logging.py::test_redact_sensitive_list - AssertionEr...
FAILED tests/shared/test_logging.py::test_redact_sensitive_max_depth - Assert...
======================== 18 failed, 109 passed in 1.76s ========================
~~~~

#### stderr

~~~~text
<no output>
~~~~
