$("#hide_old_reservations").checkbox({
    onChange: function () {
        $("tr").filter(function () {
            console.log();
            return $(this).data("is-future-reservation") === "False";
        }).toggleClass("make_hidden", $(this).is(":checked"))
    }
});

$(".reservation_calendar_delete").click(function () {
    $(this).children("form").submit();
});
