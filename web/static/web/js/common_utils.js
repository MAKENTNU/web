$(".message .close").click(function () {
    $(this)
        .closest(".message")
        .fadeOut();
});

$("span[data-content], .explanation-popup").popup();
