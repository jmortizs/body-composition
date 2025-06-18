// DOM Elements
const dateFilterForm = document.getElementById('dateFilterForm');
const axisControlsForm = document.getElementById('axisControls');
const loading = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const chartDiv = document.getElementById('scatter-chart');

// Time-Series Chart DOM Elements
const timeSeriesControlsForm = document.getElementById('timeSeriesControls');
const loadingTimeSeries = document.getElementById('loading-time-series');
const errorTimeSeriesDiv = document.getElementById('error-time-series');
const timeSeriesChartDiv = document.getElementById('time-progression-chart');

// Global date filter state (shared across all charts)
const globalDateFilter = {
    startDate: '2025-01-01',
    endDate: '2025-06-30'
};

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

// Centralized list of measurement fields and their display names
const measurementFields = [
    { value: 'basalMetabolicRate', label: 'Basal Metabolic Rate' },
    { value: 'bodyFatMass', label: 'Body Fat Mass' },
    { value: 'muscleMass', label: 'Muscle Mass' },
    { value: 'totalBodyWater', label: 'Total Body Water' },
    { value: 'weight', label: 'Weight' }
];

/**
 * Populates a <select> element with measurement field options.
 * @param {HTMLSelectElement} selectElement - The select element to populate.
 * @param {string} defaultValue - The value to select by default.
 */
function populateMeasurementSelect(selectElement, defaultValue) {
    selectElement.innerHTML = '';
    measurementFields.forEach(field => {
        const option = document.createElement('option');
        option.value = field.value;
        option.textContent = field.label;
        if (field.value === defaultValue) {
            option.selected = true;
        }
        selectElement.appendChild(option);
    });
}

// Global date filter event handler (auto-refresh on change)
document.getElementById('startDate').addEventListener('change', () => {
    globalDateFilter.startDate = document.getElementById('startDate').value;
    refreshMeasurementsChart();
    refreshTimeSeriesChart();
    refreshVariationCards();
});
document.getElementById('endDate').addEventListener('change', () => {
    globalDateFilter.endDate = document.getElementById('endDate').value;
    refreshMeasurementsChart();
    refreshTimeSeriesChart();
    refreshVariationCards();
});

// Measurements chart axis controls event handler (auto-refresh on change)
document.getElementById('xField').addEventListener('change', () => {
    refreshMeasurementsChart();
});
document.getElementById('yField').addEventListener('change', () => {
    refreshMeasurementsChart();
});

// Time-Series chart controls event handler (auto-refresh on change)
if (document.getElementById('measureField')) {
    document.getElementById('measureField').addEventListener('change', () => {
        refreshTimeSeriesChart();
    });
}
if (document.getElementById('groupTime')) {
    document.getElementById('groupTime').addEventListener('change', () => {
        refreshTimeSeriesChart();
    });
}

// Function to refresh the measurements chart
async function refreshMeasurementsChart() {
    loading.style.display = 'block';
    errorDiv.style.display = 'none';
    chartDiv.innerHTML = '';

    try {
        const xField = document.getElementById('xField').value;
        const yField = document.getElementById('yField').value;

        // Use global date filter state
        const url = `http://localhost:8080/api/v1/measurements?start_date=${globalDateFilter.startDate}&end_date=${globalDateFilter.endDate}&x_field=${xField}&y_field=${yField}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(await response.text());
        }

        const data = await response.json();
        renderChart(data, xField, yField);
    } catch (err) {
        errorDiv.textContent = err.message || 'Failed to load data';
        errorDiv.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
}

// Function to refresh the time-series chart
async function refreshTimeSeriesChart() {
    loadingTimeSeries.style.display = 'block';
    errorTimeSeriesDiv.style.display = 'none';
    timeSeriesChartDiv.innerHTML = '';
    try {
        const measureField = document.getElementById('measureField').value;
        const groupTime = document.getElementById('groupTime').value;
        // Use global date filter state
        const url = `http://localhost:8080/api/v1/time-progression?start_date=${globalDateFilter.startDate}&end_date=${globalDateFilter.endDate}&measure_field=${measureField}&group_time=${groupTime}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        renderTimeSeriesChart(data);
    } catch (err) {
        errorTimeSeriesDiv.textContent = err.message || 'Failed to load time-series data';
        errorTimeSeriesDiv.style.display = 'block';
    } finally {
        loadingTimeSeries.style.display = 'none';
    }
}

