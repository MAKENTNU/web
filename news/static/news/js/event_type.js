function update_event_type() {
    let isStandalone = $('#standalone').prop('checked');
    $("#id_number_of_tickets").parent().toggleClass("disabled", !isStandalone);
    if (isStandalone) {
        $("#info-message-tickets").show();
        $("#info-message-tickets-repeating").hide();
    } else {
        $("#info-message-tickets").hide();
        $("#info-message-tickets-repeating").show();
    }
}

$(function () {
    update_event_type();
    $('input[type=radio][name=event_type]').change(function () {
        update_event_type();
    });

});
