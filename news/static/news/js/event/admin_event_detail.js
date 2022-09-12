/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var csrfToken;
// noinspection ES6ConvertVarToLetConst
var privateEventIcon;
// noinspection ES6ConvertVarToLetConst
var publicEventIcon;

$(".tabular.menu .item").tab();

$(".toggle").click(function () {
    togglePost($(this), $(this).data("post-url"), $(this).data("model"), $(this).data("toggle"));
});

function togglePost($element, postURL, model, toggle) {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrfToken);
        },
    });
    $.ajax({
        type: "POST",
        url: postURL,
        data: {
            "toggle_attr": toggle,
        },
        success: function (data) {
            if ($.isEmptyObject(data))
                return;

            const color = data["color"];
            if (toggle === "private")
                $element.attr("src", (color === "yellow") ? privateEventIcon : publicEventIcon);
            else
                $element.removeClass("yellow grey").addClass(color);

            if (model === "event")
                $(`#message-${toggle}`).toggleClass("hidden", color === "grey");
        },
    });
}
