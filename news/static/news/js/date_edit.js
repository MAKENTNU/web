$(function() {
    var start_time = $('#id_start_time');
    var end_time = $('#id_end_time');
    var start_date = $('#id_start_date');
    var end_date = $('#id_end_date');

    var wrapper = '<div class="ui calendar"></div>';

    start_time.wrap(wrapper);
    end_time.wrap(wrapper);
    start_date.wrap(wrapper);
    end_date.wrap(wrapper);

    start_time.parent().calendar({
        ampm: false,
        type: 'time'
    });
    end_time.parent().calendar({
        ampm: false,
        type: 'time'
    });
    start_date.parent().calendar({
        type: 'date',
        endCalendar: end_date,
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                var day = ("0" + date.getDate()).slice(-2);
                var month = ("0" + (date.getMonth() + 1)).slice(-2);
                var year = date.getFullYear();
                return year + '-' + month + '-' + day;
            }
        }
    });
    end_date.parent().calendar({
        type: 'date',
        startCalendar: start_date,
        formatter: {
            date: function (date, settings) {
                if (!date) return '';
                var day = ("0" + date.getDate()).slice(-2);
                var month = ("0" + (date.getMonth() + 1)).slice(-2);
                var year = date.getFullYear();
                return year + '-' + month + '-' + day;
            }
        }
    });
});
