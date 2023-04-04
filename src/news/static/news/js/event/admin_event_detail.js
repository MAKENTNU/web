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

            const isHidden = data["is_hidden"];
            if (toggle === "private")
                $element.attr("src", isHidden ? privateEventIcon : publicEventIcon);
            else {
                const $parent = $element.parent();
                const $shownIcon = $parent.find(".shown.hidden-field");
                const $hiddenIcon = $parent.find(".hidden.hidden-field");
                $shownIcon.toggleClass("display-none", isHidden);
                $hiddenIcon.toggleClass("display-none", !isHidden);
            }

            if (model === "event")
                $(`#message-${toggle}`).toggleClass("hidden", !isHidden);
        },
    });
}
