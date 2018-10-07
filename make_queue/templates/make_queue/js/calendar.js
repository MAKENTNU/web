var canMakeReservation = {{ can_make_more_reservations }};
var canIgnoreRules = {{ can_ignore_rules }};
var rules = [
    {% for rule in rules %}
    {
        periods:  {{ rule.periods }},
        max_inside: {{ rule.max_hours }},
        max_crossed: {{ rule.max_hours_crossed }},
    },
    {% endfor %}
]

var zeroPadClock = (number) => ("00" + number).substr(-2, 2);
var timeToClock = (time) => time <= 0 ? "00:00" : zeroPadClock(Math.floor(time)) + ":" + zeroPadClock(Math.floor(time % 1 * 60));

var getStartTime = () => parseFloat($(".time_selection").css("top")) / $(".time_selection").closest(".day").height() * 24;
var getEndTime = () => (parseFloat($(".time_selection").css("top")) + $(".time_selection").height()) / $(".time_selection").closest(".day").height() * 24;
var getDay = () => parseInt($(".time_selection").closest(".day").data("week-index"));

var currentDate = () => {
    let dateText = $(clickedDay).data("date").split(".");
    let startTime = timeToClock(getStartTime()).split(":");
    return new Date(dateText[2], parseInt(dateText[1]) - 1, dateText[0], startTime[0], startTime[1])
};

var resetSelection = () => {
    clickedDay = null;
    selected = false;
    clickedPoint = 0;
    resizingDirection = null;
    $(".time_selection").remove();
};

var clickedDay, clickedPoint, selected, resizingDirection;
resetSelection();

