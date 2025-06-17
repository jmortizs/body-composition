const form = document.getElementById('controls');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const chartDiv = document.getElementById('chart');

// Chart theme colors
const chartTheme = {
    background: '#2d2d2d',
    text: '#ffffff',
    grid: '#404040',
    accent: '#031059',
    marker: {
        colorscale: [
            [0, '#031059'],
            [0.5, '#11A8A8'],
            [1, '#D1F1CC']
        ]
    }
};

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
            size: 12,
            color: data.dataPoints.map(d => d.elapseDays),
            colorscale: chartTheme.marker.colorscale,
            colorbar: {
                title: {
                    text: 'Days Elapsed',
                    font: {
                        color: chartTheme.text,
                        size: 12
                    }
                },
                thickness: 20,
                tickfont: {
                    color: chartTheme.text,
                    size: 10
                }
            },
            showscale: true,
            line: {
                color: chartTheme.background,
                width: 1
            }
        },
        hoverlabel: {
            bgcolor: chartTheme.background,
            font: {
                color: chartTheme.text,
                size: 12
            }
        }
    };

    const layout = {
        // Enable autosize to fit container
        autosize: true,
        // Set responsive width and height
        width: null,
        height: null,
        paper_bgcolor: chartTheme.background,
        plot_bgcolor: chartTheme.background,
        font: {
            color: chartTheme.text,
            family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        },
        title: {
            text: data.title,
            font: {
                size: 24,
                color: chartTheme.text
            },
            x: 0.5,
            xanchor: 'center'
        },
        xaxis: {
            title: {
                text: data.xAxisTitle,
                font: {
                    size: 16,
                    color: chartTheme.text
                }
            },
            gridcolor: chartTheme.grid,
            zerolinecolor: chartTheme.grid,
            tickfont: {
                color: chartTheme.text
            }
        },
        yaxis: {
            title: {
                text: data.yAxisTitle,
                font: {
                    size: 16,
                    color: chartTheme.text
                }
            },
            gridcolor: chartTheme.grid,
            zerolinecolor: chartTheme.grid,
            tickfont: {
                color: chartTheme.text
            }
        },
        margin: {
            l: 60,
            r: 60,
            b: 80,
            t: 100,
            pad: 4
        },
        showlegend: false,
        hovermode: 'closest'
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'toImage', 'sendDataToCloud']
    };

    Plotly.newPlot('chart', [trace], layout, config).then(() => {
        // Ensure the chart resizes properly with the window
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('chart');
        });
    });
}