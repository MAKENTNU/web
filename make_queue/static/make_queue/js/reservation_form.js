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

const $machineNameDropdown = $("#machine-name-dropdown");
const $startTimeField = $("#start-time");
const $startTimeFieldInput = $startTimeField.find("input");
const $endTimeField = $("#end-time");
const $endTimeFieldInput = $endTimeField.find("input");
const $eventField = $("#event-pk");

function getFutureReservations(machineID, forceNewTime) {
    /**
     * Retrieves future reservations and all reservation rules from the server.
     */
    let jsonUrl = `${LANG_PREFIX}/reservation/json/${machineID}/`;
    const reservationPK = $("#reservation-form").data("reservation");
    if (reservationPK) {
        jsonUrl += `${reservationPK}/`;
    }
    $.getJSON(jsonUrl, function (data) {
        reservations.length = 0;
        $.each(data.reservations, function (index, value) {
            reservations.push({
                // The values from the server are ISO-formatted strings
                startTime: new Date(value.start_time),
                endTime: new Date(value.end_time),
            });
        });

        calendar.updateCanBreakRules(data.canIgnoreRules);
        canIgnoreRules = data.canIgnoreRules;

        reservationRules.length = 0;
        $.each(data.rules, function (index, value) {
            reservationRules.push({
                periods: value.periods,
                max_inside: value.max_hours,
                max_crossed: value.max_hours_crossed,
            });
        });
        // Indicates if we want to update the start date or not
        if (forceNewTime) {
            const startTime = getFirstReservableTimeSlot(new Date());
            $startTimeField.calendar("set date", startTime);
            $endTimeField.calendar("set date", getMaxDateReservation(startTime));
        }
    });
}

function getFirstReservableTimeSlot(date) {
    /**
     * Finds the first reservable time slot on or after the supplied date
     */
    let found = false;
    while (!found) {
        found = true;
        for (let reservation of reservations) {
            // Ignore 5 minute gaps
            if (date >= reservation.startTime - new Date(300000) && date < reservation.endTime) {
                found = false;
                date = reservation.endTime;
            }
        }
    }
    return date;
}

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

function getMaxDateReservation(date) {
    /**
     *  Finds the latest date at which a reservation which starts at the given date can end and still be valid.
     */
    let maxDate = new Date(date.valueOf());
    let shouldRestrictToRules = !canIgnoreRules;
    if ($("#event-checkbox input").is(":checked") || $("#special-checkbox input").is(":checked")) {
        maxDate.setDate(maxDate.getDate() + 56);
        shouldRestrictToRules = false;
    } else {
        // Normal reservations should never be more than 1 week
        maxDate = new Date(maxDate.valueOf() + 7 * 24 * 60 * 60 * 1000 - 1000);
    }
    for (const reservation of reservations) {
        if (date <= reservation.startTime && reservation.startTime < maxDate)
            maxDate = new Date(reservation.startTime.valueOf());
    }
    if (shouldRestrictToRules) {
        // If the user/reservation type cannot ignore rules, shrink the reservation until it
        // is valid given the rules for the machine type
        return modifyToFirstValid(reservationRules, date, maxDate, 1);
    }
    return maxDate;
}

function updateMaxEndDate() {
    /**
     * Updates the max date of the calendar indicating the end time of the reservation.
     */
    const currentStartDate = $startTimeField.calendar("get date");
    if (currentStartDate !== null) {
        $endTimeField.calendar("setting", "maxDate", getMaxDateReservation(currentStartDate));
    }
}

let minDateStartTime = new Date();
if ($startTimeField.children("div").hasClass("disabled")) {
    minDateStartTime = new Date(new Date($startTimeFieldInput.val()) - new Date(5 * 60 * 1000));
}
$startTimeField.calendar({
        minDate: minDateStartTime,
        maxDate: maximumDay,
        mode: "minute",
        endCalendar: $endTimeField,
        initialDate: new Date($startTimeFieldInput.val()),
        firstDayOfWeek: 1,
        isDisabled: function (date, mode) {
            if (date === undefined)
                return true;
            if (mode === "minute")
                return !isNonReservedDate(date);
            if (mode === "hour") {
                date = new Date(date.valueOf());
                date.setMinutes(0, 0, 0);
                return isCompletelyReserved(date, new Date(date.valueOf() + 60 * 60 * 1000));
            }
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

$endTimeField.calendar({
    firstDayOfWeek: 1,
    startCalendar: $startTimeField,
    minDate: new Date(),
});

$("#reservation-form .ui.dropdown").dropdown();
$("#event-checkbox").checkbox({
    onChange: function () {
        $("#event-name-input").toggleClass("display-none", !$(this).is(":checked"));
        if ($(this).is(":checked")) {
            $("#special-checkbox").checkbox("uncheck");
            $startTimeField.calendar("setting", "maxDate", null);
        } else {
            $startTimeField.calendar("setting", "maxDate", maximumDay);
        }
        updateMaxEndDate();
    },
});
$("#special-checkbox").checkbox({
    onChange: function () {
        $("#special-input").toggleClass("display-none", !$(this).is(":checked"));
        if ($(this).is(":checked")) {
            $("#event-checkbox").checkbox("uncheck");
            $startTimeField.calendar("setting", "maxDate", null);
        } else {
            $startTimeField.calendar("setting", "maxDate", maximumDay);
        }
        updateMaxEndDate();
    },
});

$("#machine-type-dropdown").dropdown({
    onChange: function (selectedMachineType, text, $choice) {
        if (!$("#machine-type-dropdown").is(".disabled")) {
            $machineNameDropdown.toggleClass("disabled", false).dropdown("restore defaults");

            // Replace the shown machine items from the last selected machine type with the ones from the currently selected machine type
            $("#machine-name-dropdown .menu .item").toggleClass("display-none", true);
            $(`#machine-name-dropdown .menu .item.machine-type-${selectedMachineType}`).toggleClass("display-none", false);
        }
    },
}).dropdown(
    "set selected", $(".selected-machine-type").data("value"),
);

$machineNameDropdown.dropdown(
    "set selected", $(".selected-machine-name").data("value"),
).dropdown({
    onChange: function (value, text, $choice) {
        if (value && value !== "default") {
            getFutureReservations(value, true);
            calendar.changeMachine(value);
        }
        $("#start-time > div, #end-time > div").toggleClass("disabled", value === "default");
        $("#start-time, #end-time").calendar("clear");
    },
});

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

function getMachine() {
    return $machineNameDropdown.dropdown("get value");
}

const calendar = new ReservationCalendar($(".reservation-calendar"), {
    date: new Date(),
    machine: getMachine(),
    selection: true,
    canBreakRules: false,
    selectionPopupContent: timeSelectionPopupHTML,
});

if ($startTimeField.calendar("get date") !== null) {
    calendar.showDate($startTimeField.calendar("get date"));
}

getFutureReservations($machineNameDropdown.dropdown("get value"), shouldForceNewTime);
