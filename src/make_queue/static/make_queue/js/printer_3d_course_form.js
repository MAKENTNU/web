$(".clear-dropdown").click(function () {
    $(this).closest("div.ui.field").find("div.dropdown")
        .dropdown("clear")
        .find("input.search").val("");
});

$("input[name='username']").focusout((event) => {
    $.ajax(`${LANG_PREFIX}/users/username/${$(event.target).val()}/`, {
        success: function (data) {
            const fullName = data["full_name"];
            if (fullName)
                $("input[name='name']").val(fullName);
            $("#username-not-found-warning").fadeOut();
        },
        error: function () {
            $("#username-not-found-warning").fadeIn();
        },
    });
    $("#user").closest(".dropdown").dropdown("set selected", $(event.target).val());
});
