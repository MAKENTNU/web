function update_multiday() {
    var multiday = $('#id_multiday').prop('checked');
    console.log(multiday);
    if (multiday) {
        $('#id_hoopla').parent().css('display', 'block');
    } else {
        $('#id_hoopla').parent().css('display', 'none');
    }
}

$(function () {
    update_multiday();
    $('#id_multiday').change(function () {
        update_multiday();
    });

});
