var wrapper = '<div class="ui calendar"></div>';

function fix_date(element) {
    element.wrap(wrapper);
    element.parent().calendar({
        type: 'date',
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                var day = ("0" + date.getDate()).slice(-2);
                var month = ("0" + (date.getMonth() + 1)).slice(-2);
                var year = date.getFullYear();
                return day + '.' + month + '.' + year;
            }
        }
    });
}

function fix_time(element) {
    element.wrap(wrapper);
    element.parent().calendar({
        ampm: false,
        type: 'time'
    });
}

$(function() {
    fix_time($('#id_start_time'));
    fix_time($('#id_end_time'));
    fix_date($('#id_start_date'));
    fix_date($('#id_end_date'));
});