// Fetch and render variation cards
async function refreshVariationCards() {
    const cardsContainer = document.getElementById('variation-cards');
    cardsContainer.innerHTML = '';
    try {
        const url = `http://localhost:8080/api/v1/variation-card?start_date=${globalDateFilter.startDate}&end_date=${globalDateFilter.endDate}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        renderVariationCards(data);
    } catch (err) {
        cardsContainer.innerHTML = `<div style="color: var(--error); padding: 1rem;">${err.message || 'Failed to load variation cards.'}</div>`;
    }
}

function renderVariationCards(cards) {
    const container = document.getElementById('variation-cards');
    if (!cards.length) {
        container.innerHTML = '<div style="color: var(--text-secondary);">No variation data for this period.</div>';
        return;
    }
    container.innerHTML = '';
    cards.forEach(card => {
        // Arrow and color based on positive/negative
        const isPositive = card.positive;
        const arrow = card.variation > 0 ? '▲' : '▼';
        const cardClass = isPositive ? 'positive' : 'negative';
        // Format value and percent
        const valueStr = (card.value >= 0 ? '+' : '') + card.value.toFixed(2);
        const percentStr = Math.abs(card.variation).toFixed(0) + '%';
        // Card HTML
        const cardDiv = document.createElement('div');
        cardDiv.className = `variation-card ${cardClass}`;
        cardDiv.innerHTML = `
            <div class="measure">${card.measure}</div>
            <div class="value">${valueStr}</div>
            <div class="variation ${cardClass}">
                <span class="arrow">${arrow}</span>
                <span>${percentStr}</span>
            </div>
        `;
        container.appendChild(cardDiv);
    });
}

// Utility to format date as YYYY-MM-DD
function formatDate(date) {
    return date.toISOString().slice(0, 10);
}

// Set default date values dynamically
function setDefaultDateRange() {
    const end = new Date();
    const start = new Date(end.getFullYear(), end.getMonth() - 1, 1); // first day of previous month
    const startDateStr = formatDate(start);
    const endDateStr = formatDate(end);
    document.getElementById('startDate').value = startDateStr;
    document.getElementById('endDate').value = endDateStr;
    globalDateFilter.startDate = startDateStr;
    globalDateFilter.endDate = endDateStr;
}

// Initialize the page by loading the chart with default settings
document.addEventListener('DOMContentLoaded', () => {
    // Populate selectors with measurement fields
    populateMeasurementSelect(document.getElementById('xField'), 'weight');
    populateMeasurementSelect(document.getElementById('yField'), 'muscleMass');
    populateMeasurementSelect(document.getElementById('measureField'), 'weight');
    // Set initial date values dynamically
    setDefaultDateRange();
    // Load initial chart
    refreshMeasurementsChart();
    refreshTimeSeriesChart();
    refreshVariationCards();
});

function renderChart(data, xField, yField) {
    console.log(data);
    if (!data.dataPoints.length) {
        chartDiv.innerHTML = 'No data for selected range/fields.';
        return;
    }
    // Prepare correlation legend text if available
    let correlationText = '';
    if (typeof data.correlation === 'number' && !isNaN(data.correlation)) {
        correlationText = `Correlation: ${data.correlation.toFixed(3)}`;
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
            text: data.title + (correlationText ? `<br><span style=\"font-size:16px;color:#11A8A8\">${correlationText}</span>` : ''),
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

    Plotly.newPlot('scatter-chart', [trace], layout, config).then(() => {
        // Ensure the chart resizes properly with the window
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('scatter-chart');
        });
    });
}

// Function to render the time-series chart using Plotly
function renderTimeSeriesChart(data) {
    if (!data.dataPoints.length) {
        timeSeriesChartDiv.innerHTML = 'No data for selected range/field.';
        return;
    }
    const trace = {
        x: data.dataPoints.map(d => new Date(d.date)),
        y: data.dataPoints.map(d => d.value),
        mode: 'lines+markers',
        type: 'scatter',
        marker: {
            size: 10,
            color: '#11A8A8', //chartTheme.accent,
            line: {
                color: chartTheme.background,
                width: 1
            }
        },
        line: {
            color: '#11A8A8', //chartTheme.accent,
            width: 3
        },
        error_y: {
            type: 'data',
            array: data.dataPoints.map(d => d.std),
            visible: true,
            color: '#11A8A8',
            thickness: 2,
            width: 0,
            opacity: 0.8
        },
        hovertemplate: '%{x|%Y-%m-%d}: %{y}<extra></extra>',
        customdata: data.dataPoints.map(d => d.std),
        hoverlabel: {
            bgcolor: chartTheme.background,
            font: {
                color: chartTheme.text,
                size: 12
            }
        }
    };
    const layout = {
        autosize: true,
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
            },
            type: 'date'
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
    Plotly.newPlot('time-progression-chart', [trace], layout, config).then(() => {
        window.addEventListener('resize', () => {
            Plotly.Plots.resize('time-progression-chart');
        });
    });
}