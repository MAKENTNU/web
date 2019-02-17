function update_multiday() {
    let isMultiday = $('#standalone').prop('checked');
    $("#id_number_of_tickets").parent().toggleClass("disabled", !isMultiday);
    if (isMultiday) {
        $("#info-message-tickets").show();
        $("#info-message-tickets-repeating").hide();
    } else {
        $("#info-message-tickets").hide();
        $("#info-message-tickets-repeating").show();
    }
}

$(function () {
    update_multiday();
    $('input[type=radio][name=multiday]').change(function () {
        update_multiday();
    });

});
