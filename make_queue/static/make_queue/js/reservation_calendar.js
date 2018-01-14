$(".make_reservation_calendar_time_table_row").click(function (event) {
    let clicked_ratio = (event.pageX - $(this).offset().left) / $(this).width();
    let hours = ("00" + Math.floor(clicked_ratio * 24)).substr(-2, 2);
    let minutes = ("00" + Math.floor((clicked_ratio * 24 % 1) * 60)).substr(-2, 2);
    let date = $(this).data("date");
    let machine_type = $(this).data("machine-type");
    let machine_pk = $(this).data("machine");
    document.location = "/reservation/make/" + date + "/" + hours + ":" + minutes + "/" + machine_type + "/" + machine_pk + "/";
});

$(".make_reservation_calendar_time_table_item").popup({on: "hover", position: "right center"});
$(".make_reservation_calendar_time_table_item").click(false);
$("#machine_type_dropdown").dropdown().dropdown("set selected", $('.selected_machine_type').data("value"))
    .dropdown("setting", "onChange", function (value) {
        document.location = value;
    });

$("#period").calendar({
        ampm: false,
        initialDate: null,
        type: 'date',
        onChange: function (value) {
            // TODO: FIX redirect to correct day
            console.log(value);
        }
    }
);