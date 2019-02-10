let wrapper = '<div class="ui calendar"></div>';

function fix_date(element) {
    element.wrap(wrapper);
    element.parent().calendar({
        type: 'date',
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                let day = ("0" + date.getDate()).slice(-2);
                let month = ("0" + (date.getMonth() + 1)).slice(-2);
                let year = date.getFullYear();
                return day + '.' + month + '.' + year;
            },
        },
    });
}

function fix_time(element) {
    element.wrap(wrapper);
    element.parent().calendar({
        ampm: false,
        type: 'time',
    });
}

$(function () {
    fix_time($('#id_pub_time'));
    fix_date($('#id_pub_date'));
});