var onLetGoFunc = (event) => {
    if ($(clickedDay).find($(event.target)) && (event.type === "mouseout" || event.type === "touchout")) return;
    resizingDirection = null;
    {# We do not care about the situations where another day is clicked #}
    if (clickedDay == null || clickedDay !== event.target && !$(clickedDay).find($(event.target))) return false;

    selected = true;
    let time_selection_element = $(".time_selection");
    let day = time_selection_element.closest(".day");

    {# If there exists a function name timeSelectionPopupHTML create a popup with this as content #}
    if (typeof timeSelectionPopupHTML !== "undefined") {
        time_selection_element.popup({
            html: timeSelectionPopupHTML(day.data("date"), timeToClock(getStartTime()), timeToClock(getEndTime()), {
                type: day.data("machine-type"),
                pk: day.data("machine-pk")
            }),
            position: "right center", on: "onload",
        }).popup("show");
    }

    $("body").mousedown((event) => {
        if (!$(".popup").find($(event.target)).length && !$(clickedDay).find($(event.target)).length) {
            resetSelection();
            $("body").unbind("mousedown");
        }
    });

    $("<div>").addClass("extend top").on({
        "mousedown": () => resizingDirection = -1,
        "touchstart": () => resizingDirection = -1,
    }).appendTo(time_selection_element);
    $("<div>").addClass("extend bottom").on({
        "mousedown": () => resizingDirection = 1,
        "touchstart": () => resizingDirection = 1,
    }).appendTo(time_selection_element);
};

var onMouseDownFunc = (event) => {
    if (clickedDay !== null) return;

    event.preventDefault();
    clickedDay = event.target;
    clickedPoint = positionCalculation(event);
    let time_selection = $("<div>")
        .addClass("time_selection")
        .css("top", clickedPoint + "px")
        .css("height", "1px")
        .appendTo($(event.target));

    if (new Date() > currentDate()) {
        resetSelection();
        return;
    }

    $("<div>")
        .addClass("start_time")
        .html(timeToClock(getStartTime()))
        .appendTo(time_selection);
    $("<div>")
        .addClass("end_time")
        .html(timeToClock(getEndTime()))
        .appendTo(time_selection);
};

var getRulesCovered = () => {
    let insideRules = [];
    rules.forEach(function(rule) {
        if (hoursInside(rule)) {
            insideRules.push(rule);
        }
    });
    return insideRules;
};

var hoursInside = (rule) => {
    let startTime = getDay() + getStartTime()/24;
    let endTime = getDay() + getEndTime()/24;
    let hours = 0;
    rule.periods.forEach(function(period) {
        let periodStartTime = period[0];
        let periodEndTime = (period[1] - periodStartTime + 7) % 7;
        let shiftedStartTime = (startTime - periodStartTime + 7) % 7;
        let shiftedEndTime = (endTime - periodStartTime + 7) % 7;
        if (shiftedStartTime > shiftedEndTime) {
            hours += Math.min(periodEndTime, shiftedEndTime) * 24;
        } else {
            hours += (Math.min(periodEndTime, shiftedEndTime) - Math.min(periodEndTime, shiftedStartTime)) * 24;
        }
    });
    return hours;
};

var isValid = () => {
    let coveredRules = getRulesCovered();
    if (coveredRules.length === 1) {
        return coveredRules[0].max_inside >= hoursInside(coveredRules[0]);
    }
    for (let ruleIndex = 0; ruleIndex < coveredRules.length; ruleIndex++) {
        if (coveredRules[ruleIndex].max_crossed < hoursInside(coveredRules[ruleIndex])) {
            return false;
        }
    }
    return true;
};

var limitTimeSelection = (direction) => {
    while (!isValid()) {
        if (direction === "top")
            $(".time_selection")
                .css("top", parseFloat($(".time_selection").css("top")) + 1 + "px")
                .css("height", parseFloat($(".time_selection").css("height")) - 1 + "px");
        else
            $(".time_selection")
                .css("height", parseFloat($(".time_selection").css("height")) - 1 + "px");
    }
};

var resizeTop = (event) => {
    let bottomPosition = parseFloat($(".time_selection").css("top")) + parseFloat($(".time_selection").css("height"));
    let currentY = Math.min(positionCalculation(event), bottomPosition - 1);
    $(".time_selection")
        .css("height", Math.max(bottomPosition - currentY, 1) + "px")
        .css("top", currentY + "px");
    if (new Date() > currentDate()) setLimitTop();
    limitTimeSelection("top");
    $(".time_selection > .start_time").html(timeToClock(getStartTime()));
};

var resizeBottom = (event) => {
    let topHeight = parseFloat($(".time_selection").css("top"));
    let currentY = Math.max(positionCalculation(event), topHeight);
    $(".time_selection").css("height", Math.max(currentY - topHeight, 1) + "px");
    limitTimeSelection("bottom");
    $(".time_selection > .end_time").html(timeToClock(getEndTime()));
};

var setLimitTop = () => {
    let topLimit = (new Date().getHours() / 24 + (new Date().getMinutes() + 1) / (24 * 60) + new Date().getSeconds() / (24 * 60 * 60)) * $(clickedDay).height();
    $(".time_selection")
        .css("height", parseFloat($(".time_selection").css("height")) + parseFloat($(".time_selection").css("top")) - topLimit + "px")
        .css("top", topLimit + "px");
};

var onMouseMoveFunc = (event) => {
    if (clickedDay !== event.target || selected) {
        if (resizingDirection === 1) resizeBottom(event);
        if (resizingDirection === -1) resizeTop(event);
        return;
    }

    let currentY = positionCalculation(event);
    $(".time_selection").css("top", Math.min(currentY, clickedPoint) + "px").css("height", Math.abs(currentY - clickedPoint) + "px");
    {# Do not allow the selection of an area earlier than the current time #}
    if (new Date() > currentDate()) setLimitTop();
    if (currentY > clickedPoint) limitTimeSelection("bottom");
    else limitTimeSelection("top");
    $(".time_selection > .start_time").html(timeToClock(getStartTime()));
    $(".time_selection > .end_time").html(timeToClock(getEndTime()));
};

{# The position calculation differs between touch and mouse events #}
var positionCalculation = (event) =>
    (event.touches === undefined ? event.pageY : event.touches[0].pageY) - $(clickedDay).offset().top;


$(".day").on({
    "touchstart": onMouseDownFunc, "touchend": onLetGoFunc, "touchmove": onMouseMoveFunc, "touchout": onLetGoFunc,
    "mousedown": onMouseDownFunc, "mouseup": onLetGoFunc, "mousemove": onMouseMoveFunc, "mouseout": onLetGoFunc,
});
