$(function() {
    var pub_date = $('#id_pub_date');
    var pub_time = $('#id_pub_time');

    var wrapper = '<div class="ui calendar"></div>';

    pub_date.wrap(wrapper);
    pub_time.wrap(wrapper);

    pub_time.parent().calendar({
        ampm: false,
        type: 'time'
    });
    pub_date.parent().calendar({
        type: 'date',
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
