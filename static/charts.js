// Phase 5 Consolidated: Advanced Chart Management System with Real-Time API Integration
// File: static/charts.js

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
        this.retryCount = {};
        this.maxRetries = 3;
    }

    // Initialize all charts when dashboard loads
    async initialize() {
        try {
            console.log('🚀 Initializing Inventory Charts Manager...');
            
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
        // Initialize each chart with comprehensive error handling
        const initPromises = [
            this.initStockDistributionChart(),
            this.initTopProductsChart(),
            this.initActivityTrendChart(),
            this.initAlertDistributionChart(),
            this.initSupplierPerformanceChart(),
            this.initInventoryValueChart()
        ];

        // Initialize charts concurrently but handle errors gracefully
        const results = await Promise.allSettled(initPromises);
        
        let successCount = 0;
        results.forEach((result, index) => {
            if (result.status === 'fulfilled') {
                successCount++;
            } else {
                console.error(`Chart ${index} failed to initialize:`, result.reason);
            }
        });

        console.log(`📊 Charts initialized: ${successCount}/${results.length} successful`);
        
        // Setup additional features
        this.setupAutoRefresh();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
    }

    // Stock Distribution Chart with Enhanced API Integration
    async initStockDistributionChart() {
        try {
            const ctx = document.getElementById('stockDistributionChart');
            if (!ctx) return;

            const data = await this.fetchChartData('/api/charts/stock_distribution');
            if (!data) throw new Error('Failed to fetch stock distribution data');

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
                            display: false
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

    // Top Products Chart with Real-Time API Data
    async initTopProductsChart() {
        try {
            const ctx = document.getElementById('topProductsChart');
            if (!ctx) return;

            const data = await this.fetchChartData('/api/charts/top_products');
            if (!data) throw new Error('Failed to fetch top products data');

            this.charts.topProducts = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Inventory Value',
                        data: data.datasets[0].data,
                        backgroundColor: '#3498db', // Use solid color instead of gradient for now
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

    // Transaction Activity Chart with API Integration
    async initActivityTrendChart() {
        try {
            const ctx = document.getElementById('activityChart');
            if (!ctx) return;

            const period = document.getElementById('activityPeriod')?.value || 7;
            const data = await this.fetchChartData(`/api/charts/transaction_activity?period=${period}`);
            if (!data) throw new Error('Failed to fetch activity data');

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

    // Alert Distribution Chart with API Integration
    async initAlertDistributionChart() {
        try {
            const ctx = document.getElementById('alertsChart');
            if (!ctx) return;

            const data = await this.fetchChartData('/api/charts/alert_distribution');
            if (!data) throw new Error('Failed to fetch alert data');

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

    // Supplier Performance Chart with API Integration
    async initSupplierPerformanceChart() {
        try {
            const ctx = document.getElementById('suppliersChart');
            if (!ctx) return;

            const data = await this.fetchChartData('/api/charts/supplier_performance');
            if (!data) throw new Error('Failed to fetch supplier data');

            this.charts.suppliers = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Inventory Value',
                        data: data.datasets[0].data,
                        backgroundColor: this.chartConfig.colors.info, // Use solid color instead of gradient
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

    // Inventory Value Trend Chart with API Integration  
    async initInventoryValueChart() {
        try {
            const ctx = document.getElementById('valueChart');
            if (!ctx) return;

            const period = document.getElementById('valuePeriod')?.value || 7;
            const data = await this.fetchChartData(`/api/charts/inventory_value_trend?period=${period}`);
            if (!data) throw new Error('Failed to fetch value trend data');

            this.charts.value = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: data.datasets[0].label,
                        data: data.datasets[0].data,
                        borderColor: this.chartConfig.colors.success,
                        backgroundColor: this.chartConfig.colors.success + '20', // Use hex opacity instead of gradient
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

    // Enhanced Chart Refresh with Retry Logic
    async refreshChart(chartName) {
        try {
            const chart = this.charts[chartName];
            if (!chart) {
                console.warn(`Chart ${chartName} not found`);
                return;
            }

            console.log(`🔄 Refreshing ${chartName} chart...`);
            
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

            const newData = await this.fetchChartData(apiEndpoint);
            if (!newData) throw new Error('Failed to fetch updated data');

            // Update chart data with smooth animation
            chart.data.labels = newData.labels;
            chart.data.datasets = newData.datasets;
            chart.update('active');

            this.hideChartLoading(chartName);
            this.resetRetryCount(chartName);
            
            console.log(`✅ ${chartName} chart refreshed successfully`);
            
        } catch (error) {
            console.error(`❌ Error refreshing ${chartName} chart:`, error);
            this.handleChartRefreshError(chartName, error);
        }
    }

    // Auto-refresh with intelligent intervals
    setupAutoRefresh() {
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
            await Promise.allSettled(refreshPromises);
            console.log('✅ All charts refresh completed');
            this.showNotification('Charts updated with latest data', 'success');
        } catch (error) {
            console.error('❌ Error during bulk refresh:', error);
            this.showNotification('Some charts failed to update', 'error');
        }
    }

    // Enhanced API data fetching with retry logic
    async fetchChartData(endpoint) {
        const retryKey = endpoint;
        this.retryCount[retryKey] = this.retryCount[retryKey] || 0;

        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.retryCount[retryKey] = 0; // Reset on success
            return data;
            
        } catch (error) {
            console.error(`Error fetching data from ${endpoint}:`, error);
            
            if (this.retryCount[retryKey] < this.maxRetries) {
                this.retryCount[retryKey]++;
                console.log(`🔄 Retrying ${endpoint} (attempt ${this.retryCount[retryKey]}/${this.maxRetries})`);
                
                // Exponential backoff
                await new Promise(resolve => setTimeout(resolve, 1000 * this.retryCount[retryKey]));
                return this.fetchChartData(endpoint);
            }
            
            return null;
        }
    }

    // Event Handlers for Chart Interactions
    handleStockDistributionClick(stockStatus) {
        console.log(`📊 Stock distribution clicked: ${stockStatus}`);
        
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
        
        if (confirm(`View details for "${product.name}"?\n\nSKU: ${product.sku}\nCurrent Stock: ${product.quantity}\nValue: ${this.formatCurrency(product.value)}`)) {
            window.location.href = `/products?search=${product.sku}`;
        }
    }

    handleAlertClick(alertLevel) {
        console.log(`⚠️ Alert level clicked: ${alertLevel}`);
        
        if (alertLevel.toLowerCase() !== 'well stocked') {
            window.location.href = '/alerts';
        }
    }

    handleSupplierClick(supplier) {
        console.log(`🏢 Supplier clicked: ${supplier.name}`);
        
        if (confirm(`View supplier details for "${supplier.name}"?\n\nProducts: ${supplier.products}\nInventory Value: ${this.formatCurrency(supplier.value)}`)) {
            window.location.href = '/suppliers';
        }
    }

    // Advanced Event Listeners
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

        // Enhanced refresh button handlers
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh-chart]')) {
                const chartName = e.target.getAttribute('data-refresh-chart');
                this.refreshChart(chartName);
                
                // Enhanced visual feedback
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

        // Global refresh button
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-refresh-all]')) {
                this.refreshAllCharts();
                this.showNotification('Refreshing all charts...', 'info');
            }
        });

        console.log('✅ Event listeners configured');
    }

    // Keyboard Shortcuts for Power Users
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'r':
                        e.preventDefault();
                        this.refreshAllCharts();
                        this.showNotification('Charts refreshed via keyboard shortcut', 'success');
                        break;
                    case '1':
                        e.preventDefault();
                        this.refreshChart('stockDistribution');
                        break;
                    case '2':
                        e.preventDefault();
                        this.refreshChart('topProducts');
                        break;
                    case '3':
                        e.preventDefault();
                        this.refreshChart('activity');
                        break;
                }
            }
        });

        console.log('⌨️ Keyboard shortcuts enabled (Ctrl+R: refresh all, Ctrl+1-3: refresh specific charts)');
    }

    // Advanced Analytics Methods (Phase 5D Elements)
    async calculateTrends() {
        try {
            const data = await this.fetchChartData('/api/charts/refresh_all');
            if (!data) return null;

            const analytics = {
                stockHealth: this.analyzeStockHealth(data.stock_distribution),
                performanceTrends: this.analyzePerformanceTrends(data.transaction_activity),
                supplierInsights: this.analyzeSupplierInsights(data.supplier_performance),
                predictions: this.generatePredictions(data)
            };

            return analytics;
        } catch (error) {
            console.error('Error calculating trends:', error);
            return null;
        }
    }

    analyzeStockHealth(stockData) {
        const total = stockData.total;
        const inStock = stockData.datasets[0].data[0];
        const lowStock = stockData.datasets[0].data[1];
        const outOfStock = stockData.datasets[0].data[2];

        const healthScore = total > 0 ? ((inStock / total) * 100) : 0;
        
        return {
            score: healthScore,
            status: healthScore > 80 ? 'Excellent' : healthScore > 60 ? 'Good' : healthScore > 40 ? 'Fair' : 'Poor',
            recommendations: this.generateStockRecommendations(healthScore, { inStock, lowStock, outOfStock })
        };
    }

    analyzePerformanceTrends(activityData) {
        const recentData = activityData.datasets[0].data;
        const trend = this.calculateTrendDirection(recentData);
        
        return {
            direction: trend.direction,
            strength: trend.strength,
            summary: `Activity is ${trend.direction} with ${trend.strength} momentum`
        };
    }

    analyzeSupplierInsights(supplierData) {
        const suppliers = supplierData.suppliers || [];
        const topSupplier = suppliers[0];
        const supplierConcentration = suppliers.length > 0 ? (topSupplier.value / suppliers.reduce((sum, s) => sum + s.value, 0)) * 100 : 0;

        return {
            concentration: supplierConcentration,
            riskLevel: supplierConcentration > 50 ? 'High' : supplierConcentration > 30 ? 'Medium' : 'Low',
            topSupplier: topSupplier?.name || 'None',
            recommendation: this.generateSupplierRecommendation(supplierConcentration)
        };
    }

    generatePredictions(allData) {
        // Simplified prediction logic (in production, use more sophisticated algorithms)
        return {
            stockoutRisk: this.predictStockoutRisk(allData),
            restockNeeds: this.predictRestockNeeds(allData),
            valueProjection: this.projectInventoryValue(allData)
        };
    }

    // Utility Functions
    createGradient(ctx, color, vertical = false) {
        // Safety check for canvas availability
        if (!ctx || !ctx.canvas) {
            console.warn('Canvas context not available, using solid color');
            return color;
        }
        
        try {
            const canvas = ctx.canvas;
            const gradient = ctx.createLinearGradient(
                0, 0, 
                vertical ? 0 : canvas.width, 
                vertical ? canvas.height : 0
            );
            gradient.addColorStop(0, color);
            gradient.addColorStop(1, color + '60');
            return gradient;
        } catch (error) {
            console.warn('Gradient creation failed, using solid color:', error);
            return color;
        }
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
            
            // Add loading spinner if not exists
            let spinner = container.querySelector('.loading-spinner');
            if (!spinner) {
                spinner = document.createElement('div');
                spinner.className = 'loading-spinner';
                spinner.innerHTML = '⏳';
                spinner.style.cssText = `
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    font-size: 2rem;
                    z-index: 1000;
                `;
                container.appendChild(spinner);
            }
        }
    }

    hideChartLoading(chartName) {
        const container = document.getElementById(chartName)?.closest('.chart-container');
        if (container) {
            container.style.opacity = '1';
            container.style.pointerEvents = 'auto';
            
            const spinner = container.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
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
                        Unable to load ${chartName} chart.<br>
                        <button onclick="window.chartsManager.refreshChart('${canvasId.replace('Chart', '')}')" class="btn btn-small btn-primary" style="margin-top: 1rem;">
                            🔄 Retry
                        </button>
                    </div>
                </div>
            `;
        }
    }

    showNotification(message, type = 'info') {
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
        
        // Enhanced notification styling
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-left: 4px solid ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            padding: 1rem;
            z-index: 10000;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 4000);
    }

    // Error handling utilities
    handleChartRefreshError(chartName, error) {
        this.hideChartLoading(chartName);
        
        if (this.retryCount[chartName] < this.maxRetries) {
            this.retryCount[chartName] = (this.retryCount[chartName] || 0) + 1;
            console.log(`🔄 Retrying ${chartName} refresh (${this.retryCount[chartName]}/${this.maxRetries})`);
            
            setTimeout(() => {
                this.refreshChart(chartName);
            }, 2000 * this.retryCount[chartName]);
        } else {
            this.showNotification(`Failed to refresh ${chartName} chart`, 'error');
        }
    }

    resetRetryCount(chartName) {
        if (this.retryCount[chartName]) {
            delete this.retryCount[chartName];
        }
    }

    // Advanced analytics helper methods
    calculateTrendDirection(data) {
        if (data.length < 2) return { direction: 'stable', strength: 'weak' };
        
        const firstHalf = data.slice(0, Math.floor(data.length / 2));
        const secondHalf = data.slice(Math.floor(data.length / 2));
        
        const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
        const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
        
        const change = ((secondAvg - firstAvg) / firstAvg) * 100;
        
        return {
            direction: change > 5 ? 'increasing' : change < -5 ? 'decreasing' : 'stable',
            strength: Math.abs(change) > 20 ? 'strong' : Math.abs(change) > 10 ? 'moderate' : 'weak'
        };
    }

    generateStockRecommendations(healthScore, stocks) {
        const recommendations = [];
        
        if (healthScore < 60) {
            recommendations.push('Consider increasing minimum stock levels');
        }
        if (stocks.outOfStock > 0) {
            recommendations.push(`${stocks.outOfStock} products need immediate restocking`);
        }
        if (stocks.lowStock > stocks.inStock * 0.3) {
            recommendations.push('Review reorder points for better stock management');
        }
        
        return recommendations.length > 0 ? recommendations : ['Stock levels are well managed'];
    }

    generateSupplierRecommendation(concentration) {
        if (concentration > 50) {
            return 'Consider diversifying suppliers to reduce risk';
        } else if (concentration > 30) {
            return 'Supplier concentration is moderate - monitor dependency';
        } else {
            return 'Good supplier diversification maintained';
        }
    }

    predictStockoutRisk(data) {
        // Simplified risk assessment
        const stockData = data.stock_distribution;
        const total = stockData.total;
        const outOfStock = stockData.datasets[0].data[2];
        const lowStock = stockData.datasets[0].data[1];
        
        const riskScore = total > 0 ? ((outOfStock + lowStock) / total) * 100 : 0;
        
        return {
            score: riskScore,
            level: riskScore > 30 ? 'High' : riskScore > 15 ? 'Medium' : 'Low'
        };
    }

    predictRestockNeeds(data) {
        // Generate restock predictions based on current data
        return {
            urgentRestocks: data.alert_distribution?.details?.critical || 0,
            plannedRestocks: data.alert_distribution?.details?.warning || 0,
            timeline: 'Next 7-14 days'
        };
    }

    projectInventoryValue(data) {
        const currentValue = data.inventory_value_trend?.datasets[0]?.data?.slice(-1)[0] || 0;
        const trend = this.calculateTrendDirection(data.inventory_value_trend?.datasets[0]?.data || []);
        
        let projectedChange = 0;
        if (trend.direction === 'increasing') {
            projectedChange = trend.strength === 'strong' ? 0.15 : trend.strength === 'moderate' ? 0.08 : 0.03;
        } else if (trend.direction === 'decreasing') {
            projectedChange = trend.strength === 'strong' ? -0.15 : trend.strength === 'moderate' ? -0.08 : -0.03;
        }
        
        return {
            current: currentValue,
            projected: currentValue * (1 + projectedChange),
            change: projectedChange * 100,
            confidence: trend.strength === 'strong' ? 'High' : trend.strength === 'moderate' ? 'Medium' : 'Low'
        };
    }

    // Export and utility functions
    exportChart(chartName, filename) {
        const chart = this.charts[chartName];
        if (chart) {
            const url = chart.toBase64Image('image/png', 1.0);
            const link = document.createElement('a');
            link.download = filename || `${chartName}_chart_${new Date().toISOString().slice(0, 10)}.png`;
            link.href = url;
            link.click();
            
            this.showNotification(`Chart exported: ${link.download}`, 'success');
        }
    }

    getSystemHealth() {
        return {
            chartsInitialized: Object.keys(this.charts).length,
            autoRefreshActive: !!this.updateInterval,
            lastUpdate: new Date().toISOString(),
            systemStatus: this.isInitialized ? 'Operational' : 'Initializing'
        };
    }

    // Cleanup function
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

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
    if (window.location.pathname === '/dashboard') {
        window.chartsManager.initialize();
    }
});

// Global functions for backward compatibility
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

// Advanced Chart Utilities
window.ChartUtils = {
    exportChart: function(chartName, filename) {
        window.chartsManager.exportChart(chartName, filename);
    },

    printChart: function(chartName) {
        const chart = window.chartsManager.charts[chartName];
        if (chart) {
            const imageUrl = chart.toBase64Image('image/png', 1.0);
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Inventory Chart - ${chartName}</title>
                    <style>
                        body { margin: 0; padding: 20px; text-align: center; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                        img { max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 8px; }
                        .print-header { margin-bottom: 20px; color: #2c3e50; }
                        .print-footer { margin-top: 20px; color: #7f8c8d; font-size: 0.9rem; }
                    </style>
                </head>
                <body>
                    <div class="print-header">
                        <h2>Inventory Management System</h2>
                        <h3>${chartName.charAt(0).toUpperCase() + chartName.slice(1)} Chart</h3>
                        <p>Generated: ${new Date().toLocaleString()}</p>
                    </div>
                    <img src="${imageUrl}" alt="${chartName} Chart">
                    <div class="print-footer">
                        <p>Professional Inventory Management System - Advanced Analytics Dashboard</p>
                    </div>
                </body>
                </html>
            `);
            printWindow.document.close();
            setTimeout(() => printWindow.print(), 500);
        }
    },

    getChartSummary: function(chartName) {
        const chart = window.chartsManager.charts[chartName];
        if (chart) {
            return {
                type: chart.config.type,
                datasets: chart.data.datasets.length,
                dataPoints: chart.data.labels.length,
                lastUpdated: new Date().toISOString(),
                isResponsive: chart.options.responsive
            };
        }
        return null;
    },

    getSystemHealth: function() {
        return window.chartsManager.getSystemHealth();
    },

    // Advanced analytics access
    getAnalytics: async function() {
        return await window.chartsManager.calculateTrends();
    }
};

// Performance monitoring
console.log('📊 Advanced Chart Management System Loaded');
console.log('🎯 Features: Real-time API integration, Interactive drilling, Mobile responsive, Advanced analytics');
console.log('⌨️ Shortcuts: Ctrl+R (Refresh all), Ctrl+1-3 (Refresh specific charts)');
console.log('🔧 Utils: ChartUtils.exportChart(), ChartUtils.getAnalytics()');

// Performance tracking
const performanceObserver = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
        if (entry.name.includes('chart')) {
            console.log(`📈 Chart performance: ${entry.name} took ${entry.duration.toFixed(2)}ms`);
        }
    }
});

if (typeof PerformanceObserver !== 'undefined') {
    performanceObserver.observe({ entryTypes: ['measure'] });
}