$(document).ready(function() {
    $('img').each(function() {
        if ($(this).css('float') === 'left') {
            $(this).css('margin-left', '0');
        }
        if ($(this).css('float') === 'right') {
            $(this).css('margin-right', '0');
        }
    });
});
