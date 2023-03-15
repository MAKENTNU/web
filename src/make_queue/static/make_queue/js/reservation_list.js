/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var csrfToken;

$("#hide-old-reservations").checkbox({
    onChange: function () {
        $(".past-reservation")
            .toggleClass("display-none", $(this).is(":checked"));
    },
});

$(".mark-reservation-finished").click(function () {
    const $button = $(this);

    function successFunc() {
        $(`.reservation-pk-${$button.data("pk")}`).addClass("display-none");
    }

    sendAjaxRequest("POST", $button.data("url"), successFunc,
        gettext("Marking reservation as finished failed with the following error message: %(error)s."));
});

$(".delete-reservation").click(function () {
    const $button = $(this);

    function successFunc() {
        $(`.reservation-pk-${$button.data("pk")}`).remove();
    }

    sendAjaxRequest("DELETE", $button.data("url"), successFunc,
        gettext("Deleting reservation failed with the following error message: %(error)s."));
});

function sendAjaxRequest(type, url, successFunc, unknownErrorMessage) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: type,
        url: url,
        success: successFunc,
        error: function (jqXHR, textStatus, errorThrown) {
            const errorMessage = jqXHR.responseJSON ? jqXHR.responseJSON.message : null;
            const message = errorMessage ? errorMessage : interpolate(
                unknownErrorMessage, {error: errorThrown}, true,
            );
            displayErrorToast(`${message}<br/>${gettext("Please refresh the page or contact the developers.")}`);
        },
    });
}

function displayErrorToast(message) {
    $("body").toast({
        displayTime: 0,
        message: message,
        class: "error",
    });
}
