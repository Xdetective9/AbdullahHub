import os
import sys
import importlib
import importlib.util
import subprocess
import tempfile
import json
import hashlib
from pathlib import Path
from datetime import datetime
import traceback

class PluginLoader:
    def __init__(self):
        self.plugins_dir = Path('plugins/installed')
        self.loaded_plugins = {}
        self.plugin_cache = {}
    
    def load_all_plugins(self):
        """Load all installed plugins"""
        self.loaded_plugins.clear()
        
        # Load Python plugins
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                self._load_python_plugin(plugin_dir)
        
        print(f"Loaded {len(self.loaded_plugins)} plugins")
    
    def _load_python_plugin(self, plugin_dir):
        """Load a Python plugin from directory"""
        plugin_file = plugin_dir / 'plugin.py'
        manifest_file = plugin_dir / 'plugin.json'
        
        if not plugin_file.exists():
            return
        
        try:
            # Load manifest if exists
            metadata = {}
            if manifest_file.exists():
                with open(manifest_file, 'r') as f:
                    metadata = json.load(f)
            
            # Load plugin module
            module_name = f"plugins.installed.{plugin_dir.name}.plugin"
            
            spec = importlib.util.spec_from_file_location(
                module_name,
                plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Extract metadata from module
            plugin_info = {
                'id': plugin_dir.name,
                'name': getattr(module, 'PLUGIN_NAME', metadata.get('name', plugin_dir.name)),
                'description': getattr(module, 'PLUGIN_DESCRIPTION', metadata.get('description', '')),
                'version': getattr(module, 'PLUGIN_VERSION', metadata.get('version', '1.0.0')),
                'author': getattr(module, 'PLUGIN_AUTHOR', metadata.get('author', 'Unknown')),
                'category': getattr(module, 'PLUGIN_CATEGORY', metadata.get('category', 'General')),
                'module': module,
                'execute': getattr(module, 'execute', None),
                'requirements': metadata.get('requirements', []),
                'api_keys_required': metadata.get('api_keys_required', []),
                'config_schema': metadata.get('config_schema', {}),
                'loaded_at': datetime.utcnow()
            }
            
            self.loaded_plugins[plugin_dir.name] = plugin_info
            print(f"Loaded plugin: {plugin_info['name']} v{plugin_info['version']}")
            
        except Exception as e:
            print(f"Failed to load plugin {plugin_dir.name}: {e}")
            traceback.print_exc()
    
    def load_plugin(self, plugin_record):
        """Load a specific plugin from database record"""
        plugin_id = str(plugin_record.id)
        
        if plugin_id in self.loaded_plugins:
            return self.loaded_plugins[plugin_id]
        
        plugin_dir = self.plugins_dir / plugin_id
        if plugin_dir.exists():
            return self._load_python_plugin(plugin_dir)
        
        return None
    
    def execute_plugin(self, plugin_id, user_id, input_data=None, files=None, api_key=None):
        """Execute a plugin with input data"""
        if plugin_id not in self.loaded_plugins:
            # Try to load plugin
            from core.models.plugin import Plugin
            plugin_record = Plugin.query.get(plugin_id)
            if plugin_record:
                self.load_plugin(plugin_record)
            else:
                raise ValueError(f"Plugin not found: {plugin_id}")
        
        plugin_info = self.loaded_plugins[plugin_id]
        
        if not plugin_info['execute']:
            raise ValueError(f"Plugin {plugin_info['name']} has no execute function")
        
        # Prepare execution context
        context = {
            'user_id': user_id,
            'input': input_data or {},
            'files': files or {},
            'api_key': api_key,
            'plugin_id': plugin_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Execute in sandbox if configured
            if os.environ.get('ENABLE_SANDBOX', 'true').lower() == 'true':
                from core.plugin_system.sandbox import Sandbox
                sandbox = Sandbox()
                result = sandbox.execute(
                    plugin_info['execute'],
                    context,
                    timeout=30
                )
            else:
                # Direct execution (for trusted plugins)
                result = plugin_info['execute'](context)
            
            # Log execution
            self._log_execution(plugin_id, user_id, 'success')
            
            return result
            
        except Exception as e:
            # Log error
            self._log_execution(plugin_id, user_id, 'error', str(e))
            raise
    
    def _log_execution(self, plugin_id, user_id, status, error=None):
        """Log plugin execution"""
        log_entry = {
            'plugin_id': plugin_id,
            'user_id': user_id,
            'status': status,
            'error': error,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Append to log file
        log_file = Path('storage/logs/plugin_executions.log')
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_plugin_info(self, plugin_id):
        """Get plugin information"""
        return self.loaded_plugins.get(plugin_id)
    
    def list_plugins(self):
        """List all loaded plugins"""
        return [
            {
                'id': pid,
                'name': info['name'],
                'description': info['description'],
                'version': info['version'],
                'category': info['category']
            }
            for pid, info in self.loaded_plugins.items()
        ]
