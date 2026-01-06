import sys
import os
import tempfile
import shutil
from pathlib import Path
import importlib
import importlib.util
import threading
import time
import json

class Sandbox:
    def __init__(self):
        self.timeout = 30  # seconds
        self.max_memory = 256  # MB
        self.allowed_modules = [
            'math', 'datetime', 'json', 're', 'random',
            'string', 'collections', 'itertools', 'functools',
            'typing', 'base64', 'hashlib', 'hmac', 'uuid'
        ]
    
    def execute(self, func, context, timeout=None):
        """Execute function in sandbox"""
        if timeout:
            self.timeout = timeout
        
        # Create temporary directory for execution
        temp_dir = tempfile.mkdtemp(prefix='sandbox_')
        
        try:
            # Set up execution environment
            env = self._create_safe_environment(temp_dir)
            
            # Add context to environment
            env['context'] = context
            
            # Execute with timeout
            result = self._execute_with_timeout(func, env, temp_dir)
            
            return result
            
        finally:
            # Cleanup
            self._cleanup(temp_dir)
    
    def _create_safe_environment(self, temp_dir):
        """Create a safe execution environment"""
        # Restricted environment
        env = {
            '__builtins__': self._get_safe_builtins(),
            'print': self._safe_print,
            'open': self._safe_open,
            'os': self._get_safe_os_module(),
            'sys': self._get_safe_sys_module(),
            'json': json,
            'math': __import__('math'),
            'datetime': __import__('datetime'),
            're': __import__('re'),
            'random': __import__('random'),
            'base64': __import__('base64'),
            'hashlib': __import__('hashlib'),
            'uuid': __import__('uuid')
        }
        
        return env
    
    def _get_safe_builtins(self):
        """Get safe built-in functions"""
        safe_builtins = {}
        
        # Whitelist of safe built-ins
        safe_functions = [
            'abs', 'all', 'any', 'bool', 'chr', 'dict', 'dir',
            'enumerate', 'filter', 'float', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'map', 'max',
            'min', 'next', 'pow', 'range', 'reversed', 'round',
            'set', 'slice', 'sorted', 'str', 'sum', 'tuple',
            'type', 'zip'
        ]
        
        for name in safe_functions:
            if hasattr(__builtins__, name):
                safe_builtins[name] = getattr(__builtins__, name)
        
        return safe_builtins
    
    def _safe_print(self, *args, **kwargs):
        """Safe print function that logs instead of printing"""
        # Log to file instead of printing
        log_file = Path('storage/logs/sandbox.log')
        with open(log_file, 'a') as f:
            f.write(' '.join(str(arg) for arg in args) + '\n')
    
    def _safe_open(self, filepath, mode='r', *args, **kwargs):
        """Safe open function with restrictions"""
        # Only allow reading/writing within temp directory
        temp_path = Path(filepath).resolve()
        
        # Check if trying to access outside temp or sandbox
        if '..' in filepath or '/etc/' in filepath or '/root/' in filepath:
            raise PermissionError("Access denied")
        
        # Only allow certain modes
        if mode not in ['r', 'rb', 'w', 'wb', 'a', 'ab']:
            raise ValueError("Unsupported file mode")
        
        return open(filepath, mode, *args, **kwargs)
    
    def _get_safe_os_module(self):
        """Get safe subset of os module"""
        import os
        safe_os = type('SafeOS', (), {})
        
        # Allow only safe functions
        allowed = ['path', 'name', 'sep', 'linesep']
        
        for attr in allowed:
            if hasattr(os, attr):
                setattr(safe_os, attr, getattr(os, attr))
        
        # Custom safe functions
        safe_os.path = type('SafePath', (), {
            'join': os.path.join,
            'exists': os.path.exists,
            'isfile': os.path.isfile,
            'isdir': os.path.isdir,
            'basename': os.path.basename,
            'dirname': os.path.dirname,
            'splitext': os.path.splitext
        })
        
        return safe_os
    
    def _get_safe_sys_module(self):
        """Get safe subset of sys module"""
        import sys
        safe_sys = type('SafeSys', (), {})
        
        allowed = ['version', 'platform', 'argv', 'stdin', 'stdout', 'stderr']
        
        for attr in allowed:
            if hasattr(sys, attr):
                setattr(safe_sys, attr, getattr(sys, attr))
        
        return safe_sys
    
    def _execute_with_timeout(self, func, env, temp_dir):
        """Execute function with timeout"""
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                # Change to temp directory
                original_dir = os.getcwd()
                os.chdir(temp_dir)
                
                # Execute function
                result = func(env['context'])
                
                os.chdir(original_dir)
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        
        thread.join(self.timeout)
        
        if thread.is_alive():
            # Thread is still running, kill it
            raise TimeoutError(f"Execution exceeded {self.timeout} seconds")
        
        if exception:
            raise exception
        
        return result
    
    def _cleanup(self, temp_dir):
        """Clean up temporary directory"""
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except:
            pass  # Ignore cleanup errors
    
    def validate_plugin_code(self, code):
        """Validate plugin code for security"""
        import ast
        
        try:
            tree = ast.parse(code)
            
            # Check for dangerous imports/operations
            for node in ast.walk(tree):
                # Check for dangerous imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_dangerous_module(alias.name):
                            return False, f"Dangerous import: {alias.name}"
                
                # Check for dangerous function calls
                if isinstance(node, ast.Call):
                    if self._is_dangerous_call(node):
                        return False, "Dangerous function call detected"
            
            return True, "Code is safe"
            
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
    
    def _is_dangerous_module(self, module_name):
        """Check if module is dangerous"""
        dangerous_modules = [
            'os', 'sys', 'subprocess', 'shutil', 'socket',
            'requests', 'urllib', 'ctypes', 'pickle', 'marshal',
            'eval', 'exec', 'compile', '__import__'
        ]
        
        return any(module_name.startswith(danger) for danger in dangerous_modules)
    
    def _is_dangerous_call(self, node):
        """Check if function call is dangerous"""
        dangerous_calls = ['eval', 'exec', 'compile', 'open', 'system', 'popen']
        
        if isinstance(node.func, ast.Name):
            return node.func.id in dangerous_calls
        
        return False
