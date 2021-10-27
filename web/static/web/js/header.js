$("#nav-user-dropdown, #makerspace-dropdown")
    .dropdown({
        action: "nothing",
        onShow: function () {
            // When not mobile layout:
            if (!window.matchMedia("(max-width: 991.98px)").matches) {
                // Fixes Fomantic-UI not adding this class when the username is within a certain length range
                // (seems to happen when the dropdown menu is wider than approx. 150px)
                $(this).find("nav.menu").addClass("left");
            }
        },
    });

$(".lang-link").click(function (event) {
    event.preventDefault();
    $("#lang-form").submit();
});

$("#burger").click(function () {
    $("#header").toggleClass("active");
});
