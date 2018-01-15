let reservations = [];

function getFutureReservations(machine_type, machine_id) {
    $.getJSON("/reservation/json/" + machine_type + "/" + machine_id, function (data) {
        reservations.length = 0;
        $.each(data.reservations, function (index, value) {
            reservations.push({
                "start_time": new Date(Date.parse(value.start_date)),
                "end_time": new Date(Date.parse(value.end_date)),
            });
        });
        return reservations;
    })
}

function isNonReservedDate(date) {
    for (let index = 0; index < reservations.length; index++) {
        if (date >= reservations[index].start_time && date < reservations[index].end_time) return false;
    }
    return true;
}

function isReservedHour(date) {
    let endHour = new Date(date.valueOf());
    endHour.setHours(endHour.getHours() + 1);
    for (let index = 0; index < reservations.length; index++) {
        if (date >= reservations[index].start_time && endHour <= reservations[index].end_time) return true;
    }
    return false;
}

function getMaxDateReservation(date) {
    let maxDate = new Date(date.valueOf());
    maxDate.setDate(maxDate.getDate() + 5);
    for (let index = 0; index < reservations.length; index++) {
        if (date <= reservations[index].start_time && reservations[index].start_time < maxDate)
            maxDate = new Date(reservations[index].start_time.valueOf());
    }
    return maxDate;
}

$("#start_time").calendar({
        minDate: new Date(),
        ampm: false,
        endCalendar: $("#end_time"),
        initialDate: null,
        isDisabled: function (date, mode) {
            if (mode === "minute") return !isNonReservedDate(date);
            if (mode === "hour") return isReservedHour(date);
            return false;
        },
        onChange: function (value) {
            if (value === undefined) return true;
            let shouldChange = isNonReservedDate(value);
            if (shouldChange) {
                $("#end_time").calendar("setting", 'maxDate', getMaxDateReservation(value));
            }
            return shouldChange;
        }
    }
);

$("#end_time").calendar({
    ampm: false,
    startCalendar: $("#start_time"),
});

$('.ui.dropdown').dropdown();
$('#event_checkbox').checkbox({
    onChange: function () {
        $("#event_name_input").toggleClass("make_non_visible", !$(this).is(':checked'))
    },
});

$('#machine_type_dropdown').dropdown('setting', 'onChange', function (value) {
    if (!$('#machine_type_dropdown').is(".disabled")) {
        $('#machine_name_dropdown').toggleClass("disabled", false).dropdown("restore defaults");
        $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", true);
        $('#machine_name_dropdown .menu').toggleClass("menu", false);
        $('#machine_name_dropdown .' + value).toggleClass("menu", true);
        $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", false);
    }
}).dropdown("set selected", $('.selected_machine_type').data("value"));

$('#machine_name_dropdown').dropdown("set selected", $('.selected_machine_name').data("value")).dropdown('setting', "onChange", function (value) {
    if (value !== "default") getFutureReservations($('#machine_type_dropdown').dropdown('get value'), value);
    $("#start_time > div, #end_time > div").toggleClass('disabled', value === "default");
    $("#start_time, #end_time").calendar('clear');
});

zeroPadDateElement = (val) => val < 10 ? "0" + val : val;

function formatDate(date) {
    return date.getFullYear() + "-" + zeroPadDateElement(date.getMonth() + 1) + "-" + zeroPadDateElement(date.getDate())
        + " " + zeroPadDateElement(date.getHours()) + ":" + zeroPadDateElement(date.getMinutes())
}

$('form').submit(function () {
    $("#start_time input").first().val(formatDate($("#start_time").calendar("get date")));
    $("#end_time input").first().val(formatDate($("#end_time").calendar("get date")));
});

getFutureReservations("3D-printer", 1);
console.log(reservations);