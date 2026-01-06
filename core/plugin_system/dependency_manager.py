import subprocess
import sys
import json
import os
from pathlib import Path
import importlib
import pkg_resources
from packaging import requirements, version

class DependencyManager:
    def __init__(self):
        self.installed_packages = self._get_installed_packages()
    
    def _get_installed_packages(self):
        """Get list of installed packages"""
        installed = {}
        for dist in pkg_resources.working_set:
            installed[dist.key] = dist.version
        return installed
    
    def install_dependencies(self, requirements_list):
        """Install Python dependencies from requirements list"""
        if not requirements_list:
            return True
        
        try:
            # Filter out already installed packages
            to_install = []
            for req_str in requirements_list:
                try:
                    req = requirements.Requirement(req_str)
                    package_name = req.name.lower()
                    
                    # Check if already installed with correct version
                    if package_name in self.installed_packages:
                        installed_version = version.parse(self.installed_packages[package_name])
                        
                        if req.specifier:
                            if not installed_version in req.specifier:
                                to_install.append(req_str)
                        # If no version specifier, assume any version is OK
                    else:
                        to_install.append(req_str)
                        
                except Exception as e:
                    print(f"Error parsing requirement {req_str}: {e}")
                    to_install.append(req_str)
            
            if not to_install:
                return True
            
            # Install packages
            print(f"Installing dependencies: {to_install}")
            
            for package in to_install:
                try:
                    subprocess.check_call([
                        sys.executable, "-m", "pip", "install", 
                        "--quiet", "--no-warn-script-location", package
                    ])
                except subprocess.CalledProcessError as e:
                    print(f"Failed to install {package}: {e}")
                    # Try without specific version
                    try:
                        req = requirements.Requirement(package)
                        subprocess.check_call([
                            sys.executable, "-m", "pip", "install",
                            "--quiet", req.name
                        ])
                    except:
                        print(f"Completely failed to install {package}")
                        continue
            
            # Update installed packages list
            self.installed_packages = self._get_installed_packages()
            return True
            
        except Exception as e:
            print(f"Dependency installation failed: {e}")
            return False
    
    def install_npm_dependencies(self, package_json_path):
        """Install Node.js dependencies from package.json"""
        if not os.path.exists(package_json_path):
            return False
        
        try:
            # Read package.json
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            
            if not dependencies and not dev_dependencies:
                return True
            
            # Create package.json in temp directory
            temp_dir = Path('temp_npm_install')
            temp_dir.mkdir(exist_ok=True)
            
            temp_package = temp_dir / 'package.json'
            with open(temp_package, 'w') as f:
                json.dump({
                    'dependencies': dependencies,
                    'devDependencies': dev_dependencies
                }, f)
            
            # Install dependencies
            subprocess.check_call(['npm', 'install', '--quiet'], cwd=temp_dir)
            
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            
            return True
            
        except Exception as e:
            print(f"NPM dependency installation failed: {e}")
            return False
    
    def check_dependency(self, package_name, min_version=None):
        """Check if a specific dependency is installed"""
        try:
            importlib.import_module(package_name)
            
            if min_version:
                installed_version = self.installed_packages.get(package_name.lower())
                if installed_version:
                    installed_ver = version.parse(installed_version)
                    min_ver = version.parse(min_version)
                    return installed_ver >= min_ver
                return False
            
            return True
        except ImportError:
            return False
    
    def get_missing_dependencies(self, requirements_list):
        """Get list of missing dependencies"""
        missing = []
        
        for req_str in requirements_list:
            try:
                req = requirements.Requirement(req_str)
                package_name = req.name.lower()
                
                if package_name not in self.installed_packages:
                    missing.append(req_str)
                    continue
                
                # Check version
                if req.specifier:
                    installed_version = version.parse(self.installed_packages[package_name])
                    if not installed_version in req.specifier:
                        missing.append(req_str)
                        
            except Exception:
                missing.append(req_str)
        
        return missing
    
    def create_requirements_file(self, requirements_list, file_path='requirements.txt'):
        """Create requirements.txt file"""
        with open(file_path, 'w') as f:
            for req in requirements_list:
                f.write(f"{req}\n")
    
    def update_package_cache(self):
        """Update package cache"""
        self.installed_packages = self._get_installed_packages()
