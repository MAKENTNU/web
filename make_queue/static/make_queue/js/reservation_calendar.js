function getWeekNumber(date) {
    date = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    let yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    let weekNumber = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
    return weekNumber;
}

$(".make_reservation_calendar_time_table_row.can_make_reservation").click(function (event) {
    let clicked_ratio = (event.pageX - $(this).offset().left) / $(this).width();
    let hours = ("00" + Math.floor(clicked_ratio * 24)).substr(-2, 2);
    let minutes = ("00" + Math.floor((clicked_ratio * 24 % 1) * 60)).substr(-2, 2);
    let date = $(this).data("date");
    let machine_type = $(this).data("machine-type");
    let machine_pk = $(this).data("machine");
    document.location = langPrefix + "/reservation/make/" + date + "/" + hours + ":" + minutes + "/" + machine_type + "/" + machine_pk + "/";
});

$(".make_reservation_calendar_time_table_item").click(() => false);
$(".make_reservation_calendar_time_table_event").click((e) => document.location = $(e.target).data("event-url"));

$("#period_desktop, #period_mobile").calendar({
        ampm: false,
        initialDate: null,
        type: 'date',
        onChange: function (date) {
            let current_location = document.location.href.split("/");
            current_location[current_location.length - 4] = date.getFullYear();
            current_location[current_location.length - 3] = getWeekNumber(date);
            document.location = current_location.join("/");
        },
    },
);

$(".enable_popup").popup();

if (allowed) {
    function timeSelectionPopupHTML(date, startTime, endTime, machine) {
        let container = $("<div>");
        $("<div>").addClass("header").html(gettext("New reservation")).appendTo(container);
        $("<div>").html(date).appendTo(container);
        $("<div>").html(startTime + " - " + endTime).appendTo(container);
        let form = $("<form>").attr("method", "POST").attr("action", langPrefix + "/reservation/make/" + machine.pk + "/").addClass("ui form").appendTo(container);
        $("input[name=csrfmiddlewaretoken]").clone().appendTo(form);
        $("<input>").addClass("make_hidden").val(date + " " + startTime).attr("name", "start_time").appendTo(form);
        $("<input>").addClass("make_hidden").val(date + " " + endTime).attr("name", "end_time").appendTo(form);
        $("<input>").addClass("make_hidden").val(machine.type).attr("name", "machine_type").appendTo(form);
        $("<input>").addClass("make_hidden").val(machine.pk).attr("name", "machine_name").appendTo(form);
        $("<input>").attr("type", "submit").addClass("ui time_selection_button make_yellow button").val(gettext("Reserve")).appendTo(form);
        return container.children();
    }
} else {
    function timeSelectionPopupHTML(date, startTime, endTime, machine) {
        return $("<div>").html(gettext("Can't add more reservations"));
    }
}
