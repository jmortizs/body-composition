const form = document.getElementById('controls');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const chartDiv = document.getElementById('chart');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    loading.style.display = 'block';
    errorDiv.style.display = 'none';
    chartDiv.innerHTML = '';
    try {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const xField = document.getElementById('xField').value;
        const yField = document.getElementById('yField').value;
        const url = `http://localhost:8080/api/measurements/scatter?start_date=${startDate}&end_date=${endDate}&x_field=${xField}&y_field=${yField}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        renderChart(data, xField, yField);
    } catch (err) {
        errorDiv.textContent = err.message || 'Failed to load data';
        errorDiv.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
});

function renderChart(data) {
    console.log(data);
    if (!data.dataPoints.length) {
        chartDiv.innerHTML = 'No data for selected range/fields.';
        return;
    }
    const trace = {
        x: data.dataPoints.map(d => d.x),
        y: data.dataPoints.map(d => d.y),
        text: data.dataPoints.map(d => new Date(d.date).toLocaleDateString()),
        mode: 'markers',
        type: 'scatter',
        marker: {
            size: 10,
            color: data.dataPoints.map(d => d.elapseDays),
            colorscale: 'Viridis',
            colorbar: {
                title: 'Days Elapsed',
                thickness: 20
            },
            showscale: true
        }
    };
    const layout = {
        title: {
            text: data.title,
            font: {
                size: 24
            }
        },
        xaxis: {
            title: {
                text: data.xAxisTitle,
                font: {
                    size: 16
                }
            }
        },
        yaxis: {
            title: {
                text: data.yAxisTitle,
                font: {
                    size: 16
                }
            }
        },
        margin: {
            l: 50,
            r: 50,
            b: 100,
            t: 100,
            pad: 4
        }
    };
    Plotly.newPlot('chart', [trace], layout);
}