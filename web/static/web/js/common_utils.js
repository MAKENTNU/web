function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

$(".message .close").click(function () {
    $(this)
        .closest(".message")
        .fadeOut();
});

$("span[data-content], .explanation-popup").popup();

// Only forms that have not opted out (using the `dont-prevent-leaving` class),
// and that have a `method` attribute that is not `GET` (case-insensitive) - as those forms shouldn't contain data that is saved in the backend
$("form:not(.dont-prevent-leaving)[method]:not([method=GET])").dirty({
    preventLeaving: true,
});
