// `STATISTICS_DATA_URL` is declared in `statistics.html`.

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

const CONFIG = {
    hours: {
        yLabel: gettext("Hours reserved"),
        valueKey: "len",
        stops: STOPS.yellow,
        integerY: false,
    },
    counts: {
        yLabel: gettext("Number of reservations"),
        valueKey: "number_of_reservations",
        stops: STOPS.blue,
        integerY: true,
    },
};

// chartRegistry[sourceId] = {chart, kind}
const chartRegistry = {};

function buildBarConfig(data, kind) {
    const cfg = CONFIG[kind];
    const yScale = {
        beginAtZero: true,
        title: { display: true, text: cfg.yLabel },
    };
    if (cfg.integerY) {
        yScale.ticks = { stepSize: 1, precision: 0 };
    }
    return {
        type: "bar",
        data: {
            labels: data.map(e => e.name),
            datasets: [{
                data: data.map(e => e[cfg.valueKey] || 0),
                backgroundColor: gradientPalette(cfg.stops, data.length),
                borderWidth: 0,
                fill: true,
            }],
        },
        options: {
            events: [],
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: yScale },
            plugins: { legend: { display: false } },
        },
    };
}

function renderMachineChart(canvas) {
    const sourceId = canvas.dataset.source;
    const kind = canvas.dataset.kind;
    const node = document.getElementById(sourceId);
    if (!node) return;
    const data = JSON.parse(node.textContent);
    const chart = new Chart(canvas.getContext("2d"), buildBarConfig(data, kind));
    chartRegistry[sourceId] = { chart, kind };
}

function updateBarChart(sourceId, data) {
    const entry = chartRegistry[sourceId];
    if (!entry) return;
    const cfg = CONFIG[entry.kind];
    entry.chart.data.labels = data.map(e => e.name);
    entry.chart.data.datasets[0].data = data.map(e => e[cfg.valueKey] || 0);
    entry.chart.data.datasets[0].backgroundColor = gradientPalette(cfg.stops, data.length);
    entry.chart.update();
}

let timeChart;

function renderTimespan() {
    const canvas = document.getElementById("timespan");
    if (!canvas) return;
    const data = JSON.parse(document.getElementById("time").textContent);
    timeChart = new Chart(canvas.getContext("2d"), {
        type: "line",
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: gettext("Average reservations"),
                data: Object.values(data),
                backgroundColor: "rgba(248, 200, 17, 0.3)",
                borderColor: "rgb(248, 200, 17)",
                borderWidth: 2,
                fill: true,
                tension: 0.3,
                pointBackgroundColor: "rgb(239, 184, 14)",
                pointBorderWidth: 0,
            }],
        },
        options: {
            events: [],
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: gettext("Average reservations per day") },
                },
                x: {
                    title: { display: true, text: gettext("Hour of day") },
                    ticks: { maxRotation: 0, minRotation: 0 },
                },
            },
        },
    });
}

function updateTimeChart(data) {
    if (!timeChart) return;
    timeChart.data.labels = Object.keys(data);
    timeChart.data.datasets[0].data = Object.values(data);
    timeChart.update();
}

function dateToIso(d) {
    if (!d) return "";
    const yyyy = d.getFullYear();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
}

function initStatsCalendar(el) {
    const $cal = $(el);
    if ($cal.data("module-calendar")) return;
    const settings = {
        type: "date",
        firstDayOfWeek: 1,
        monthFirst: false,
        formatter: {
            date: function (date) {
                if (!date) return "";
                const dd = String(date.getDate()).padStart(2, "0");
                const mm = String(date.getMonth() + 1).padStart(2, "0");
                return `${dd}.${mm}.${date.getFullYear()}`;
            },
        },
    };
    if (typeof MONTH_TRANSLATIONS !== "undefined") {
        settings.text = {
            months: MONTH_TRANSLATIONS,
            monthsShort: SHORT_MONTH_TRANSLATIONS,
        };
    }
    $cal.calendar(settings);
    const initialIso = el.dataset.iso || "";
    if (initialIso) {
        const [y, m, d] = initialIso.split("-").map(Number);
        $cal.calendar("set date", new Date(y, m - 1, d));
    }
}

const statsFilter = {
    onChange(select) {
        const wrap = select.closest(".stats-filter-inline");
        const custom = wrap.querySelector(".stats-custom-range");
        const key = wrap.dataset.key;
        if (select.value === "custom") {
            custom.hidden = false;
            custom.style.display = "";
            wrap.querySelectorAll(".stats-datepicker").forEach(initStatsCalendar);
            return;
        }
        custom.hidden = true;
        custom.style.display = "none";
        wrap.querySelectorAll(".stats-datepicker").forEach(el => {
            if ($(el).data("module-calendar")) $(el).calendar("clear");
        });
        this.apply(key, select.value, "", "", wrap);
    },
    applyCustom(btn) {
        const wrap = btn.closest(".stats-filter-inline");
        const key = wrap.dataset.key;
        const $wrap = $(wrap);
        const fromDate = $wrap.find(".stats-datepicker[data-role='from']").calendar("get date");
        const toDate = $wrap.find(".stats-datepicker[data-role='to']").calendar("get date");
        this.apply(key, "custom", dateToIso(fromDate), dateToIso(toDate), wrap);
    },
    pushUrl(key, range, from, to) {
        const u = new URL(window.location);
        u.searchParams.delete(`from_${key}`);
        u.searchParams.delete(`to_${key}`);
        if (range === "all") {
            u.searchParams.delete(`range_${key}`);
        } else {
            u.searchParams.set(`range_${key}`, range);
            if (range === "custom") {
                if (from) u.searchParams.set(`from_${key}`, from);
                if (to) u.searchParams.set(`to_${key}`, to);
            }
        }
        history.replaceState(null, "", u.toString());
        return u;
    },
    apply(key, range, from, to, wrap) {
        const u = this.pushUrl(key, range, from, to);
        const fetchUrl = new URL(STATISTICS_DATA_URL, window.location.origin);
        fetchUrl.searchParams.set("key", key);
        u.searchParams.forEach((v, k) => fetchUrl.searchParams.set(k, v));
        wrap.classList.add("loading");
        fetch(fetchUrl.toString(), { headers: { "Accept": "application/json" } })
            .then(r => r.json())
            .then(data => {
                if (key === "time") {
                    updateTimeChart(data.time);
                } else {
                    const section = wrap.closest(".stats-section");
                    const numbers = section.querySelectorAll(".stats-big-number");
                    if (numbers[0]) numbers[0].textContent = data.reservation_count;
                    if (numbers[1]) numbers[1].textContent = data.total_hours_sum;
                    updateBarChart(`${key}-hours`, data.total_hours);
                    updateBarChart(`${key}-counts`, data.counts);
                }
            })
            .finally(() => wrap.classList.remove("loading"));
    },
};
window.statsFilter = statsFilter;

document.querySelectorAll("canvas.machine-chart").forEach(renderMachineChart);
renderTimespan();
// Init all datepickers eagerly (works even when their container starts hidden).
document.querySelectorAll(".stats-datepicker").forEach(initStatsCalendar);
