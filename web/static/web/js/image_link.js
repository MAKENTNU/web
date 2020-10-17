$(document).ready(function () {
    $("img[href]").click(function (e) {
        e.preventDefault();
        window.location = $(this).attr("href");
    });
});
