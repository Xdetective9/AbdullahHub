// Plugin Management JavaScript

class PluginManager {
    constructor() {
        this.init();
    }
    
    init() {
        // Initialize plugin cards
        this.initPluginCards();
        
        // Initialize search and filters
        this.initSearch();
        
        // Initialize install buttons
        this.initInstallButtons();
        
        // Initialize plugin runner
        this.initPluginRunner();
    }
    
    initPluginCards() {
        // Add hover effects to plugin cards
        document.querySelectorAll('.plugin-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px)';
                card.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.3)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.2)';
            });
        });
    }
    
    initSearch() {
        const searchInput = document.getElementById('pluginSearch');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const pluginCards = document.querySelectorAll('.plugin-card');
            
            pluginCards.forEach(card => {
                const title = card.querySelector('.plugin-title').textContent.toLowerCase();
                const desc = card.querySelector('.plugin-desc').textContent.toLowerCase();
                const tags = card.querySelector('.plugin-tags')?.textContent.toLowerCase() || '';
                
                if (title.includes(searchTerm) || desc.includes(searchTerm) || tags.includes(searchTerm)) {
                    card.style.display = 'block';
                    card.style.animation = 'fadeIn 0.3s ease';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    initInstallButtons() {
        document.querySelectorAll('.install-plugin').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                const pluginId = button.dataset.pluginId;
                const originalText = button.innerHTML;
                
                // Show loading state
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                button.disabled = true;
                
                try {
                    const response = await fetch(`/plugins/install/${pluginId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCsrfToken()
                        }
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        // Show success
                        button.innerHTML = '<i class="fas fa-check"></i> Installed';
                        button.classList.remove('btn-primary');
                        button.classList.add('btn-success');
                        
                        // Show notification
                        this.showNotification(data.message || 'Plugin installed successfully!', 'success');
                        
                        // Update UI after delay
                        setTimeout(() => {
                            if (button.closest('.plugin-card')) {
                                button.closest('.plugin-card').classList.add('installed');
                            }
                        }, 1000);
                    } else {
                        // Show error
                        button.innerHTML = originalText;
                        button.disabled = false;
                        this.showNotification(data.error || 'Installation failed', 'danger');
                    }
                } catch (error) {
                    console.error('Installation error:', error);
                    button.innerHTML = originalText;
                    button.disabled = false;
                    this.showNotification('Network error. Please try again.', 'danger');
                }
            });
        });
    }
    
    initPluginRunner() {
        const runButtons = document.querySelectorAll('.run-plugin');
        runButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const pluginId = button.dataset.pluginId;
                await this.executePlugin(pluginId);
            });
        });
    }
    
    async executePlugin(pluginId, inputData = {}) {
        try {
            // Show loading
            this.showLoader();
            
            const response = await fetch(`/plugins/execute/${pluginId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(inputData)
            });
            
            const data = await response.json();
            
            // Hide loader
            this.hideLoader();
            
            if (data.success) {
                this.showResult(data.result);
                return data.result;
            } else {
                this.showNotification(data.error || 'Execution failed', 'danger');
                return null;
            }
        } catch (error) {
            console.error('Execution error:', error);
            this.hideLoader();
            this.showNotification('Network error. Please try again.', 'danger');
            return null;
        }
    }
    
    showLoader() {
        // Create or show loader
        let loader = document.getElementById('pluginLoader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'pluginLoader';
            loader.className = 'plugin-loader';
            loader.innerHTML = `
                <div class="loader-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Running plugin...</p>
                </div>
            `;
            document.body.appendChild(loader);
        }
        loader.style.display = 'flex';
    }
    
    hideLoader() {
        const loader = document.getElementById('pluginLoader');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    showResult(result) {
        // Create result modal
        const modal = document.createElement('div');
        modal.className = 'plugin-result-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Plugin Result</h5>
                    <button type="button" class="btn-close" onclick="this.closest('.plugin-result-modal').remove()"></button>
                </div>
                <div class="modal-body">
                    <pre class="result-output">${JSON.stringify(result, null, 2)}</pre>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.plugin-result-modal').remove()">Close</button>
                    <button type="button" class="btn btn-primary" onclick="this.downloadResult()">Download</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add download functionality
        modal.querySelector('.btn-primary').addEventListener('click', () => {
            this.downloadResult(result);
        });
    }
    
    downloadResult(result) {
        const dataStr = JSON.stringify(result, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `plugin-result-${Date.now()}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
    }
    
    showNotification(message, type = 'info') {
        // Use existing notification system or create one
        if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            // Fallback notification
            const notification = document.createElement('div');
            notification.className = `alert alert-${type} alert-dismissible fade show`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                min-width: 300px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            `;
            
            notification.innerHTML = `
                ${message}
                <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
            `;
            
            document.body.appendChild(notification);
            
            // Auto remove after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }
    }
    
    getCsrfToken() {
        // Get CSRF token from meta tag
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.content : '';
    }
    
    // Plugin configuration
    configurePlugin(pluginId) {
        // Show configuration modal
        const modal = document.createElement('div');
        modal.className = 'plugin-config-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Configure Plugin</h5>
                    <button type="button" class="btn-close" onclick="this.closest('.plugin-config-modal').remove()"></button>
                </div>
                <div class="modal-body">
                    <form id="pluginConfigForm">
                        <!-- Configuration fields will be loaded dynamically -->
                        <div id="configFields"></div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.plugin-config-modal').remove()">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="this.saveConfiguration()">Save</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Load configuration schema
        this.loadConfigurationSchema(pluginId);
    }
    
    async loadConfigurationSchema(pluginId) {
        try {
            const response = await fetch(`/plugins/${pluginId}/config`);
            const data = await response.json();
            
            if (data.success) {
                this.renderConfigForm(data.schema);
            }
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }
    
    renderConfigForm(schema) {
        const fieldsDiv = document.getElementById('configFields');
        let html = '';
        
        for (const [key, config] of Object.entries(schema)) {
            html += this.renderConfigField(key, config);
        }
        
        fieldsDiv.innerHTML = html;
    }
    
    renderConfigField(key, config) {
        const { type, label, description, default: defaultValue, required } = config;
        
        let fieldHtml = `
            <div class="mb-3">
                <label class="form-label">${label || key}</label>
        `;
        
        switch (type) {
            case 'string':
                fieldHtml += `
                    <input type="text" 
                           name="${key}" 
                           class="form-control" 
                           value="${defaultValue || ''}"
                           ${required ? 'required' : ''}>
                `;
                break;
                
            case 'number':
                fieldHtml += `
                    <input type="number" 
                           name="${key}" 
                           class="form-control" 
                           value="${defaultValue || 0}"
                           ${required ? 'required' : ''}>
                `;
                break;
                
            case 'boolean':
                fieldHtml += `
                    <div class="form-check">
                        <input type="checkbox" 
                               name="${key}" 
                               class="form-check-input"
                               ${defaultValue ? 'checked' : ''}>
                        <label class="form-check-label">${label || key}</label>
                    </div>
                `;
                break;
                
            case 'select':
                fieldHtml += `
                    <select name="${key}" class="form-control" ${required ? 'required' : ''}>
                        ${config.options.map(opt => `
                            <option value="${opt.value}" ${opt.value === defaultValue ? 'selected' : ''}>
                                ${opt.label}
                            </option>
                        `).join('')}
                    </select>
                `;
                break;
        }
        
        if (description) {
            fieldHtml += `<small class="text-muted">${description}</small>`;
        }
        
        fieldHtml += '</div>';
        return fieldHtml;
    }
}

// Initialize plugin manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pluginManager = new PluginManager();
});

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function timeAgo(date) {
    const seconds = Math.floor((new Date() - new Date(date)) / 1000);
    
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + ' years ago';
    
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + ' months ago';
    
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + ' days ago';
    
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + ' hours ago';
    
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + ' minutes ago';
    
    return Math.floor(seconds) + ' seconds ago';
}

// Add CSS for plugin manager
const pluginStyles = `
.plugin-loader {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loader-content {
    background: var(--bg-card);
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    border: 1px solid var(--border-color);
}

.plugin-result-modal, .plugin-config-modal {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.plugin-result-modal .modal-content,
.plugin-config-modal .modal-content {
    background: var(--bg-card);
    border-radius: 15px;
    border: 1px solid var(--border-color);
    max-width: 800px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
}

.result-output {
    background: var(--bg-darker);
    padding: 1rem;
    border-radius: 5px;
    max-height: 400px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
}

.plugin-card {
    transition: all 0.3s ease;
    cursor: pointer;
}

.plugin-card.installed {
    border: 2px solid var(--success);
    background: rgba(67, 233, 123, 0.05);
}

.plugin-card .plugin-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 0.7rem;
    padding: 0.2rem 0.5rem;
}

@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

.installing {
    animation: pulse 0.5s ease infinite;
}
`;

// Add styles to document
const styleSheet = document.createElement('style');
styleSheet.textContent = pluginStyles;
document.head.appendChild(styleSheet);
