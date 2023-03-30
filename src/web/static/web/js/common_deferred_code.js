$(".message .close").click(function () {
    $(this)
        .closest(".message")
        .fadeOut();
});

$(".popup-trigger").popup({
    hoverable: true,
    closable: false,
});

// Only forms that have not opted out (using the `dont-prevent-leaving` class),
// and that have a `method` attribute that is not `GET` (case-insensitive) - as those forms shouldn't contain data that is saved in the backend
const $DIRTY_FORMS = $("form:not(.dont-prevent-leaving)[method]:not([method=GET])");
$DIRTY_FORMS.dirty({
    preventLeaving: true,
});
