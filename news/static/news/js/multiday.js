function update_multiday() {
    let is_multiday = $('#id_multiday').prop('checked');
    $("#id_number_of_tickets").parent().toggleClass("disabled", !is_multiday);

}

$(function () {
    update_multiday();
    $('#id_multiday').change(function () {
        update_multiday();
    });

});
