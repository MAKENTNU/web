$("#start_date").calendar({
        minDate: new Date(),
        ampm: false,
        endCalendar: $("#end_date"),
        initialDate: null,
    }
);

$("#end_date").calendar({
        ampm: false,
        startCalendar: $("#start_date")
});

$('.ui.dropdown').dropdown();
$('#event_checkbox').checkbox({
    onChange: function() {
        $("#event_name_input").toggleClass("make_non_visible", !$(this).is(':checked'))
    },
});

$('#machine_type_dropdown').dropdown('setting', 'onChange', function(value) {
    $('#machine_name_dropdown').toggleClass("disabled", false).dropdown("restore defaults");
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", true);
    $('#machine_name_dropdown .menu').toggleClass("menu", false);
    $('#machine_name_dropdown .'+value).toggleClass("menu", true);
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", false);
});

$('#machine_type_dropdown').dropdown("set selected", $('.selected_machine_type').data("value"));
$('#machine_name_dropdown').dropdown("set selected", $('.selected_machine_name').data("value"));