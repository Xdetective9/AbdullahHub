import os
import json
import zipfile
import tarfile
import ast
import re
import tempfile
from pathlib import Path
import subprocess
import sys

class PluginAnalyzer:
    def __init__(self):
        self.supported_languages = ['python', 'javascript', 'nodejs', 'bash']
    
    def analyze_plugin(self, file_path):
        """Analyze plugin file to extract metadata and requirements"""
        file_ext = Path(file_path).suffix.lower()
        
        # Handle compressed files
        if file_ext in ['.zip', '.tar.gz', '.tgz']:
            return self._analyze_compressed(file_path)
        elif file_ext == '.py':
            return self._analyze_python(file_path)
        elif file_ext in ['.js', '.ts']:
            return self._analyze_javascript(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
    
    def _analyze_compressed(self, file_path):
        """Analyze compressed plugin package"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Extract based on file type
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
            else:  # tar.gz or tgz
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(temp_dir)
            
            # Look for plugin manifest
            manifest_path = Path(temp_dir) / 'plugin.json'
            if manifest_path.exists():
                return self._analyze_from_manifest(manifest_path)
            
            # Look for Python setup.py or package.json
            setup_py = Path(temp_dir) / 'setup.py'
            package_json = Path(temp_dir) / 'package.json'
            
            if setup_py.exists():
                return self._analyze_python_package(temp_dir)
            elif package_json.exists():
                return self._analyze_node_package(temp_dir)
            else:
                # Auto-detect language
                return self._auto_detect_plugin(temp_dir)
                
        finally:
            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _analyze_python(self, file_path):
        """Analyze Python plugin file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse AST to extract metadata
        tree = ast.parse(content)
        
        metadata = {
            'name': 'Unknown Plugin',
            'description': '',
            'version': '1.0.0',
            'author': 'Unknown',
            'category': 'General',
            'requirements': [],
            'api_keys_required': [],
            'language': 'python'
        }
        
        # Look for metadata assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if target.id == 'PLUGIN_NAME':
                            if isinstance(node.value, ast.Constant):
                                metadata['name'] = node.value.value
                        elif target.id == 'PLUGIN_DESCRIPTION':
                            if isinstance(node.value, ast.Constant):
                                metadata['description'] = node.value.value
                        elif target.id == 'PLUGIN_VERSION':
                            if isinstance(node.value, ast.Constant):
                                metadata['version'] = node.value.value
                        elif target.id == 'PLUGIN_AUTHOR':
                            if isinstance(node.value, ast.Constant):
                                metadata['author'] = node.value.value
                        elif target.id == 'PLUGIN_CATEGORY':
                            if isinstance(node.value, ast.Constant):
                                metadata['category'] = node.value.value
        
        # Extract imports for requirements
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        
        metadata['requirements'] = self._parse_python_requirements(imports)
        
        # Look for API key patterns
        api_patterns = [
            r'api[_-]?key',
            r'api[_-]?secret',
            r'token',
            r'password',
            r'auth[_-]?key'
        ]
        
        api_keys = []
        for pattern in api_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                api_keys.append(pattern.replace('\\', ''))
        
        metadata['api_keys_required'] = list(set(api_keys))
        
        return metadata
    
    def _analyze_javascript(self, file_path):
        """Analyze JavaScript plugin file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        metadata = {
            'name': 'Unknown Plugin',
            'description': '',
            'version': '1.0.0',
            'author': 'Unknown',
            'category': 'General',
            'requirements': [],
            'api_keys_required': [],
            'language': 'javascript'
        }
        
        # Look for metadata in comments or assignments
        name_match = re.search(r'@name\s+(.+)', content)
        if name_match:
            metadata['name'] = name_match.group(1).strip()
        
        desc_match = re.search(r'@description\s+(.+)', content)
        if desc_match:
            metadata['description'] = desc_match.group(1).strip()
        
        version_match = re.search(r'@version\s+(.+)', content)
        if version_match:
            metadata['version'] = version_match.group(1).strip()
        
        # Look for require/import statements
        import_patterns = [
            r'require\([\'"](.+?)[\'"]\)',
            r'from\s+[\'"](.+?)[\'"]',
            r'import\s+[\'"](.+?)[\'"]'
        ]
        
        imports = []
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        metadata['requirements'] = self._parse_js_requirements(imports)
        
        return metadata
    
    def _parse_python_requirements(self, imports):
        """Convert imports to pip requirements"""
        requirements = []
        standard_libs = set(sys.builtin_module_names)
        
        for imp in imports:
            # Skip standard library
            if imp.split('.')[0] in standard_libs:
                continue
            
            # Common mapping
            mapping = {
                'requests': 'requests>=2.25.1',
                'numpy': 'numpy>=1.19.5',
                'pandas': 'pandas>=1.2.0',
                'PIL': 'Pillow>=8.1.0',
                'cv2': 'opencv-python>=4.5.1',
                'bs4': 'beautifulsoup4>=4.9.3',
                'sklearn': 'scikit-learn>=0.24.1',
                'tensorflow': 'tensorflow>=2.4.0',
                'torch': 'torch>=1.8.0'
            }
            
            if imp in mapping:
                requirements.append(mapping[imp])
            else:
                # Use import name as package name
                pkg_name = imp.split('.')[0].replace('_', '-')
                requirements.append(f'{pkg_name}>=1.0.0')
        
        return list(set(requirements))
    
    def _parse_js_requirements(self, imports):
        """Convert imports to npm requirements"""
        requirements = []
        
        for imp in imports:
            # Skip built-ins and relative imports
            if imp.startswith('.') or imp.startswith('/'):
                continue
            
            # Common mapping
            mapping = {
                'express': 'express',
                'axios': 'axios',
                'lodash': 'lodash',
                'moment': 'moment',
                'react': 'react',
                'vue': 'vue'
            }
            
            if imp in mapping:
                requirements.append(f'{mapping[imp]}@latest')
            else:
                # Use import name as package name
                requirements.append(f'{imp}@latest')
        
        return requirements
    
    def _analyze_from_manifest(self, manifest_path):
        """Analyze plugin from manifest file"""
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        return {
            'name': manifest.get('name', 'Unknown Plugin'),
            'description': manifest.get('description', ''),
            'version': manifest.get('version', '1.0.0'),
            'author': manifest.get('author', 'Unknown'),
            'category': manifest.get('category', 'General'),
            'requirements': manifest.get('requirements', []),
            'api_keys_required': manifest.get('api_keys_required', []),
            'language': manifest.get('language', 'python')
        }
    
    def _auto_detect_plugin(self, directory):
        """Auto-detect plugin type in directory"""
        dir_path = Path(directory)
        
        # Check for Python files
        py_files = list(dir_path.glob('**/*.py'))
        if py_files:
            return self._analyze_python(str(py_files[0]))
        
        # Check for JS files
        js_files = list(dir_path.glob('**/*.js'))
        if js_files:
            return self._analyze_javascript(str(js_files[0]))
        
        raise ValueError("Could not detect plugin type in package")
