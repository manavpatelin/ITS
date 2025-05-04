function loadLiveTraffic() {
    document.querySelectorAll('.menu button').forEach(btn => btn.classList.remove('active'));
    document.querySelector('.menu button:first-child').classList.add('active');
    
    fetch('/live_content')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content-area').innerHTML = data;
            const scripts = document.getElementById('content-area').getElementsByTagName('script');
            Array.from(scripts).forEach(script => {
                const newScript = document.createElement('script');
                Array.from(script.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.innerHTML = script.innerHTML;
                script.parentNode.replaceChild(newScript, script);
            });
        })
        .catch(error => console.error('Error loading live traffic view:', error));
}

function loadAnalytics() {
    document.querySelectorAll('.menu button').forEach(btn => btn.classList.remove('active'));
    document.querySelector('.menu button:last-child').classList.add('active');

    fetch('/analytics')
        .then(response => response.text())
        .then(data => {
            document.getElementById('content-area').innerHTML = data;
            const scripts = document.getElementById('content-area').getElementsByTagName('script');
            Array.from(scripts).forEach(script => {
                const newScript = document.createElement('script');
                Array.from(script.attributes).forEach(attr => {
                    newScript.setAttribute(attr.name, attr.value);
                });
                newScript.innerHTML = script.innerHTML;
                script.parentNode.replaceChild(newScript, script);
            });
        })
        .catch(error => console.error('Error loading analytics view:', error));
}

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleTimeString();
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    setInterval(updateTime, 1000);
    updateTime();
    
    // Load live traffic view by default
    loadLiveTraffic();
});