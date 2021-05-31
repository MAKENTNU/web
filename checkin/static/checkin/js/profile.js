var csrfToken; // defined in profile.html

$('.ui.rating').rating();
$('.ui.dropdown').dropdown();
$('.rating.skill-lvl').rating('disable');

$('#star-rating').click(function () {
    let rating = $(this).rating('get rating');
    if (rating === $('#rating-input').val()) {
        $('#rating-input').val(0);
        $(this).rating('set rating', 0);
    } else {
        $('#rating-input').val(rating);
    }
});

$('.register-profile').click(function () {
    register_profile_post($(this));
});

function register_profile_post(element) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: "POST",
        url: '/checkin/register/profile/',
        data: {},
        success: function (data) {
            if (data['scan_exists']) {
                if (data['scan_is_recent']) {
                    element.removeClass('red');
                    element.removeAttr('data-tooltip');
                    element.removeAttr('data-position');
                    element.addClass('green');
                    element.addClass('disabled');
                    element.html(gettext("Registered"));
                } else {
                    element.addClass('red');
                    element.attr('data-tooltip', gettext("Scan card again!"));
                    element.attr('data-position', 'right center');
                }
            } else {
                element.addClass('red');
                element.attr('data-tooltip', gettext("Scan card"));
                element.attr('data-position', 'right center');
            }
            $(".message.negative").fadeOut();
        },
        error: function (jqXHR, error, errorthrown) {
            if (jqXHR.status === 409) {
                $("#duplicate_error").fadeIn();
            }
        },
    });
}

$('#profile-pic').click(function () {
    $('#input-image').click();
});

// When user has chosen image, send form to server
$('#input-image').change(function () {
    $('#image-form').submit();
});
