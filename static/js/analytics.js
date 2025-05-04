// Chart colors
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
const CONGESTION_COLORS = {
    low: '#00C49F',     // Green
    medium: '#FFBB28',  // Yellow
    high: '#FF8042',    // Orange
    severe: '#FF0000'   // Red
};

// Initialize charts
let vehicleCountChart, laneDistributionChart, vehicleTypeChart;
let ambulanceTimelineChart, performanceChart, confusionMatrixChart;

// Store latest data
let latestData = [];
const DATA_REFRESH_INTERVAL = 3000; // Refresh every 3 seconds for live updates

// Initialize all charts when the page loads
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    fetchData(); // Initial data fetch
    
    // Set up periodic data refresh for live updates
    setInterval(fetchData, DATA_REFRESH_INTERVAL);
    
    // Update current time
    updateTime();
    setInterval(updateTime, 1000);
});

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toLocaleTimeString();
}

// Function to navigate to live traffic view
function loadLiveTraffic() {
    window.location.href = '/live_content';
}

// Fetch data from API
async function fetchData() {
    try {
        const response = await fetch('/api/traffic-data');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        
        // Update all charts with new data
        if (data.trafficData && data.trafficData.length > 0) {
            updateVehicleCountChart(data.trafficData);
            updateLaneDistributionChart(data.trafficData);
            updateVehicleTypeChart(data.vehicleTypes);
            updateAmbulanceDetection(data.trafficData);
            updatePerformanceCharts(data.trafficData, data.confusionMatrix);
            
            // Update current count and processing time
            const latestData = data.trafficData[0];
            document.getElementById('currentCount').textContent = latestData.Count;
            document.getElementById('processingTime').textContent = latestData.ProcessingTime;
            
            // Update congestion status
            updateCongestionStatus(data.trafficData);
            
            // Store latest data
            latestData = data.trafficData;
            
            // Add a visual indicator that data has been updated
            flashUpdateIndicator();
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Add a visual indicator for data updates
function flashUpdateIndicator() {
    const indicator = document.getElementById('update-indicator');
    if (indicator) {
        indicator.classList.add('flash-update');
        setTimeout(() => {
            indicator.classList.remove('flash-update');
        }, 500);
    }
}

// Chart configurations
const chartConfigs = {
    vehicleCount: {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Vehicle Count',
                data: [],
                fill: true,
                backgroundColor: 'rgba(136, 132, 216, 0.2)',
                borderColor: 'rgba(136, 132, 216, 1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    suggestedMin: 100
                }
            }
        }
    },
    laneDistribution: {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                { label: 'Lane 1', data: [], backgroundColor: '#0088FE', stack: 'Stack 0' },
                { label: 'Lane 2', data: [], backgroundColor: '#00C49F', stack: 'Stack 0' },
                { label: 'Lane 3', data: [], backgroundColor: '#FFBB28', stack: 'Stack 0' },
                { label: 'Lane 4', data: [], backgroundColor: '#FF8042', stack: 'Stack 0' }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { stacked: true },
                y: { 
                    stacked: true,
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        stepSize: 25
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10
                    }
                }
            }
        }
    },
    vehicleType: {
        type: 'doughnut',
        data: {
            labels: ['Cars', 'Trucks', 'Motorcycles', 'Buses', 'Emergency'],
            datasets: [{
                data: [50, 50, 50, 50, 50],
                backgroundColor: COLORS,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    },
    ambulanceTimeline: {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Ambulance Detection',
                data: [],
                stepped: true,
                backgroundColor: 'rgba(255, 0, 0, 0.2)',
                borderColor: 'rgba(255, 0, 0, 1)',
                pointRadius: 4,
                pointBackgroundColor: 'rgba(255, 0, 0, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: -0.1,
                    max: 1.1,
                    ticks: {
                        callback: function(value) {
                            if (value === 0) return 'No';
                            if (value === 1) return 'Yes';
                            return '';
                        }
                    }
                }
            }
        }
    },
    performance: {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Precision', data: [], borderColor: '#8884d8', tension: 0.4 },
                { label: 'Recall', data: [], borderColor: '#82ca9d', tension: 0.4 },
                { label: 'F1 Score', data: [], borderColor: '#ffc658', tension: 0.4 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    min: 80,
                    max: 100
                }
            }
        }
    },
    confusionMatrix: {
        type: 'bar',
        data: {
            labels: ['TP', 'FP', 'TN', 'FN'],
            datasets: [{
                data: [85, 5, 87, 3],
                backgroundColor: COLORS
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    }
};

// Get congestion level based on count
function getCongestionLevel(count) {
    if (count < 30) return 'low';
    if (count < 50) return 'medium';
    if (count < 70) return 'high';
    return 'severe';
}

// Initialize all charts
function initCharts() {
    vehicleCountChart = new Chart(
        document.getElementById('vehicleCountChart'),
        chartConfigs.vehicleCount
    );
    
    laneDistributionChart = new Chart(
        document.getElementById('laneDistributionChart'),
        chartConfigs.laneDistribution
    );
    
    vehicleTypeChart = new Chart(
        document.getElementById('vehicleTypeChart'),
        chartConfigs.vehicleType
    );
    
    ambulanceTimelineChart = new Chart(
        document.getElementById('ambulanceTimelineChart'),
        chartConfigs.ambulanceTimeline
    );
    
    performanceChart = new Chart(
        document.getElementById('performanceChart'),
        chartConfigs.performance
    );
    
    confusionMatrixChart = new Chart(
        document.getElementById('confusionMatrixChart'),
        chartConfigs.confusionMatrix
    );
}

// Update vehicle count chart
function updateVehicleCountChart(data) {
    const labels = data.map(item => item.Time);
    const counts = data.map(item => item.Count);
    
    vehicleCountChart.data.labels = labels;
    vehicleCountChart.data.datasets[0].data = counts;
    vehicleCountChart.update();
}

// Update lane distribution chart
function updateLaneDistributionChart(data) {
    // Get the most recent data points (up to 12)
    const recentData = data.slice(0, 12).reverse();
    
    // Extract time labels
    const timeLabels = recentData.map(item => item.Time);
    
    // Extract lane data for each time point
    const lane1Data = recentData.map(item => item.Lane1);
    const lane2Data = recentData.map(item => item.Lane2);
    const lane3Data = recentData.map(item => item.Lane3);
    const lane4Data = recentData.map(item => item.Lane4);
    
    // Update chart data
    laneDistributionChart.data.labels = timeLabels;
    laneDistributionChart.data.datasets[0].data = lane1Data;
    laneDistributionChart.data.datasets[1].data = lane2Data;
    laneDistributionChart.data.datasets[2].data = lane3Data;
    laneDistributionChart.data.datasets[3].data = lane4Data;
    
    laneDistributionChart.update();
    
    // Update congestion status with colored bars like in the image
    const latestData = data[0];
    const congestionDiv = document.getElementById('congestionStatus');
    congestionDiv.innerHTML = '';
    
    const lanes = [
        { name: 'Lane 1', value: latestData.Lane1 },
        { name: 'Lane 2', value: latestData.Lane2 },
        { name: 'Lane 3', value: latestData.Lane3 },
        { name: 'Lane 4', value: latestData.Lane4 }
    ];
    
    lanes.forEach(lane => {
        const level = getCongestionLevel(lane.value);
        const color = CONGESTION_COLORS[level];
        
        const colDiv = document.createElement('div');
        colDiv.className = 'col-3';
        
        // Create a colored bar with text inside
        let bgColor = color;
        let textColor = 'white';
        
        colDiv.innerHTML = `
            <div style="background-color: ${bgColor}; color: ${textColor}; text-align: center; padding: 8px; border-radius: 4px; font-weight: bold;">
                ${lane.name}: ${lane.value}
            </div>
        `;
        congestionDiv.appendChild(colDiv);
    });
}

// Update vehicle type chart
function updateVehicleTypeChart(vehicleTypes) {
    const labels = Object.keys(vehicleTypes);
    const data = Object.values(vehicleTypes);
    
    vehicleTypeChart.data.labels = labels;
    vehicleTypeChart.data.datasets[0].data = data;
    vehicleTypeChart.update();
}

// Update performance chart
function updatePerformanceChart(data) {
    const latestData = data.filter(item => 
        item.Precision > 0 && item.Recall > 0 && item.F1Score > 0);
    
    if (latestData.length > 0) {
        const precision = latestData.map(item => item.Precision);
        const recall = latestData.map(item => item.Recall);
        const f1Score = latestData.map(item => item.F1Score);
        const labels = latestData.map(item => item.Time);
        
        performanceChart.data.labels = labels;
        performanceChart.data.datasets[0].data = precision;
        performanceChart.data.datasets[1].data = recall;
        performanceChart.data.datasets[2].data = f1Score;
        performanceChart.update();
    }
}

// Update confusion matrix chart
function updateConfusionMatrixChart(matrixData) {
    const labels = matrixData.map(item => item.name);
    const data = matrixData.map(item => item.value);
    
    confusionMatrixChart.data.labels = labels;
    confusionMatrixChart.data.datasets[0].data = data;
    confusionMatrixChart.update();
}

// Update congestion status
function updateCongestionStatus(data) {
    const latestData = data[data.length - 1];
    const congestionDiv = document.getElementById('congestionStatus');
    congestionDiv.innerHTML = '';
    
    const lanes = [
        { name: 'Lane 1', value: latestData.Lane1 },
        { name: 'Lane 2', value: latestData.Lane2 },
        { name: 'Lane 3', value: latestData.Lane3 },
        { name: 'Lane 4', value: latestData.Lane4 }
    ];
    
    lanes.forEach(lane => {
        const level = getCongestionLevel(lane.value);
        const color = CONGESTION_COLORS[level];
        
        const colDiv = document.createElement('div');
        colDiv.className = 'col-3';
        colDiv.innerHTML = `
            <div class="congestion-indicator">
                <span style="background-color: ${color}"></span>
                <div>
                    <strong>${lane.name}</strong>
                    <p>${level.charAt(0).toUpperCase() + level.slice(1)}</p>
                </div>
            </div>
        `;
        congestionDiv.appendChild(colDiv);
    });
}

// Update ambulance detection
function updateAmbulanceDetection(data) {
    let times = data.map(d => d.Time);
    let ambulanceData = data.map(d => d.Action === 'Ambulance' ? 1 : 0);
    
    // Update chart data
    ambulanceTimelineChart.data.labels = times;
    ambulanceTimelineChart.data.datasets[0].data = ambulanceData;
    ambulanceTimelineChart.update();
    
    // Check if there are any ambulances in the current data
    let hasAmbulance = data.some(d => d.Action === 'Ambulance');
    let ambulanceCount = data.filter(d => d.Action === 'Ambulance').length;
    
    // Update alert
    let alertHTML = `
        <div class="alert-badge ${hasAmbulance ? 'bg-danger' : 'bg-success'}">
            <i class="bi ${hasAmbulance ? 'bi-exclamation-triangle' : 'bi-check-circle'}"></i>
            ${hasAmbulance 
                ? `${ambulanceCount} ambulance${ambulanceCount > 1 ? 's' : ''} detected - Priority activated` 
                : 'No emergency vehicles detected'}
        </div>
    `;
    
    document.getElementById('ambulanceAlert').innerHTML = alertHTML;
}

// Update performance charts
function updatePerformanceCharts(data, confusionMatrix) {
    updatePerformanceChart(data);
    updateConfusionMatrixChart(confusionMatrix);
    
    // Update metrics
    if (data.length > 0) {
        const latestData = data[0];
        document.getElementById('avgPrecision').textContent = `${latestData.Precision.toFixed(1)}%`;
        document.getElementById('avgRecall').textContent = `${latestData.Recall.toFixed(1)}%`;
        document.getElementById('avgF1').textContent = `${latestData.F1Score.toFixed(1)}%`;
    }
}