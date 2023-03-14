/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var csrfToken;
// noinspection ES6ConvertVarToLetConst
var registerProfileURL;

$(".container .ui.rating").rating();
$(".container .ui.dropdown").dropdown();
$(".rating.skill-lvl").rating("disable");

$("#star-rating").click(function () {
    const rating = $(this).rating("get rating");
    const $ratingInput = $("#rating-input");
    if (rating === $ratingInput.val()) {
        $ratingInput.val(0);
        $(this).rating("set rating", 0);
    } else {
        $ratingInput.val(rating);
    }
});

$(".register-profile").click(function () {
    registerProfilePost($(this));
});

function registerProfilePost($element) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: "POST",
        url: registerProfileURL,
        data: {},
        success: function (data) {
            if (data["scan_exists"]) {
                if (data["scan_is_recent"]) {
                    $element.removeClass("red");
                    $element.removeAttr("data-tooltip");
                    $element.removeAttr("data-position");
                    $element.addClass("green");
                    $element.addClass("disabled");
                    $element.html(gettext("Registered"));
                } else {
                    $element.addClass("red");
                    $element.attr("data-tooltip", gettext("Scan card again!"));
                    $element.attr("data-position", "right center");
                }
            } else {
                $element.addClass("red");
                $element.attr("data-tooltip", gettext("Scan card"));
                $element.attr("data-position", "right center");
            }
            $(".message.negative").fadeOut();
        },
        error: function (jqXHR, textStatus, errorthrown) {
            if (jqXHR.status === 409) {
                $("#duplicate-error").fadeIn();
            }
        },
    });
}

$("#profile-pic").click(function () {
    $("#input-image").click();
});

// When the user has selected an image, submit the form to the server
$("#input-image").change(function () {
    $("#image-form").submit();
});
