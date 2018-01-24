function filterUsers(searchName) {
    $(".users > .item").each(function (index, element) {
        let username = $(element).data("username");
        let fullname = $(element).data("fullname");
        $(element).toggleClass("make_hidden", !isSearchEqual(searchName, username) && !isSearchEqual(searchName, fullname));
    });
}

function isSearchEqual(search, actualValue) {
    return actualValue.toLowerCase().split(" ").join("").indexOf(search.toLowerCase().split(" ").join("")) > -1;
}

function successfulUpdateButton(element) {
    element.toggleClass("success_submit", true);
    element.toggleClass("loading_submit", false);
    element.text("Endring lagret");
    setTimeout(() => {
        element.toggleClass("success_submit", false);
        element.text("Lagre")
    }, 5000);
}

function loadingButton(element) {
    element.toggleClass("loading_submit", true);
    element.text("Lagrer")
}

function initialize_user_handlers() {
    $("#3d-quota-can-print").closest(".checkbox").checkbox();
    $("#3D-Printer_card").find("> .button").on("click", function (event) {
        let button = $(this);
        loadingButton(button);
        $.post("/reservation/quota/update/3D-printer/", {
            csrfmiddlewaretoken: $("#csrf input").val(),
            username: $("#current_username").data("username"),
            can_print: $("#3d-quota-can-print").closest("checkbox").is(":checked"),
            max_length_reservation: $("#3d-quota-len-res").val(),
            max_number_of_reservations: $("#3d-quota-num-res").val()
        }, () => successfulUpdateButton(button)
        )
    });
    $("#Sewing_card").find("> .button").on("click", function (event) {
        let button = $(this);
        loadingButton(button);
        $.post("/reservation/quota/update/sewing/", {
                csrfmiddlewaretoken: $("#csrf input").val(),
                username: $("#current_username").data("username"),
                max_length_reservation: $("#sewing-quota-len-res").val(),
                max_number_of_reservations: $("#sewing-quota-num-res").val()
            }, () => successfulUpdateButton(button)
        )
    })
}

$("#user_search_field input").on('input', function (event) {
    filterUsers(event.target.value);
});

$(".user_select").each(function (index, element) {
    $(element).on("click", function (event) {
        let username = $(element).closest(".user_element").data("username");
        $.ajax("/reservation/quota/" + username + "/", {
            success: function (data, textStatus) {
                $("#quota_user").html(data);
                initialize_user_handlers();
            }
        })
    })
});

initialize_user_handlers();