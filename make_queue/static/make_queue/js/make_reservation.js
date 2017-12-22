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

$("#submit").click(function(){
   $("#reserve_form").submit();
});

$('.ui.dropdown').dropdown();
$('.ui.checkbox').checkbox();

$('#machine_type_dropdown').dropdown('setting', 'onChange', function(value) {
    $('#machine_name_dropdown').toggleClass("disabled", false).dropdown("restore defaults");
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", true);
    $('#machine_name_dropdown .menu').toggleClass("menu", false);
    $('#machine_name_dropdown .'+value).toggleClass("menu", true);
    $('#machine_name_dropdown .menu .item').toggleClass("make_hidden", false);
});