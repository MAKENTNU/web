$("#hide-old-reservations").checkbox({
    onChange: function () {
        $("tr, .card").filter(function () {
            return $(this).data("is-future-reservation") === "False";
        }).toggleClass("display-none", $(this).is(":checked"));
    },
});

$(".reservation-calendar-delete, .reservation-mark-done").click(function () {
    $(this).children("form").submit();
});
