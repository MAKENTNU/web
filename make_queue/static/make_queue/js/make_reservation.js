$("#start_time").calendar({
        minDate: new Date(),
        ampm: false,
        endCalendar: $("#end_time"),
        initialDate: null,
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
    $('#machine_name_dropdown').toggleClass("disabled", false).dropdown("restore defaults");
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", true);
    $('#machine_name_dropdown .menu').toggleClass("menu", false);
    $('#machine_name_dropdown .' + value).toggleClass("menu", true);
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", false);
});

$('#machine_type_dropdown').dropdown("set selected", $('.selected_machine_type').data("value"));
$('#machine_name_dropdown').dropdown("set selected", $('.selected_machine_name').data("value"));

zeroPadDateElement = (val) => val < 10 ? "0" + val : val;

function formatDate(date) {
    return date.getFullYear() + "-" + zeroPadDateElement(date.getMonth() + 1) + "-" + zeroPadDateElement(date.getDate())
        + " " + zeroPadDateElement(date.getHours()) + ":" + zeroPadDateElement(date.getMinutes())
}

$('form').submit(function () {
    $("#start_time input").first().val(formatDate($("#start_time").calendar("get date")));
    $("#end_time input").first().val(formatDate($("#end_time").calendar("get date")));
});