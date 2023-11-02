/*
 * Linking `reservation_form.css` is required when linking this script.
 * The `var` variables below must also be defined.
*/
// noinspection ES6ConvertVarToLetConst
var maximumDay;
// noinspection ES6ConvertVarToLetConst
var shouldForceNewTime;

const reservations = [];
const reservationRules = [];
let canIgnoreRules = false;

const $startTimeField = $("#start-time");
const $startTimeFieldInput = $startTimeField.find("input");
const $endTimeField = $("#end-time");
const $eventField = $("#event-pk");



function isNonReservedDate(date) {
    /**
     * Checks if the given date is inside any reservation
     */
    for (const reservation of reservations) {
        if (date >= reservation.startTime && date < reservation.endTime)
            return false;
    }
    return true;
}

function isCompletelyReserved(start, end) {
    /**
     * Checks if the given time period is completely reserved (ignores open slots of less than 5 minutes)
     */
    const maxDifference = 5 * 60 * 1000;
    const reservationsInPeriod = getReservationsInPeriod(start, end);
    if (!reservationsInPeriod.length)
        return false;
    reservationsInPeriod.sort((a, b) => a.startTime - b.startTime);
    let currentTime = start;
    for (const reservation of reservationsInPeriod) {
        if (reservation.startTime > new Date(currentTime.valueOf() + maxDifference))
            return false;
        currentTime = reservation.endTime;
    }
    return currentTime >= new Date(end.valueOf() - maxDifference);
}

function getReservationsInPeriod(start, end) {
    /**
     * Returns all reservations that are at least partially within the given time period.
     */
    let reservationsInPeriod = [];
    for (const reservation of reservations) {
        if ((reservation.startTime <= start && reservation.endTime > start) ||
            (reservation.startTime > start && reservation.endTime < end) ||
            (reservation.startTime < end && reservation.endTime > end)) {
            reservationsInPeriod.push(reservation);
        }
    }
    return reservationsInPeriod;
}

let minDateStartTime = new Date();

$startTimeField.calendar({
        minDate: minDateStartTime,
        maxDate: maximumDay,
        mode: "day",
        endCalendar: $endTimeField,
        initialDate: new Date($startTimeFieldInput.val()),
        firstDayOfWeek: 1,
        isDisabled: function (date, mode) {
            if (!date)
                return true;
           /* if (mode === "minute")
                return !isNonReservedDate(date);
            if (mode === "hour") {
                date = new Date(date.valueOf());
                date.setMinutes(0, 0, 0);
                return isCompletelyReserved(date, new Date(date.valueOf() + 60 * 60 * 1000));
            }*/
            if (mode === "day") {
                date = new Date(date.valueOf());
                date.setHours(0, 0, 0, 0);
                return isCompletelyReserved(date, new Date(date.valueOf() + 24 * 60 * 60 * 1000));
            }
            return false;
        },
        onChange: function (value) {
            if (value === undefined)
                return true;
            const shouldChange = isNonReservedDate(value);
            if (shouldChange) {
                $endTimeField.calendar("setting", "maxDate", getMaxDateReservation(value));
            }
            return shouldChange;
        },
    },
);

$("form").submit(function (event) {
    let is_valid = true;
    $machineNameDropdown.toggleClass("error-border", false);
    $startTimeFieldInput.toggleClass("error-border", false);
    $endTimeFieldInput.toggleClass("error-border", false);
    $eventField.toggleClass("error-border", false);

    if ($machineNameDropdown.dropdown("get value") === "default") {
        $machineNameDropdown.toggleClass("error-border", true);
        is_valid = false;
    }

    if ($startTimeField.calendar("get date") === null) {
        $startTimeFieldInput.toggleClass("error-border", true);
        is_valid = false;
    }

    if ($endTimeField.calendar("get date") === null) {
        $endTimeFieldInput.toggleClass("error-border", true);
        is_valid = false;
    }

    if ($("#event-checkbox input").is(":checked") && $eventField.dropdown("get value") === "") {
        $eventField.toggleClass("error-border", true);
        is_valid = false;
    }

    if (!is_valid)
        return event.preventDefault();
});

function timeSelectionPopupHTML() {
    /**
     * Creates a valid popup for the time selection utility in the reservation calendar
     */
    const $button = $("<div>").addClass("ui fluid make-bg-yellow button").html(gettext("Choose time"));
    $button.on("mousedown touchstart", () => {
        $startTimeField.calendar("set date", calendar.getSelectionStartTime());
        $endTimeField.calendar("set date", calendar.getSelectionEndTime());
        calendar.resetSelection();
    });
    return $button;
}

const calendar = new ReservationCalendar($(".reservation-calendar"), {
    date: new Date(),
    machineType: getMachineType(),
    machine: getMachine(),
    selection: true,
    canIgnoreRules: false,
    selectionPopupContent: timeSelectionPopupHTML,
});

if ($startTimeField.calendar("get date") !== null) {
    calendar.showDate($startTimeField.calendar("get date"));
}

getFutureReservations($machineNameDropdown.dropdown("get value"), shouldForceNewTime);
