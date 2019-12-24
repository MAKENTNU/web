let reservations = [];
let reservationRules = [];
let reservationCalendarDate = new Date();
var canIgnoreRules; // Defined in calendar.html

function getFutureReservations(machine_id, force_new_time) {
    /**
     * Retrieves future reservations and all reservation rules from the server.
     */
    let jsonUrl = `${langPrefix}/reservation/json/${machine_id}`;
    if ($("#reserve_form").data("reservation")) {
        jsonUrl += "/" + $("#reserve_form").data("reservation");
    }
    $.getJSON(jsonUrl, function (data) {
        reservations.length = 0;
        $.each(data.reservations, function (index, value) {
            reservations.push({
                "start_time": new Date(Date.parse(value.start_date)),
                "end_time": new Date(Date.parse(value.end_date)),
            });
        });
        canIgnoreRules = data.canIgnoreRules;
        reservationRules.length = 0;
        $.each(data.rules, function (index, value) {
            reservationRules.push({
                "periods": value.periods,
                "max_inside": value.max_hours,
                "max_crossed": value.max_hours_crossed,
            });
        });
        // Indicates if we want to update the start date or not
        if (force_new_time) {
            let start_date = getFirstReservableTimeSlot(new Date());
            $("#start_time").calendar("set date", start_date);
            $("#end_time").calendar("set date", getMaxDateReservation(start_date));
        }
    });
}

function getWeekNumber(date) {
    /**
     * Returns the week number of a given date (this is not built in to JS)
     */
    date = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    let yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    return Math.ceil((((date - yearStart) / (24 * 60 * 60 * 1000)) + 1) / 7);
}

function updateReservationCalendar() {
    /**
     * Retrieves the reservation calendar for the date set for the reservation calendar
     */
    let weekNumber = getWeekNumber(reservationCalendarDate);
    let year = reservationCalendarDate.getFullYear();
    let machine_pk = $("#machine_name_dropdown").dropdown("get value");
    $.get(`${langPrefix}/reservation/calendar/${year}/${weekNumber}/${machine_pk}/`, {}, (data) => {
        $("#reservation_calendar").html(data);
        setupReservationCalendar();
    });
}

function getFirstReservableTimeSlot(date) {
    /**
     * Finds the first reservable time slot on or after the supplied date
     */
    let found = false;
    while (!found) {
        found = true;
        for (let index = 0; index < reservations.length; index++) {
            // Ignore 5 minute gaps
            if (date >= reservations[index].start_time - new Date(300000) && date < reservations[index].end_time) {
                found = false;
                date = reservations[index].end_time;
            }
        }
    }
    return date;
}

function isNonReservedDate(date) {
    /**
     * Checks if the given date is inside any reservation
     */
    for (let index = 0; index < reservations.length; index++) {
        if (date >= reservations[index].start_time && date < reservations[index].end_time) return false;
    }
    return true;
}

function isCompletelyReserved(start, end) {
    /**
     * Checks if the given time period is completely reserved (ignores open slots of less than 5 minutes)
     */
    let maxDifference = 5 * 60 * 1000;
    let reservationsPeriod = reservationsInPeriod(start, end);
    if (!reservationsPeriod.length) return false;
    reservationsPeriod.sort((a, b) => a.start_time - b.start_time);
    let currentTime = start;
    for (let index = 0; index < reservationsPeriod.length; index++) {
        if (reservationsPeriod[index].start_time > new Date(currentTime.valueOf() + maxDifference)) return false;
        currentTime = reservationsPeriod[index].end_time;
    }
    return currentTime >= new Date(end.valueOf() - maxDifference);
}

function reservationsInPeriod(start, end) {
    /**
     * Returns all reservations that are at least partially within the given time period.
     */
    let reservationsPeriod = [];
    for (let index = 0; index < reservations.length; index++) {
        let reservation = reservations[index];
        if ((reservation.start_time <= start && reservation.end_time > start) ||
            (reservation.start_time > start && reservation.end_time < end) ||
            (reservation.start_time < end && reservation.end_time > end))
            reservationsPeriod.push(reservation);
    }
    return reservationsPeriod;
}

