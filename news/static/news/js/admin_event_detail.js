/* `csrfToken`, `privateEventIcon` and `publicEventIcon` must be defined when linking this script */
var csrfToken;
var privateEventIcon;
var publicEventIcon;

$(".tabular.menu .item").tab();

$(".toggle").click(function () {
    toggle_post($(this), $(this).data("pk"), $(this).data("model"), $(this).data("toggle"));
});

function toggle_post($element, pk, model, toggle) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: "POST",
        url: `/news/admin/toggle/${model}/`,
        data: {
            "pk": pk,
            "toggle": toggle,
        },
        success: function (data) {
            if ($.isEmptyObject(data))
                return;

            const color = data["color"];
            if (toggle === "private") {
                $element.attr("src", (color === "yellow") ? privateEventIcon : publicEventIcon);
            } else {
                $element.removeClass("yellow grey").addClass(color);
            }

            if (model === "event")
                $(`#message-${toggle}`).toggleClass("hidden", color === "grey");
        },
    });
}
