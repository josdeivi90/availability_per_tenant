/**
 * KubeHealth Dashboard - Frontend JavaScript
 * Maneja la lógica del dashboard, carga de datos, gráficos y actualizaciones
 */

class KubeHealthDashboard {
    constructor() {
        console.log('🔧 Construyendo KubeHealthDashboard...');
        this.isPolling = false;
        this.pollingInterval = null;
        this.availabilityChart = null;
        this.incidentsChart = null;
        this.lastUpdated = null;
        this.githubToken = null; // Se configurará desde el status.json o variables
        this.githubRepo = null;  // Se configurará desde el status.json o variables
        
        // Datos de organizaciones para búsqueda
        this.allOrganizations = [];
        this.searchTimeout = null;
        
        // URLs de configuración
        this.statusUrl = './status.json'; // Donde el backend publica el JSON
        this.githubApiUrl = 'https://api.github.com';
        
        // Elementos del DOM
        this.elements = {};
        
        console.log('🎯 Configuración inicial completa, llamando init()...');
        this.init();
    }

    /**
     * Inicializa el dashboard
     */
    async init() {
        try {
            console.log('🚀 Inicializando KubeHealth Dashboard...');
            
            // Cachear elementos del DOM
            console.log('📋 Cacheando elementos del DOM...');
            this.cacheElements();
            
            // Configurar event listeners
            console.log('👂 Configurando event listeners...');
            this.setupEventListeners();
            
            // Configurar gráficos
            console.log('📊 Configurando gráficos...');
            this.setupCharts();
            
            // Cargar datos iniciales
            console.log('📡 Cargando datos iniciales...');
            await this.fetchData();
            
            // Configurar polling automático cada 2 minutos
            console.log('⏰ Configurando polling automático...');
            this.startAutoPolling();
            
            console.log('✅ Dashboard inicializado correctamente');
        } catch (error) {
            console.error('💥 Error durante la inicialización:', error);
            this.showError(`Error de inicialización: ${error.message}`);
        }
    }

    /**
     * Cachea elementos del DOM para mejor performance
     */
    cacheElements() {
        this.elements = {
            // Estados
            loadingState: document.getElementById('loading-state'),
            mainContent: document.getElementById('main-content'),
            errorState: document.getElementById('error-state'),
            
            // Header
            lastUpdated: document.getElementById('last-updated'),
            refreshBtn: document.getElementById('refresh-btn'),
            refreshIcon: document.getElementById('refresh-icon'),
            refreshText: document.getElementById('refresh-text'),
            
            // Search
            organizationSearch: document.getElementById('organization-search'),
            searchDropdown: document.getElementById('search-dropdown'),
            searchResults: document.getElementById('search-results'),
            searchSpinner: document.getElementById('search-spinner'),
            searchClear: document.getElementById('search-clear'),
            selectedOrganization: document.getElementById('selected-organization'),
            selectedOrgDetails: document.getElementById('selected-org-details'),
            
            // Status general
            overallStatusIcon: document.getElementById('overall-status-icon'),
            overallStatusText: document.getElementById('overall-status-text'),
            
            // Summary cards
            totalClusters: document.getElementById('total-clusters'),
            totalNamespaces: document.getElementById('total-namespaces'),
            podsRunning: document.getElementById('pods-running'),
            activeIncidents: document.getElementById('active-incidents'),
            
            // Listas
            clustersList: document.getElementById('clusters-list'),
            
            // Charts
            availabilityChart: document.getElementById('availability-chart'),
            incidentsChart: document.getElementById('incidents-chart')
        };
    }

