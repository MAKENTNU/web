$("#hide_old_reservations").checkbox({
    onChange: function () {
        $("tr, .card").filter(function () {
            return $(this).data("is-future-reservation") === "False";
        }).toggleClass("make_hidden", $(this).is(":checked"));
    },
});

$(".reservation_calendar_delete, .reservation_mark_done").click(function () {
    $(this).children("form").submit();
});
