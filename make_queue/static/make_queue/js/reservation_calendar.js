function getWeekNumber(date) {
    date = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
    var yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
    var weekNumber = Math.ceil((((date - yearStart) / 86400000) + 1) / 7);
    return weekNumber;
}

$(".make_reservation_calendar_time_table_row").click(function (event) {
    let clicked_ratio = (event.pageX - $(this).offset().left) / $(this).width();
    let hours = ("00" + Math.floor(clicked_ratio * 24)).substr(-2, 2);
    let minutes = ("00" + Math.floor((clicked_ratio * 24 % 1) * 60)).substr(-2, 2);
    let date = $(this).data("date");
    let machine_type = $(this).data("machine-type");
    let machine_pk = $(this).data("machine");
    document.location = "/reservation/make/" + date + "/" + hours + ":" + minutes + "/" + machine_type + "/" + machine_pk + "/";
});

$(".make_reservation_calendar_time_table_item").click(function (event) {
    return false;
});

$("#period").calendar({
        ampm: false,
        initialDate: null,
        type: 'date',
        onChange: function (date) {
            let current_location = document.location.href.split("/");
            current_location[current_location.length - 4] = date.getFullYear();
            current_location[current_location.length - 3] = getWeekNumber(date);
            document.location = current_location.join("/");
        }
    }
);