    /**
     * Configura los event listeners
     */
    setupEventListeners() {
        // Botón de actualizar
        this.elements.refreshBtn.addEventListener('click', () => {
            this.triggerManualUpdate();
        });

        // Funcionalidad de búsqueda
        this.setupSearchListeners();

        // Recargar página en caso de error
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                location.reload();
            }
        });

        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!this.elements.organizationSearch.contains(e.target) && 
                !this.elements.searchDropdown.contains(e.target)) {
                this.hideSearchDropdown();
            }
        });

        // Reposicionar dropdown en scroll o resize
        window.addEventListener('scroll', () => {
            if (!this.elements.searchDropdown.classList.contains('hidden')) {
                this.positionSearchDropdown();
            }
        });

        window.addEventListener('resize', () => {
            if (!this.elements.searchDropdown.classList.contains('hidden')) {
                this.positionSearchDropdown();
            }
        });
    }

    /**
     * Configura los gráficos de Chart.js
     */
    setupCharts() {
        console.log('📊 Configurando gráficos - Chart disponible:', typeof Chart !== 'undefined');
        
        if (typeof Chart === 'undefined') {
            console.warn('⚠️ Chart.js no está disponible, mostrando placeholders');
            this.showChartPlaceholders();
            return;
        }
        
        // Configuración común
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)',
                    }
                }
            }
        };

        // Gráfico de disponibilidad
        const availabilityCtx = this.elements.availabilityChart.getContext('2d');
        this.availabilityChart = new Chart(availabilityCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Disponibilidad (%)',
                    data: [],
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        ...commonOptions.scales.y,
                        min: 0,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });

        // Gráfico de incidentes
        const incidentsCtx = this.elements.incidentsChart.getContext('2d');
        this.incidentsChart = new Chart(incidentsCtx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Incidentes Activos',
                    data: [],
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: 'rgb(239, 68, 68)',
                    borderWidth: 1
                }]
            },
            options: {
                ...commonOptions,
                scales: {
                    ...commonOptions.scales,
                    y: {
                        ...commonOptions.scales.y,
                        ticks: {
                            stepSize: 1
                        }
                    }
                }
            }
        });
    }

    /**
     * Obtiene los datos del status.json
     */
    async fetchData() {
        try {
            console.log('📡 Obteniendo datos del servidor...');
            console.log('🔗 URL de status:', this.statusUrl);
            
            const response = await fetch(this.statusUrl + '?t=' + Date.now());
            console.log('📤 Respuesta recibida:', response.status, response.statusText);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            console.log('✅ Datos obtenidos correctamente:', data);
            
            // Actualizar UI con los datos
            this.updateUI(data);
            
            return data;
            
        } catch (error) {
            console.error('❌ Error al obtener datos:', error);
            console.error('❌ Stack trace:', error.stack);
            this.showError(`Error: ${error.message}`);
            throw error;
        }
    }

    /**
     * Actualiza la interfaz de usuario con los datos
     */
    updateUI(data) {
        try {
            console.log('🔄 Actualizando interfaz de usuario...');
            
            // Ocultar loading, mostrar contenido
            this.showMainContent();
            
            // Actualizar timestamp
            this.updateLastUpdated(data.last_updated);
            
            // Actualizar estado general
            this.updateOverallStatus(data.overall_status);
            
            // Actualizar cards de resumen
            this.updateSummaryCards(data.summary);
            
            // Actualizar gráficos
            this.updateCharts(data.historical_data);
            
            // Actualizar lista de clústeres
            this.updateClustersList(data.clusters);
            
            // Actualizar datos de organizaciones para búsqueda
            this.updateOrganizationsData(data);
            
            console.log('✅ Interfaz actualizada correctamente');
            
        } catch (error) {
            console.error('❌ Error al actualizar UI:', error);
            this.showError('Error al procesar los datos');
        }
    }

    /**
     * Actualiza la fecha de última actualización
     */
    updateLastUpdated(timestamp) {
        if (timestamp) {
            const date = new Date(timestamp);
            const options = {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'America/Mexico_City'
            };
            this.elements.lastUpdated.textContent = date.toLocaleDateString('es-MX', options);
            this.lastUpdated = timestamp;
        }
    }

    /**
     * Actualiza el estado general del sistema
     */
    updateOverallStatus(status) {
        const statusConfig = {
            'Saludable': {
                class: 'bg-green-500',
                icon: 'fas fa-heart',
                color: 'text-green-600'
            },
            'Advertencia': {
                class: 'bg-yellow-500',
                icon: 'fas fa-exclamation-triangle',
                color: 'text-yellow-600'
            },
            'Crítico': {
                class: 'bg-red-500',
                icon: 'fas fa-times-circle',
                color: 'text-red-600'
            }
        };

        const config = statusConfig[status] || statusConfig['Advertencia'];
        
        this.elements.overallStatusIcon.className = `h-8 w-8 rounded-full flex items-center justify-center ${config.class}`;
        this.elements.overallStatusIcon.innerHTML = `<i class="${config.icon} text-white text-lg"></i>`;
        this.elements.overallStatusText.textContent = status;
        this.elements.overallStatusText.className = `text-2xl font-bold ${config.color}`;
    }

    /**
     * Actualiza las tarjetas de resumen
     */
    updateSummaryCards(summary) {
        if (summary) {
            this.elements.totalClusters.textContent = summary.total_clusters || '0';
            this.elements.totalNamespaces.textContent = summary.total_namespaces_monitored || '0';
            this.elements.podsRunning.textContent = summary.pods_running || '0';
            this.elements.activeIncidents.textContent = summary.active_incidents || '0';
        }
    }

    /**
     * Actualiza los gráficos con datos históricos
     */
    updateCharts(historicalData) {
        if (!historicalData || !historicalData.timestamps) {
            console.log('📊 No hay datos históricos disponibles');
            return;
        }

        // Si Chart.js no está disponible, skip
        if (typeof Chart === 'undefined') {
            console.log('📊 Chart.js no disponible, saltando actualización de gráficos');
            return;
        }

        // Procesar timestamps para labels más legibles
        const labels = historicalData.timestamps.map(timestamp => {
            const date = new Date(timestamp);
            return date.toLocaleDateString('es-MX', { 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        });

        // Actualizar gráfico de disponibilidad
        if (this.availabilityChart && historicalData.availability_history) {
            console.log('📊 Actualizando gráfico de disponibilidad');
            this.availabilityChart.data.labels = labels;
            this.availabilityChart.data.datasets[0].data = historicalData.availability_history;
            this.availabilityChart.update();
        }

        // Actualizar gráfico de incidentes
        if (this.incidentsChart && historicalData.incident_history) {
            console.log('📊 Actualizando gráfico de incidentes');
            this.incidentsChart.data.labels = labels;
            this.incidentsChart.data.datasets[0].data = historicalData.incident_history;
            this.incidentsChart.update();
        }
    }

    /**
     * Actualiza la lista de clústeres
     */
    updateClustersList(clusters) {
        if (!clusters || !Array.isArray(clusters)) {
            this.elements.clustersList.innerHTML = '<p class="p-4 text-gray-500">No hay datos de clústeres disponibles</p>';
            return;
        }

        let html = '';
        
        clusters.forEach((cluster, clusterIndex) => {
            const statusColor = this.getStatusColor(cluster.status);
            
            html += `
                <div class="border-b border-gray-200 last:border-b-0">
                    <div class="px-4 py-4 sm:px-6">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center">
                                <div class="flex-shrink-0">
                                    <div class="h-3 w-3 rounded-full ${statusColor}"></div>
                                </div>
                                <div class="ml-3">
                                    <h4 class="text-sm font-medium text-gray-900">${cluster.name}</h4>
                                    <p class="text-sm text-gray-500">Estado: ${cluster.status}</p>
                                </div>
                            </div>
                            <button onclick="dashboard.toggleClusterDetails(${clusterIndex})" 
                                    class="text-blue-600 hover:text-blue-900 text-sm font-medium">
                                <span id="toggle-text-${clusterIndex}">Mostrar detalles</span>
                                <i class="fas fa-chevron-down ml-1" id="toggle-icon-${clusterIndex}"></i>
                            </button>
                        </div>
                        
                        <div id="cluster-details-${clusterIndex}" class="hidden mt-4">
                            ${this.renderNamespaces(cluster.namespaces || [])}
                        </div>
                    </div>
                </div>
            `;
        });

        this.elements.clustersList.innerHTML = html;
    }

    /**
     * Renderiza los namespaces de un clúster
     */
    renderNamespaces(namespaces) {
        if (!namespaces.length) {
            return '<p class="text-sm text-gray-500">No hay organizaciones monitoreadas en este clúster</p>';
        }

        let html = '<div class="space-y-3">';
        
        namespaces.forEach(namespace => {
            const statusColor = this.getStatusColor(namespace.status);
            const availabilityColor = namespace.availability_percentage >= 95 ? 'text-green-600' : 
                                    namespace.availability_percentage >= 90 ? 'text-yellow-600' : 'text-red-600';
            
            html += `
                <div class="bg-gray-50 rounded-lg p-4 border-2 border-transparent transition-all duration-200" data-org-uuid="${namespace.uuid}">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center">
                            <div class="h-2 w-2 rounded-full ${statusColor} mr-2"></div>
                            <h5 class="text-sm font-medium text-gray-900">${namespace.organization_name}</h5>
                        </div>
                        <span class="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">${namespace.uuid}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                            <p class="text-gray-500">Disponibilidad</p>
                            <p class="font-medium ${availabilityColor}">${namespace.availability_percentage}%</p>
                        </div>
                        <div>
                            <p class="text-gray-500">Pods Running</p>
                            <p class="font-medium text-gray-900">${namespace.pods?.running || 0}</p>
                        </div>
                        <div>
                            <p class="text-gray-500">Pods Failed</p>
                            <p class="font-medium text-gray-900">${namespace.pods?.failed || 0}</p>
                        </div>
                        <div>
                            <p class="text-gray-500">Reinicios</p>
                            <p class="font-medium text-gray-900">${namespace.pods?.restarts || 0}</p>
                        </div>
                    </div>
                    
                    ${this.renderIncidents(namespace.related_incidents || [])}
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    /**
     * Renderiza los incidentes relacionados
     */
    renderIncidents(incidents) {
        if (!incidents.length) {
            return '';
        }

        let html = '<div class="mt-3 pt-3 border-t border-gray-200"><h6 class="text-xs font-medium text-gray-700 mb-2">Incidentes Relacionados:</h6><div class="space-y-1">';
        
        incidents.forEach(incident => {
            const date = new Date(incident.created_at).toLocaleDateString('es-MX', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            html += `
                <div class="flex items-center justify-between text-xs">
                    <a href="${incident.url}" target="_blank" class="text-blue-600 hover:text-blue-800 truncate max-w-xs">
                        ${incident.title}
                    </a>
                    <span class="text-gray-500 ml-2">${date}</span>
                </div>
            `;
        });

        html += '</div></div>';
        return html;
    }

    /**
     * Obtiene el color CSS para un estado
     */
    getStatusColor(status) {
        const colors = {
            'Saludable': 'bg-green-500',
            'Advertencia': 'bg-yellow-500',
            'Crítico': 'bg-red-500'
        };
        return colors[status] || 'bg-gray-500';
    }

    /**
     * Alterna la visibilidad de los detalles del clúster
     */
    toggleClusterDetails(clusterIndex) {
        const details = document.getElementById(`cluster-details-${clusterIndex}`);
        const toggleText = document.getElementById(`toggle-text-${clusterIndex}`);
        const toggleIcon = document.getElementById(`toggle-icon-${clusterIndex}`);
        
        if (details.classList.contains('hidden')) {
            details.classList.remove('hidden');
            toggleText.textContent = 'Ocultar detalles';
            toggleIcon.classList.remove('fa-chevron-down');
            toggleIcon.classList.add('fa-chevron-up');
        } else {
            details.classList.add('hidden');
            toggleText.textContent = 'Mostrar detalles';
            toggleIcon.classList.remove('fa-chevron-up');
            toggleIcon.classList.add('fa-chevron-down');
        }
    }

    /**
     * Dispara una actualización manual
     */
    async triggerManualUpdate() {
        try {
            console.log('🔄 Disparando actualización manual...');
            
            // Cambiar estado del botón
            this.setRefreshButton(true, 'Actualizando...', 'fa-spin fa-sync-alt');
            
            // Simular disparo del workflow (aquí iría la llamada a GitHub API)
            // Por ahora, solo actualizamos los datos
            await this.fetchData();
            
            // Iniciar polling agresivo por 2 minutos para detectar nuevos datos
            this.startPolling();
            
        } catch (error) {
            console.error('❌ Error en actualización manual:', error);
        } finally {
            // Restaurar botón después de 3 segundos
            setTimeout(() => {
                this.setRefreshButton(false, 'Actualizar Ahora', 'fa-sync-alt');
            }, 3000);
        }
    }

    /**
     * Configura el estado del botón de actualizar
     */
    setRefreshButton(disabled, text, iconClass) {
        this.elements.refreshBtn.disabled = disabled;
        this.elements.refreshText.textContent = text;
        this.elements.refreshIcon.className = `mr-2 ${iconClass}`;
        
        if (disabled) {
            this.elements.refreshBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            this.elements.refreshBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }

    /**
     * Inicia polling agresivo después de actualización manual
     */
    startPolling() {
        if (this.isPolling) return;
        
        this.isPolling = true;
        let attempts = 0;
        const maxAttempts = 40; // 2 minutos con intervalos de 3 segundos
        
        console.log('🔍 Iniciando polling para detectar nuevos datos...');
        
        this.pollingInterval = setInterval(async () => {
            attempts++;
            
            try {
                const data = await this.fetchData();
                
                // Si hay nuevos datos, detener polling
                if (data.last_updated !== this.lastUpdated) {
                    console.log('✅ Nuevos datos detectados, deteniendo polling');
                    this.stopPolling();
                    return;
                }
                
            } catch (error) {
                console.warn('⚠️ Error durante polling:', error.message);
            }
            
            // Detener después del máximo de intentos
            if (attempts >= maxAttempts) {
                console.log('⏰ Polling terminado por timeout');
                this.stopPolling();
            }
            
        }, 3000); // Cada 3 segundos
    }

    /**
     * Detiene el polling
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        this.isPolling = false;
    }

    /**
     * Inicia polling automático menos frecuente
     */
    startAutoPolling() {
        // Polling automático cada 2 minutos
        setInterval(() => {
            if (!this.isPolling) { // Solo si no estamos en polling agresivo
                console.log('🔄 Actualización automática...');
                this.fetchData().catch(error => {
                    console.warn('⚠️ Error en actualización automática:', error.message);
                });
            }
        }, 120000); // 2 minutos
    }

    /**
     * Muestra el contenido principal
     */
    showMainContent() {
        this.elements.loadingState.classList.add('hidden');
        this.elements.errorState.classList.add('hidden');
        this.elements.mainContent.classList.remove('hidden');
    }

    /**
     * Muestra placeholders cuando Chart.js no está disponible
     */
    showChartPlaceholders() {
        console.log('📊 Mostrando placeholders para gráficos');
        
        if (this.elements.availabilityChart) {
            this.elements.availabilityChart.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
                    <div class="text-center">
                        <i class="fas fa-chart-line text-4xl text-gray-400 mb-2"></i>
                        <p class="text-gray-600 font-medium">Gráfico de Disponibilidad</p>
                        <p class="text-gray-500 text-sm">Chart.js no disponible</p>
                    </div>
                </div>
            `;
        }
        
        if (this.elements.incidentsChart) {
            this.elements.incidentsChart.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-64 bg-gray-100 rounded-lg">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl text-gray-400 mb-2"></i>
                        <p class="text-gray-600 font-medium">Gráfico de Incidentes</p>
                        <p class="text-gray-500 text-sm">Chart.js no disponible</p>
                    </div>
                </div>
            `;
        }
    }

    /**
     * Configura los event listeners específicos de búsqueda
     */
    setupSearchListeners() {
        console.log('🔍 Configurando funcionalidad de búsqueda...');
        
        // Input de búsqueda
        this.elements.organizationSearch.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // Mostrar/ocultar botón de limpiar
            if (query.length > 0) {
                this.elements.searchClear.classList.remove('hidden');
            } else {
                this.elements.searchClear.classList.add('hidden');
                this.hideSearchDropdown();
                this.hideSelectedOrganization();
            }
            
            // Debounce la búsqueda
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            this.searchTimeout = setTimeout(() => {
                this.searchOrganizations(query);
            }, 300);
        });

        // Navegación con teclado en el input
        this.elements.organizationSearch.addEventListener('keydown', (e) => {
            const dropdown = this.elements.searchDropdown;
            const results = dropdown.querySelectorAll('.search-result-item');
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (results.length > 0) {
                    results[0].focus();
                }
            } else if (e.key === 'Escape') {
                this.hideSearchDropdown();
            }
        });

        // Botón de limpiar
        this.elements.searchClear.addEventListener('click', () => {
            this.elements.organizationSearch.value = '';
            this.elements.searchClear.classList.add('hidden');
            this.hideSearchDropdown();
            this.hideSelectedOrganization();
            this.elements.organizationSearch.focus();
        });
    }

    /**
     * Busca organizaciones basado en el query
     */
    searchOrganizations(query) {
        if (!query || query.length < 2) {
            this.hideSearchDropdown();
            return;
        }

        console.log('🔍 Buscando organizaciones:', query);
        
        // Mostrar spinner
        this.elements.searchSpinner.classList.remove('hidden');
        
        // Filtrar organizaciones
        const results = this.allOrganizations.filter(org => 
            org.organization_name.toLowerCase().includes(query.toLowerCase()) ||
            org.uuid.toLowerCase().includes(query.toLowerCase())
        ).slice(0, 10); // Máximo 10 resultados

        // Mostrar resultados
        this.showSearchResults(results, query);
        
        // Ocultar spinner
        this.elements.searchSpinner.classList.add('hidden');
    }

    /**
     * Muestra los resultados de búsqueda en el dropdown
     */
    showSearchResults(results, query) {
        const container = this.elements.searchResults;
        
        if (results.length === 0) {
            container.innerHTML = `
                <div class="px-4 py-3 text-gray-500 text-center">
                    <i class="fas fa-search mb-2"></i>
                    <p>No se encontraron organizaciones para "${query}"</p>
                </div>
            `;
        } else {
            container.innerHTML = results.map((org, index) => {
                const statusColor = this.getStatusColor(org.status);
                const availabilityColor = org.availability_percentage >= 95 ? 'text-green-600' : 
                                        org.availability_percentage >= 90 ? 'text-yellow-600' : 'text-red-600';
                
                return `
                    <div class="search-result-item px-4 py-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0 focus:bg-blue-50 focus:outline-none" 
                         tabindex="0"
                         data-org-index="${index}">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center min-w-0 flex-1">
                                <div class="h-3 w-3 rounded-full ${statusColor} mr-3 flex-shrink-0"></div>
                                <div class="min-w-0 flex-1">
                                    <p class="text-sm font-medium text-gray-900 truncate">${this.highlightMatch(org.organization_name, query)}</p>
                                    <p class="text-xs text-gray-500 truncate">${org.cluster_name}</p>
                                </div>
                            </div>
                            <div class="ml-3 text-right flex-shrink-0">
                                <p class="text-sm font-medium ${availabilityColor}">${org.availability_percentage}%</p>
                                <p class="text-xs text-gray-500">${org.pods.running} pods</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        // Mostrar dropdown con posicionamiento correcto
        this.elements.searchDropdown.classList.remove('hidden');
        
        // Posicionar correctamente el dropdown
        this.positionSearchDropdown();
        
        // Agregar event listeners a los resultados
        container.querySelectorAll('.search-result-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.selectOrganization(results[index]);
            });
            
            item.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.selectOrganization(results[index]);
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    const next = item.nextElementSibling;
                    if (next) next.focus();
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    const prev = item.previousElementSibling;
                    if (prev) {
                        prev.focus();
                    } else {
                        this.elements.organizationSearch.focus();
                    }
                } else if (e.key === 'Escape') {
                    this.hideSearchDropdown();
                    this.elements.organizationSearch.focus();
                }
            });
        });
    }

    /**
     * Resalta las coincidencias en el texto
     */
    highlightMatch(text, query) {
        if (!query) return text;
        
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<span class="bg-yellow-200 font-semibold">$1</span>');
    }

    /**
     * Selecciona una organización y muestra sus detalles
     */
    selectOrganization(org) {
        console.log('✅ Organización seleccionada:', org.organization_name);
        
        // Actualizar el input
        this.elements.organizationSearch.value = org.organization_name;
        
        // Ocultar dropdown
        this.hideSearchDropdown();
        
        // Mostrar detalles
        this.showOrganizationDetails(org);
        
        // Scroll hacia la organización en la lista principal si está visible
        this.highlightOrganizationInList(org);
    }

    /**
     * Muestra los detalles de la organización seleccionada
     */
    showOrganizationDetails(org) {
        const statusColor = this.getStatusColor(org.status);
        const availabilityColor = org.availability_percentage >= 95 ? 'text-green-600' : 
                                org.availability_percentage >= 90 ? 'text-yellow-600' : 'text-red-600';
        
        const incidentsHtml = org.related_incidents && org.related_incidents.length > 0 ? 
            `<div class="mt-3 pt-3 border-t border-blue-200">
                <h6 class="text-xs font-medium text-blue-700 mb-2">Incidentes Activos (${org.related_incidents.length}):</h6>
                ${org.related_incidents.map(incident => `
                    <div class="mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                        <a href="${incident.url}" target="_blank" class="text-red-700 hover:text-red-900 font-medium">${incident.title}</a>
                        <p class="text-red-600 mt-1">${new Date(incident.created_at).toLocaleDateString('es-MX', {
                            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                        })}</p>
                    </div>
                `).join('')}
            </div>` : 
            '<div class="mt-3 pt-3 border-t border-blue-200"><p class="text-xs text-green-700"><i class="fas fa-check-circle mr-1"></i>Sin incidentes activos</p></div>';

        this.elements.selectedOrgDetails.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                    <h5 class="font-medium text-blue-900 mb-2 flex items-center">
                        <div class="h-3 w-3 rounded-full ${statusColor} mr-2"></div>
                        ${org.organization_name}
                    </h5>
                    <p class="text-xs text-blue-700 mb-1"><strong>Clúster:</strong> ${org.cluster_name}</p>
                    <p class="text-xs text-blue-700 mb-1"><strong>UUID:</strong> ${org.uuid}</p>
                    <p class="text-xs text-blue-700"><strong>Estado:</strong> ${org.status}</p>
                </div>
                
                <div>
                    <h6 class="font-medium text-blue-900 mb-2">Disponibilidad</h6>
                    <p class="text-lg font-bold ${availabilityColor}">${org.availability_percentage}%</p>
                </div>
                
                <div>
                    <h6 class="font-medium text-blue-900 mb-2">Pods</h6>
                    <div class="grid grid-cols-2 gap-2 text-xs">
                        <div><span class="font-medium">Running:</span> ${org.pods.running}</div>
                        <div><span class="font-medium">Failed:</span> ${org.pods.failed}</div>
                        <div><span class="font-medium">Pending:</span> ${org.pods.pending || 0}</div>
                        <div><span class="font-medium">Reinicios:</span> ${org.pods.restarts}</div>
                    </div>
                </div>
            </div>
            ${incidentsHtml}
        `;
        
        this.elements.selectedOrganization.classList.remove('hidden');
    }

    /**
     * Oculta el dropdown de búsqueda
     */
    hideSearchDropdown() {
        this.elements.searchDropdown.classList.add('hidden');
    }

    /**
     * Posiciona correctamente el dropdown de búsqueda
     */
    positionSearchDropdown() {
        const dropdown = this.elements.searchDropdown;
        const input = this.elements.organizationSearch;
        
        if (!dropdown || !input) return;
        
        // Obtener dimensiones del input
        const inputRect = input.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        // Calcular espacio disponible abajo y arriba
        const spaceBelow = viewportHeight - inputRect.bottom;
        const spaceAbove = inputRect.top;
        
        // Resetear estilos
        dropdown.style.top = '';
        dropdown.style.bottom = '';
        dropdown.style.maxHeight = '';
        
        // Decidir posición basado en espacio disponible
        if (spaceBelow >= 240 || spaceBelow >= spaceAbove) {
            // Mostrar abajo del input
            dropdown.style.top = '100%';
            dropdown.style.maxHeight = Math.min(240, spaceBelow - 20) + 'px';
        } else {
            // Mostrar arriba del input
            dropdown.style.bottom = '100%';
            dropdown.style.maxHeight = Math.min(240, spaceAbove - 20) + 'px';
        }
        
        // Asegurar z-index alto
        dropdown.style.zIndex = '9999';
        dropdown.style.position = 'absolute';
        dropdown.style.width = '100%';
    }

    /**
     * Oculta los detalles de la organización seleccionada
     */
    hideSelectedOrganization() {
        this.elements.selectedOrganization.classList.add('hidden');
    }

    /**
     * Resalta la organización en la lista principal
     */
    highlightOrganizationInList(org) {
        // Remover highlights anteriores
        document.querySelectorAll('.organization-highlight').forEach(el => {
            el.classList.remove('organization-highlight', 'bg-blue-100', 'border-blue-300');
        });
        
        // Buscar y resaltar la organización en la lista
        const orgElements = document.querySelectorAll(`[data-org-uuid="${org.uuid}"]`);
        orgElements.forEach(el => {
            el.classList.add('organization-highlight', 'bg-blue-100', 'border-blue-300');
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
    }

    /**
     * Actualiza los datos de organizaciones para búsqueda
     */
    updateOrganizationsData(data) {
        console.log('🔍 Actualizando datos de organizaciones para búsqueda...');
        
        this.allOrganizations = [];
        
        if (data.clusters && Array.isArray(data.clusters)) {
            data.clusters.forEach(cluster => {
                if (cluster.namespaces && Array.isArray(cluster.namespaces)) {
                    cluster.namespaces.forEach(namespace => {
                        this.allOrganizations.push({
                            ...namespace,
                            cluster_name: cluster.name
                        });
                    });
                }
            });
        }
        
        console.log(`🔍 ${this.allOrganizations.length} organizaciones disponibles para búsqueda`);
    }

    /**
     * Muestra el estado de error
     */
    showError(message) {
        console.error('🚨 Mostrando error:', message);
        this.elements.loadingState.classList.add('hidden');
        this.elements.mainContent.classList.add('hidden');
        this.elements.errorState.classList.remove('hidden');
    }
}

// Función para intentar cargar Chart.js (opcional)
function tryToLoadChart() {
    return new Promise((resolve) => {
        let attempts = 0;
        const maxAttempts = 30; // 3 segundos máximo
        
        const checkChart = () => {
            attempts++;
            console.log(`📊 Verificando Chart.js... intento ${attempts}`);
            
            if (typeof Chart !== 'undefined') {
                console.log('✅ Chart.js está disponible');
                resolve(true);
            } else if (attempts >= maxAttempts) {
                console.warn('⚠️ Chart.js no disponible después de 3 segundos, continuando sin gráficos');
                resolve(false);
            } else {
                setTimeout(checkChart, 100);
            }
        };
        
        checkChart();
    });
}

// Inicializar dashboard cuando se carga la página
let dashboard;

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🌐 DOM Content Loaded - Verificando dependencias...');
    
    try {
        // Intentar cargar Chart.js (opcional)
        const chartAvailable = await tryToLoadChart();
        
        if (chartAvailable) {
            console.log('🚀 Chart.js disponible, inicializando dashboard completo...');
        } else {
            console.log('🚀 Inicializando dashboard sin gráficos...');
        }
        
        dashboard = new KubeHealthDashboard();
        console.log('✅ Dashboard creado exitosamente');
        
    } catch (error) {
        console.error('💥 Error al crear dashboard:', error);
        document.getElementById('loading-state').innerHTML = `
            <div class="text-center">
                <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-4">
                    <i class="fas fa-exclamation-triangle text-red-600 text-2xl"></i>
                </div>
                <h2 class="text-xl font-semibold text-gray-900 mb-2">Error de Inicialización</h2>
                <p class="text-gray-500 text-sm mb-4">${error.message}</p>
                <button onclick="window.location.reload()" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700">
                    <i class="fas fa-redo mr-2"></i>
                    Reintentar
                </button>
            </div>
        `;
    }
});

// Hacer disponible globalmente para debugging
window.dashboard = dashboard; 