document.addEventListener('DOMContentLoaded', () => {
    fetch('results.json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').classList.add('hidden');
            document.getElementById('dashboard').classList.remove('hidden');
            processBenchmarkData(data);
        })
        .catch(error => {
            document.getElementById('loading').textContent = 'Error loading benchmark data. Please ensure results.json exists.';
            console.error('Error:', error);
        });
});

function processBenchmarkData(data) {
    // 1. Aggregate Data by Model
    const modelStats = {};
    const models = [...new Set(data.map(item => item.model))];

    models.forEach(model => {
        const modelData = data.filter(item => item.model === model);
        const avgLatency = modelData.reduce((sum, item) => sum + item.latency, 0) / modelData.length;
        const avgRelevance = modelData.reduce((sum, item) => sum + item.relevance_score, 0) / modelData.length;
        const avgAccuracy = modelData.reduce((sum, item) => sum + item.accuracy_score, 0) / modelData.length;

        modelStats[model] = {
            latency: avgLatency,
            relevance: avgRelevance,
            accuracy: avgAccuracy,
            count: modelData.length
        };
    });

    // 2. Identify Winners (KPIs)
    let fastestModel = { name: '-', value: Infinity };
    let bestRelevance = { name: '-', value: -1 };
    let bestAccuracy = { name: '-', value: -1 };

    for (const [name, stats] of Object.entries(modelStats)) {
        if (stats.latency < fastestModel.value) fastestModel = { name, value: stats.latency };
        if (stats.relevance > bestRelevance.value) bestRelevance = { name, value: stats.relevance };
        if (stats.accuracy > bestAccuracy.value) bestAccuracy = { name, value: stats.accuracy };
    }

    // Update DOM KPIs
    document.getElementById('fastest-model-val').textContent = fastestModel.value.toFixed(2) + 's';
    document.getElementById('fastest-model-name').textContent = fastestModel.name;

    document.getElementById('best-relevance-val').textContent = bestRelevance.value.toFixed(2);
    document.getElementById('best-relevance-name').textContent = bestRelevance.name;

    document.getElementById('best-accuracy-val').textContent = bestAccuracy.value.toFixed(2);
    document.getElementById('best-accuracy-name').textContent = bestAccuracy.name;

    // 3. Render Charts
    renderCharts(models, modelStats);

    // 4. Populate Table
    populateTable(data, models);
}

function renderCharts(models, stats) {
    const ctxLatency = document.getElementById('latencyChart').getContext('2d');
    const ctxQuality = document.getElementById('qualityChart').getContext('2d');

    // Prepare Datasets
    const latencies = models.map(m => stats[m].latency);
    const relevance = models.map(m => stats[m].relevance);
    const accuracy = models.map(m => stats[m].accuracy);

    // Latency Chart
    new Chart(ctxLatency, {
        type: 'bar',
        data: {
            labels: models,
            datasets: [{
                label: 'Average Latency (seconds)',
                data: latencies,
                backgroundColor: 'rgba(56, 139, 253, 0.7)',
                borderColor: '#58a6ff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true, grid: { color: '#30363d' } },
                x: { grid: { display: false } }
            }
        }
    });

    // Quality Chart
    new Chart(ctxQuality, {
        type: 'bar',
        data: {
            labels: models,
            datasets: [
                {
                    label: 'Relevance Score',
                    data: relevance,
                    backgroundColor: 'rgba(35, 134, 54, 0.7)',
                    borderColor: '#238636',
                    borderWidth: 1
                },
                {
                    label: 'Accuracy Score',
                    data: accuracy,
                    backgroundColor: 'rgba(210, 153, 34, 0.7)',
                    borderColor: '#d29922',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 10, grid: { color: '#30363d' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function populateTable(data, models) {
    const tableBody = document.querySelector('#resultsTable tbody');
    const filter = document.getElementById('modelFilter');

    // Populate Filter
    models.forEach(model => {
        const option = document.createElement('option');
        option.value = model;
        option.textContent = model;
        filter.appendChild(option);
    });

    const renderRows = (filterValue) => {
        tableBody.innerHTML = '';
        const filteredData = filterValue === 'all' ? data : data.filter(d => d.model === filterValue);

        filteredData.forEach(row => {
            const tr = document.createElement('tr');

            // Score badges
            const getBadgeClass = (score) => score >= 8 ? 'score-high' : score >= 5 ? 'score-med' : 'score-low';

            tr.innerHTML = `
                <td><strong>${row.model}</strong></td>
                <td>${row.question}</td>
                <td style="font-size: 0.9em; color: #8b949e;">${row.prediction}</td>
                <td>
                    <span class="score-badge ${getBadgeClass(row.relevance_score)}">Rel: ${row.relevance_score}</span>
                    <span class="score-badge ${getBadgeClass(row.accuracy_score)}">Acc: ${row.accuracy_score}</span>
                </td>
                <td>${row.latency.toFixed(2)}s</td>
            `;
            tableBody.appendChild(tr);
        });
    };

    renderRows('all');

    filter.addEventListener('change', (e) => {
        renderRows(e.target.value);
    });
}
