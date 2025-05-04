function updateStats() {
    const counts = document.querySelectorAll('[id^="count-"]');
    let total = 0;
    counts.forEach(count => {
        total += parseInt(count.textContent) || 0;
    });
    document.getElementById('total-vehicles').textContent = total;
}

function updateTrafficLights() {
    fetch('/traffic_states')
        .then(response => response.json())
        .then(states => {
            for (let lane in states) {
                const laneElement = document.querySelector(`.lane-card:nth-child(${lane})`);
                const redLight = laneElement.querySelector('.light.red');
                const yellowLight = laneElement.querySelector('.light.yellow');
                const greenLight = laneElement.querySelector('.light.green');
                const timer = laneElement.querySelector('.digital-timer');
                const timerDisplay = timer.querySelector('span');

                redLight.classList.toggle('active', states[lane].color === 'red');
                yellowLight.classList.toggle('active', states[lane].color === 'yellow');
                greenLight.classList.toggle('active', states[lane].color === 'green');
                
                // Update timer color and value
                timer.classList.toggle('green', states[lane].color === 'green');
                timerDisplay.textContent = states[lane].timer.toString().padStart(2, '0');

                // Update average wait time
                const avgWait = Math.max(...Object.values(states).map(s => s.remaining_red || 0));
                document.getElementById('avg-wait').textContent = `${avgWait}s`;
            }
        })
        .catch(error => console.error('Error:', error));
}

function updateVehicleCounts() {
    fetch('/vehicle_counts')
        .then(response => response.json())
        .then(counts => {
            Object.keys(counts).forEach(laneId => {
                document.getElementById(`count-${laneId}`).textContent = counts[laneId];
            });
            updateStats();
        })
        .catch(error => console.error('Error:', error));
}

function checkAmbulance() {
    fetch('/ambulance_status')
        .then(response => response.json())
        .then(status => {
            let emergencyCount = 0;
            Object.keys(status).forEach(laneId => {
                const indicator = document.getElementById(`ambulance-${laneId}`);
                if (status[laneId]) {
                    indicator.innerHTML = '<i class="fas fa-ambulance"></i> EMERGENCY';
                    indicator.style.display = 'flex';
                    emergencyCount++;
                } else {
                    indicator.style.display = 'none';
                }
            });
            document.getElementById('emergency-count').textContent = emergencyCount;
        })
        .catch(error => console.error('Error:', error));
}

// Initialize updates with error handling
function initializeUpdates() {
    updateTrafficLights();
    updateVehicleCounts();
    checkAmbulance();
}

setInterval(initializeUpdates, 1000);
initializeUpdates();