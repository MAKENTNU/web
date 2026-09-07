Chart.defaults.font.family = "Ubuntu";
Chart.defaults.font.weight = 500;
Chart.defaults.font.size = 12.5;

const STOPS = {
    yellow: [[245, 161, 63], [248, 200, 17], [253, 224, 107]],
    blue: [[34, 43, 52], [12, 66, 106], [165, 187, 201]],
};

function lerp(a, b, t) {
    return Math.round(a + (b - a) * t);
}

/** One colour per bar. */
function gradientPalette(stops, n) {
    if (n <= 0) return [];
    if (n === 1) return [`rgb(${stops[Math.floor(stops.length / 2)].join(",")})`];
    const out = [];
    for (let i = 0; i < n; i++) {
        const t = i / (n - 1);
        const segPos = t * (stops.length - 1);
        const idx = Math.min(Math.floor(segPos), stops.length - 2);
        const f = segPos - idx;
        const [r1, g1, b1] = stops[idx];
        const [r2, g2, b2] = stops[idx + 1];
        out.push(`rgb(${lerp(r1, r2, f)},${lerp(g1, g2, f)},${lerp(b1, b2, f)})`);
    }
    return out;
}

// The two kinds of bar chart.
const BAR_KINDS = {
    hours: {
        field: "hours",
        yLabel: gettext("Hours reserved"),
        stops: STOPS.yellow,
        integerY: false,
    },
    counts: {
        field: "count",
        yLabel: gettext("Number of reservations"),
        stops: STOPS.blue,
        integerY: true,
    },
};

const COMMON_OPTIONS = {
    events: [],
    responsive: true,
    maintainAspectRatio: false,
};

/** Reads the JSON `json_script` wrote into the page. */
function readJson(elementId) {
    const node = document.getElementById(elementId);
    return node ? JSON.parse(node.textContent) : null;
}

/** Draws a chart, destroying:) any chart already on the canvas. */
function draw(canvas, config) {
    if (canvas.chart) canvas.chart.destroy();
    canvas.chart = new Chart(canvas.getContext("2d"), config);
}

/** Drawing the barcharts, calls the function above
 * `rows` is a section's `per_machine` list. */
function drawBarChart(canvas, rows) {
    const kind = BAR_KINDS[canvas.dataset.kind];
    if (!kind || !rows) return;
    draw(canvas, {
        type: "bar",
        data: {
            labels: rows.map(row => row.name),
            datasets: [{
                data: rows.map(row => row[kind.field] || 0),
                backgroundColor: gradientPalette(kind.stops, rows.length),
                borderWidth: 0,
                fill: true,
            }],
        },
        options: {
            ...COMMON_OPTIONS,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: kind.yLabel },
                    ...(kind.integerY ? { ticks: { stepSize: 1, precision: 0 } } : {}),
                },
            },
            plugins: { legend: { display: false } },
        },
    });
}

/** The average reservations by hour chart. */
function drawTimeChart(canvas, values) {
    if (!values) return;
    const colour = "248, 200, 17";
    draw(canvas, {
        type: "line",
        data: {
            labels: Object.keys(values),
            datasets: [{
                data: Object.values(values),
                backgroundColor: `rgba(${colour}, 0.3)`,
                borderColor: `rgb(${colour})`,
                pointBackgroundColor: `rgb(${colour})`,
                borderWidth: 2,
                pointBorderWidth: 0,
                fill: true,
                tension: 0.3,
            }],
        },
        options: {
            ...COMMON_OPTIONS,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: gettext("Average reservations per day"),
                    },
                },
                x: {
                    title: { display: true, text: gettext("Hour of day") },
                    ticks: { maxRotation: 0, minRotation: 0 },
                },
            },
            plugins: { legend: { display: false } },
        },
    });
}

document.querySelectorAll("canvas[data-kind]").forEach(canvas => {
    drawBarChart(canvas, readJson(canvas.dataset.source));
});
const timeCanvas = document.getElementById("timespan");
if (timeCanvas) drawTimeChart(timeCanvas, readJson("time"));