function getMaxDateReservation(date) {
    /**
     *  Finds the latest date at which a reservation which starts at the given date can end and still be valid.
     */
    let maxDate = new Date(date.valueOf());
    let shouldRestrictToRules = !canIgnoreRules;
    if ($("#event_checkbox input").is(':checked') || $("#special_checkbox input").is(":checked")) {
        maxDate.setDate(maxDate.getDate() + 56);
        shouldRestrictToRules = false;
    } else {
        // Normal reservations should never be more than 1 week
        maxDate = new Date(maxDate.valueOf() + 7 * 24 * 60 * 60 * 1000 - 1000);
    }
    for (let index = 0; index < reservations.length; index++) {
        if (date <= reservations[index].start_time && reservations[index].start_time < maxDate)
            maxDate = new Date(reservations[index].start_time.valueOf());
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
     * Updates the max date of the calender indicating the end time of the reservation.
     */
    let currentStartDate = $("#start_time").calendar("get date");
    if (currentStartDate !== null) {
        $("#end_time").calendar("setting", 'maxDate', getMaxDateReservation(currentStartDate));
    }
}

let minDateStartTime = new Date();
if ($("#start_time").children("div").hasClass("disabled")) {
    minDateStartTime = new Date(new Date($("#start_time").find("input").val()) - new Date(5 * 60 * 1000));
}
$("#start_time").calendar({
        minDate: minDateStartTime,
        maxDate: maximum_day,
        ampm: false,
        mode: "minute",
        endCalendar: $("#end_time"),
        initialDate: new Date($("#start_time").find("input").val()),
        firstDayOfWeek: 1,
        isDisabled: function (date, mode) {
            if (date === undefined) return true;
            if (mode === "minute") return !isNonReservedDate(date);
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
            if (value === undefined) return true;
            let shouldChange = isNonReservedDate(value);
            if (shouldChange) {
                $("#end_time").calendar("setting", 'maxDate', getMaxDateReservation(value));
            }
            return shouldChange;
        },
    },
);

$("#end_time").calendar({
    ampm: false,
    firstDayOfWeek: 1,
    startCalendar: $("#start_time"),
    minDate: new Date(),
});

$('.ui.dropdown').dropdown();
$('#event_checkbox').checkbox({
    onChange: function () {
        $("#event_name_input").toggleClass("make_hidden", !$(this).is(':checked'));
        if ($(this).is(':checked')) {
            $('#special_checkbox').checkbox("uncheck");
            $('#maintenance_checkbox').checkbox("uncheck");
            $("#start_time").calendar("setting", "maxDate", null);
        } else {
            $("#start_time").calendar("setting", "maxDate", maximum_day);
        }
        updateMaxEndDate();
    },
});

$('#special_checkbox').checkbox({
    onChange: function () {
        $("#special_input").toggleClass("make_hidden", !$(this).is(':checked'));
        if ($(this).is(':checked')) {
            $('#event_checkbox').checkbox("uncheck");
            $('#maintenance_checkbox').checkbox("uncheck");
            $("#start_time").calendar("setting", "maxDate", null);
        } else {
            $("#start_time").calendar("setting", "maxDate", maximum_day);
        }
        updateMaxEndDate();
    },
});

$('#maintenance_checkbox').checkbox({
    onChange: function () {
        if ($(this).is(':checked')) {
            $('#event_checkbox').checkbox("uncheck");
            $('#special_checkbox').checkbox("uncheck");
            $("#start_time").calendar("setting", "maxDate", null);
        } else {
            $("#start_time").calendar("setting", "maxDate", maximum_day);
        }
        updateMaxEndDate();
    },
});

$('#machine_type_dropdown').dropdown('setting', 'onChange', function (selectedMachineType) {
    if (!$('#machine_type_dropdown').is(".disabled")) {
        $('#machine_name_dropdown').toggleClass("disabled", false).dropdown("restore defaults");

        // Replace the shown machine items from the last selected machine type with the ones from the currently selected machine type
        $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", true);
        $(`#machine_name_dropdown .menu .item.${selectedMachineType}`).toggleClass("make_hidden", false);
    }
}).dropdown("set selected", $('.selected_machine_type').data("value"));

$('#machine_name_dropdown').dropdown("set selected", $('.selected_machine_name').data("value")).dropdown('setting', "onChange", function (value) {
    if (value !== "default" && value !== "") {
        getFutureReservations(value, true);
        updateReservationCalendar();
    }
    $("#start_time > div, #end_time > div").toggleClass('disabled', value === "default");
    $("#start_time, #end_time").calendar('clear');
});

zeroPadDateElement = (val) => (val < 10) ? `0${val}` : val;

function formatDate(date) {
    /**
     * Formats the given date in a format that Django understands
     */
    return date.getFullYear() + "-" + zeroPadDateElement(date.getMonth() + 1) + "-" + zeroPadDateElement(date.getDate())
        + " " + zeroPadDateElement(date.getHours()) + ":" + zeroPadDateElement(date.getMinutes());
}

$('form').submit(function (event) {
    let is_valid = true;
    $("#machine_name_dropdown").toggleClass("error_border", false);
    $("#start_time").find("input").toggleClass("error_border", false);
    $("#end_time").find("input").toggleClass("error_border", false);
    $("#event_pk").toggleClass("error_border", false);


    if ($("#machine_name_dropdown").dropdown("get value") === "default") {
        $("#machine_name_dropdown").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#start_time").calendar("get date") === null) {
        $("#start_time").find("input").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#end_time").calendar("get date") === null) {
        $("#end_time").find("input").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#event_checkbox input").is(':checked') && $("#event_pk").dropdown("get value") === "") {
        $("#event_pk").toggleClass("error_border", true);
        is_valid = false;
    }

    if (!is_valid) return event.preventDefault();

    $("#start_time input").first().val(formatDate($("#start_time").calendar("get date")));
    $("#end_time input").first().val(formatDate($("#end_time").calendar("get date")));
});

function setupReservationCalendar() {
    /**
     * Registration of custom onclick functions for the reservation calendar (it is loaded async)
     */

    $("#now_button").click(() => {
        reservationCalendarDate = new Date();
        updateReservationCalendar();
    });

    $("#prev_week_button").click(() => {
        reservationCalendarDate.setDate(reservationCalendarDate.getDate() - 7);
        updateReservationCalendar();
    });

    $("#next_week_button").click(() => {
        reservationCalendarDate.setDate(reservationCalendarDate.getDate() + 7);
        updateReservationCalendar();
    });

}

setupReservationCalendar();

$('.message .close').on('click', function () {
    $(this).closest('.message').transition('fade');
});

if ($("#start_time").calendar("get date") !== null) {
    reservationCalendarDate = $("#start_time").calendar("get date");
}
updateReservationCalendar();

function timeSelectionPopupHTML(date, startTime, endTime, machine) {
    /**
     * Creates a valid popup for the time selection utility in the reservation calendar
     */
    return $("<div>").addClass("ui make_yellow button").html(gettext("Choose time")).click(() => {
        $("#start_time").calendar("set date", new Date(`${date} ${startTime}`));
        $("#end_time").calendar("set date", new Date(`${date} ${endTime}`));
        $("body").mousedown();
    });
}
