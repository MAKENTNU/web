var popupTimer;

function delayPopup(popup) {
    popupTimer = setTimeout(function() { $(popup).popup('hide') }, 4200);
}

$(document).ready(function () {
    $('.copy-token').click(function (){
        clearTimeout(popupTimer);

        var $input = $(this).closest('div').find('.copy-input');

        /* Select the text field */
        $input.select();

        /* Copy the text inside the text field */
        document.execCommand("copy");

        $(this)
            .popup({
                title: gettext('Successfully copied to clipboard!'),
                on: 'manual',
                exclusive: true
            })
            .popup('show')
        ;
        // Hide popup after 5 seconds
        delayPopup(this);
    });

});
