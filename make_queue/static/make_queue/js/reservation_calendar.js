$(".make_reservation_calendar_time_table").click(function (event) {
    let clicked_ratio = (event.pageY - $(this).offset().top)/$(this).height();
    let hours = ("00" + Math.floor(clicked_ratio*24)).substr(-2, 2);
    let minutes = ("00" + Math.floor((clicked_ratio*24%1)*60)).substr(-2, 2);
    let data_element = $(this).closest(".make_reservation_calendar_time_table");
    let date = data_element.data("date");
    let machine_type = data_element.data("machine-type");
    let machine_pk = data_element.data("machine");
    document.location = "/reservation/make/"+date+"/"+hours+":"+minutes+"/"+machine_type+"/"+machine_pk+"/";
});

$(".make_reservation_calendar_time_table_item").popup({on: "hover", position: "right center"});