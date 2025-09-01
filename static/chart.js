// Phase 5B5: Advanced Chart Management System
// Create this as static/charts.js for comprehensive chart functionality

class InventoryChartsManager {
    constructor() {
        this.charts = {};
        this.chartConfig = {
            colors: {
                primary: '#3498db',
                success: '#27ae60',
                warning: '#f39c12',
                danger: '#e74c3c',
                info: '#9b59b6',
                secondary: '#95a5a6',
                light: '#ecf0f1',
                dark: '#2c3e50'
            },
            animation: {
                duration: 1200,
                easing: 'easeInOutQuart'
            }
        };
        
        this.isInitialized = false;
        this.updateInterval = null;
    }

    // Initialize all charts when dashboard loads
    async initialize() {
        try {
            console.log('🚀 Initializing Inventory Charts Manager...');
            
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeCharts());
            } else {
                this.initializeCharts();
            }
            
            this.isInitialized = true;
            console.log('✅ Chart Manager initialized successfully');
            
        } catch (error) {
            console.error('❌ Error initializing Chart Manager:', error);
        }
    }

    async initializeCharts() {
        // Initialize each chart with error handling
        await this.initStockDistributionChart();
        await this.initTopProductsChart();
        await this.initActivityTrendChart();
        await this.initAlertDistributionChart();
        await this.initSupplierPerformanceChart();
        await this.initInventoryValueChart();
        
        // Setup auto-refresh for real-time updates
        this.setupAutoRefresh();
        
        // Setup event listeners
        this.setupEventListeners();
    }

    // Stock Distribution Pie Chart with Enhanced Interactivity
    async initStockDistributionChart() {
        try {
            const ctx = document.getElementById('stockDistributionChart');
            if (!ctx) return;

            const response = await fetch('/api/charts/stock_distribution');
            const data = await response.json();

            this.charts.stockDistribution = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.datasets[0].data,
                        backgroundColor: [
                            this.chartConfig.colors.success,
                            this.chartConfig.colors.warning,
                            this.chartConfig.colors.danger
                        ],
                        borderWidth: 4,
                        borderColor: '#ffffff',
                        hoverBorderWidth: 6,
                        hoverOffset: 10
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '60%',
                    plugins: {
                        legend: {
                            display: false // Using custom legend
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const total = data.total;
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return `${context.label}: ${context.parsed} products (${percentage}%)`;
                                }
                            },
                            backgroundColor: 'rgba(44, 62, 80, 0.95)',
                            titleColor: '#ffffff',
                            bodyColor: '#ffffff',
                            cornerRadius: 8,
                            padding: 12
                        }
                    },
                    animation: this.chartConfig.animation,
                    onHover: (event, elements) => {
                        ctx.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = data.labels[index];
                            this.handleStockDistributionClick(label);
                        }
                    }
                }
            });

            console.log('✅ Stock Distribution Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Stock Distribution Chart:', error);
            this.showChartError('stockDistributionChart', 'Stock Distribution');
        }
    }

    // Top Products Bar Chart with Drill-Down Capability
    async initTopProductsChart() {
        try {
            const ctx = document.getElementById('topProductsChart');
            if (!ctx) return;

            const response = await fetch('/api/charts/top_products');
            const data = await response.json();

            this.charts.topProducts = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Inventory Value',
                        data: data.datasets[0].data,
                        backgroundColor: this.createGradient(ctx, this.chartConfig.colors.primary),
                        borderColor: this.chartConfig.colors.dark,
                        borderWidth: 1,
                        borderRadius: 6,
                        borderSkipped: false,
                        hoverBackgroundColor: this.chartConfig.colors.info,
                        hoverBorderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                title: (context) => {
                                    const index = context[0].dataIndex;
                                    return data.products[index].name;
                                },
                                label: (context) => {
                                    const index = context.dataIndex;
                                    const product = data.products[index];
                                    return [
                                        `SKU: ${product.sku}`,
                                        `Quantity: ${product.quantity.toLocaleString()} units`,
                                        `Unit Price: ${this.formatCurrency(product.price)}`,
                                        `Total Value: ${this.formatCurrency(product.value)}`
                                    ];
                                }
                            },
                            backgroundColor: 'rgba(44, 62, 80, 0.95)',
                            multiKeyBackground: '#ffffff'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => this.formatCurrency(value)
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            ticks: {
                                maxRotation: 45,
                                font: {
                                    size: 11
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    },
                    animation: this.chartConfig.animation,
                    onHover: (event, elements) => {
                        ctx.style.cursor = elements.length > 0 ? 'pointer' : 'default';
                    },
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const product = data.products[index];
                            this.handleProductClick(product);
                        }
                    }
                }
            });

            console.log('✅ Top Products Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Top Products Chart:', error);
            this.showChartError('topProductsChart', 'Top Products');
        }
    }

    // Transaction Activity Line Chart with Time Period Selection
    async initActivityTrendChart() {
        try {
            const ctx = document.getElementById('activityChart');
            if (!ctx) return;

            const period = document.getElementById('activityPeriod')?.value || 7;
            const response = await fetch(`/api/charts/transaction_activity?period=${period}`);
            const data = await response.json();

            this.charts.activity = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: data.datasets.map((dataset, index) => ({
                        ...dataset,
                        borderColor: [
                            this.chartConfig.colors.primary,
                            this.chartConfig.colors.success,
                            this.chartConfig.colors.danger
                        ][index],
                        backgroundColor: [
                            this.chartConfig.colors.primary + '20',
                            this.chartConfig.colors.success + '20',
                            this.chartConfig.colors.danger + '20'
                        ][index],
                        pointBackgroundColor: [
                            this.chartConfig.colors.primary,
                            this.chartConfig.colors.success,
                            this.chartConfig.colors.danger
                        ][index],
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 8,
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'top',
                            labels: {
                                usePointStyle: true,
                                padding: 20
                            }
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            backgroundColor: 'rgba(44, 62, 80, 0.95)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,
                                callback: (value) => Math.floor(value).toString()
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.05)'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    animation: this.chartConfig.animation
                }
            });

            console.log('✅ Transaction Activity Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Activity Chart:', error);
            this.showChartError('activityChart', 'Transaction Activity');
        }
    }

    // Alert Distribution Doughnut Chart
    async initAlertDistributionChart() {
        try {
            const ctx = document.getElementById('alertsChart');
            if (!ctx) return;

            const response = await fetch('/api/charts/alert_distribution');
            const data = await response.json();

            this.charts.alerts = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.datasets[0].data,
                        backgroundColor: data.datasets[0].backgroundColor,
                        borderWidth: 3,
                        borderColor: '#ffffff',
                        hoverOffset: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    cutout: '50%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                usePointStyle: true,
                                font: {
                                    size: 12
                                }
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const total = data.details.total;
                                    const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                                    return `${context.label}: ${context.parsed} products (${percentage}%)`;
                                }
                            },
                            backgroundColor: 'rgba(44, 62, 80, 0.95)'
                        }
                    },
                    animation: this.chartConfig.animation,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const label = data.labels[index];
                            this.handleAlertClick(label);
                        }
                    }
                }
            });

            console.log('✅ Alert Distribution Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Alert Chart:', error);
            this.showChartError('alertsChart', 'Alert Distribution');
        }
    }

    // Supplier Performance Horizontal Bar Chart
    async initSupplierPerformanceChart() {
        try {
            const ctx = document.getElementById('suppliersChart');
            if (!ctx) return;

            const response = await fetch('/api/charts/supplier_performance');
            const data = await response.json();

            this.charts.suppliers = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Inventory Value',
                        data: data.datasets[0].data,
                        backgroundColor: this.createGradient(ctx, this.chartConfig.colors.info),
                        borderColor: this.chartConfig.colors.dark,
                        borderWidth: 1,
                        borderRadius: 4,
                        hoverBackgroundColor: this.chartConfig.colors.primary
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => {
                                    const index = context.dataIndex;
                                    const supplier = data.suppliers[index];
                                    return [
                                        `Inventory Value: ${this.formatCurrency(supplier.value)}`,
                                        `Products: ${supplier.products}`,
                                        `Total Stock: ${supplier.stock.toLocaleString()} units`
                                    ];
                                }
                            },
                            backgroundColor: 'rgba(44, 62, 80, 0.95)'
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: {
                                callback: (value) => this.formatCurrency(value)
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        y: {
                            grid: {
                                display: false
                            }
                        }
                    },
                    animation: this.chartConfig.animation,
                    onClick: (event, elements) => {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const supplier = data.suppliers[index];
                            this.handleSupplierClick(supplier);
                        }
                    }
                }
            });

            console.log('✅ Supplier Performance Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Supplier Chart:', error);
            this.showChartError('suppliersChart', 'Supplier Performance');
        }
    }

    // Inventory Value Trend Line Chart with Period Selection
    async initInventoryValueChart() {
        try {
            const ctx = document.getElementById('valueChart');
            if (!ctx) return;

            const period = document.getElementById('valuePeriod')?.value || 7;
            const response = await fetch(`/api/charts/inventory_value_trend?period=${period}`);
            const data = await response.json();

            this.charts.value = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: data.datasets[0].label,
                        data: data.datasets[0].data,
                        borderColor: this.chartConfig.colors.success,
                        backgroundColor: this.createGradient(ctx, this.chartConfig.colors.success, true),
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: this.chartConfig.colors.success,
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 3,
                        pointRadius: 6,
                        pointHoverRadius: 10,
                        pointHoverBorderWidth: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => `Total Value: ${this.formatCurrency(context.parsed.y)}`
                            },
                            backgroundColor: 'rgba(44, 62, 80, 0.95)'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: (value) => this.formatCurrency(value)
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.1)'
                            }
                        },
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.05)'
                            }
                        }
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    animation: this.chartConfig.animation
                }
            });

            console.log('✅ Inventory Value Chart initialized');
        } catch (error) {
            console.error('❌ Error initializing Value Chart:', error);
            this.showChartError('valueChart', 'Inventory Value Trend');
        }
    }

    // Enhanced Chart Refresh with Real-Time Data
    async refreshChart(chartName) {
        try {
            const chart = this.charts[chartName];
            if (!chart) {
                console.warn(`Chart ${chartName} not found`);
                return;
            }

            console.log(`🔄 Refreshing ${chartName} chart...`);
            
            // Show loading state
            this.showChartLoading(chartName);
            
            let apiEndpoint;
            switch(chartName) {
                case 'stockDistribution':
                    apiEndpoint = '/api/charts/stock_distribution';
                    break;
                case 'topProducts':
                    apiEndpoint = '/api/charts/top_products';
                    break;
                case 'activity':
                    const period = document.getElementById('activityPeriod')?.value || 7;
                    apiEndpoint = `/api/charts/transaction_activity?period=${period}`;
                    break;
                case 'alerts':
                    apiEndpoint = '/api/charts/alert_distribution';
                    break;
                case 'suppliers':
                    apiEndpoint = '/api/charts/supplier_performance';
                    break;
                case 'value':
                    const valuePeriod = document.getElementById('valuePeriod')?.value || 7;
                    apiEndpoint = `/api/charts/inventory_value_trend?period=${valuePeriod}`;
                    break;
                default:
                    throw new Error(`Unknown chart type: ${chartName}`);
            }

            const response = await fetch(apiEndpoint);
            const newData = await response.json();

            // Update chart data
            chart.data.labels = newData.labels;
            chart.data.datasets = newData.datasets;
            chart.update('active');

            // Hide loading state
            this.hideChartLoading(chartName);
            
            console.log(`✅ ${chartName} chart refreshed successfully`);
            
        } catch (error) {
            console.error(`❌ Error refreshing ${chartName} chart:`, error);
            this.hideChartLoading(chartName);
        }
    }

    // Auto-refresh setup for real-time updates
    setupAutoRefresh() {
        // Auto-refresh every 5 minutes
        this.updateInterval = setInterval(() => {
            this.refreshAllCharts();
        }, 300000); // 5 minutes

        console.log('⏰ Auto-refresh enabled (5 minute intervals)');
    }

    async refreshAllCharts() {
        console.log('🔄 Refreshing all charts...');
        
        const chartNames = Object.keys(this.charts);
        const refreshPromises = chartNames.map(name => this.refreshChart(name));
        
        try {
            await Promise.all(refreshPromises);
            console.log('✅ All charts refreshed successfully');
            
            // Show success notification
            this.showNotification('Charts updated with latest data', 'success');
        } catch (error) {
            console.error('❌ Error refreshing charts:', error);
            this.showNotification('Some charts failed to update', 'error');
        }
    }

    // Event Handlers for Chart Interactions
    handleStockDistributionClick(stockStatus) {
        console.log(`📊 Stock distribution clicked: ${stockStatus}`);
        
        // Navigate to filtered products view
        let filterParam;
        switch(stockStatus.toLowerCase()) {
            case 'in stock':
                filterParam = 'in_stock';
                break;
            case 'low stock':
                filterParam = 'low_stock';
                break;
            case 'out of stock':
                filterParam = 'out_of_stock';
                break;
        }
        
        if (filterParam) {
            window.location.href = `/products?filter=${filterParam}`;
        }
    }

    handleProductClick(product) {
        console.log(`📦 Product clicked: ${product.name}`);
        
        // Show product details modal or navigate to product page
        if (confirm(`View details for "${product.name}"?\n\nSKU: ${product.sku}\nCurrent Stock: ${product.quantity}\nValue: ${this.formatCurrency(product.value)}`)) {
            // In a real implementation, you might open a modal or navigate to product details
            window.location.href = `/products?search=${product.sku}`;
        }
    }

    handleAlertClick(alertLevel) {
        console.log(`⚠️ Alert level clicked: ${alertLevel}`);
        
        if (alertLevel.toLowerCase() !== 'well stocked') {
            // Navigate to alerts dashboard
            window.location.href = '/alerts';
        }
    }

    handleSupplierClick(supplier) {
        console.log(`🏢 Supplier clicked: ${supplier.name}`);
        
        if (confirm(`View supplier details for "${supplier.name}"?\n\nProducts: ${supplier.products}\nInventory Value: ${this.formatCurrency(supplier.value)}`)) {
            // Navigate to suppliers page (in future, might be supplier details page)
            window.location.href = '/suppliers';
        }
    }

    // Utility Functions
    createGradient(ctx, color, vertical = false) {
        const gradient = ctx.createLinearGradient(0, 0, vertical ? 0 : ctx.canvas.width, vertical ? ctx.canvas.height : 0);
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, color + '60');
        return gradient;
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    showChartLoading(chartName) {
        const container = document.getElementById(chartName)?.closest('.chart-container');
        if (container) {
            container.style.opacity = '0.6';
            container.style.pointerEvents = 'none';
        }
    }

    hideChartLoading(chartName) {
        const container = document.getElementById(chartName)?.closest('.chart-container');
        if (container) {
            container.style.opacity = '1';
            container.style.pointerEvents = 'auto';
        }
    }

    showChartError(canvasId, chartName) {
        const canvas = document.getElementById(canvasId);
        if (canvas) {
            const container = canvas.closest('.chart-container');
            container.innerHTML = `
                <div class="chart-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-message">
                        <strong>Chart Loading Error</strong><br>
                        Unable to load ${chartName} chart. Please refresh the page.
                    </div>
                </div>
            `;
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `chart-notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Setup Event Listeners
    setupEventListeners() {
        // Period change handlers
        const activityPeriod = document.getElementById('activityPeriod');
        if (activityPeriod) {
            activityPeriod.addEventListener('change', () => {
                this.refreshChart('activity');
            });
        }

        const valuePeriod = document.getElementById('valuePeriod');
        if (valuePeriod) {
            valuePeriod.addEventListener('change', () => {
                this.refreshChart('value');
            });
        }

        // Refresh button handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh-chart]')) {
                const chartName = e.target.getAttribute('data-refresh-chart');
                this.refreshChart(chartName);
                
                // Visual feedback
                e.target.disabled = true;
                e.target.innerHTML = '⏳';
                
                setTimeout(() => {
                    e.target.innerHTML = '✅';
                    setTimeout(() => {
                        e.target.innerHTML = '🔄';
                        e.target.disabled = false;
                    }, 500);
                }, 1000);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshAllCharts();
                        break;
                }
            }
        });

        console.log('✅ Event listeners configured');
    }

    // Cleanup function
    destroy() {
        // Clear auto-refresh interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Destroy all chart instances
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });

        this.charts = {};
        this.isInitialized = false;
        
        console.log('🧹 Charts Manager cleaned up');
    }
}

// Global chart manager instance
window.chartsManager = new InventoryChartsManager();

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on dashboard page
    if (window.location.pathname === '/dashboard') {
        window.chartsManager.initialize();
    }
});

// Global functions for template compatibility
window.refreshChart = function(chartName) {
    if (window.chartsManager && window.chartsManager.isInitialized) {
        window.chartsManager.refreshChart(chartName);
    }
};

window.updateActivityChart = function() {
    if (window.chartsManager && window.chartsManager.isInitialized) {
        window.chartsManager.refreshChart('activity');
    }
};

window.updateValueChart = function() {
    if (window.chartsManager && window.chartsManager.isInitialized) {
        window.chartsManager.refreshChart('value');
    }
};

// Additional utility functions for chart management
window.ChartUtils = {
    // Export chart as image
    exportChart: function(chartName, filename) {
        const chart = window.chartsManager.charts[chartName];
        if (chart) {
            const url = chart.toBase64Image('image/png', 1.0);
            const link = document.createElement('a');
            link.download = filename || `${chartName}_chart.png`;
            link.href = url;
            link.click();
        }
    },

    // Print chart
    printChart: function(chartName) {
        const chart = window.chartsManager.charts[chartName];
        if (chart) {
            const imageUrl = chart.toBase64Image('image/png', 1.0);
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Chart Print</title>
                    <style>
                        body { margin: 0; padding: 20px; text-align: center; }
                        img { max-width: 100%; height: auto; }
                        .print-header { margin-bottom: 20px; color: #2c3e50; }
                    </style>
                </head>
                <body>
                    <div class="print-header">
                        <h2>Inventory Management Chart</h2>
                        <p>Generated: ${new Date().toLocaleString()}</p>
                    </div>
                    <img src="${imageUrl}" alt="${chartName} Chart">
                </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    },

    // Get chart data summary
    getChartSummary: function(chartName) {
        const chart = window.chartsManager.charts[chartName];
        if (chart) {
            return {
                type: chart.config.type,
                datasets: chart.data.datasets.length,
                dataPoints: chart.data.labels.length,
                lastUpdated: new Date().toISOString()
            };
        }
        return null;
    }
};

console.log('📊 Advanced Chart Management System Loaded');
console.log('🎯 Features: Real-time updates, Interactive drilling, Mobile responsive, Error handling');
console.log('⌨️  Keyboard shortcuts: Ctrl+R (Refresh all charts)');