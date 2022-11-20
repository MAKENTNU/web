let popupTimer;

function createPopup($elementToCreateFor, popupHtml) {
    $elementToCreateFor
        .popup({
            html: popupHtml,
            on: "manual",
            exclusive: true,
        })
        .popup("show");
    // Hide popup after 5 seconds
    delayPopup($elementToCreateFor, 5000);
}

function delayPopup($popup, delayMillis) {
    popupTimer = setTimeout(function () {
        $popup.popup("hide");
    }, delayMillis);
}

$(".copy-token").click(function () {
    const $copyButton = $(this);
    clearTimeout(popupTimer);

    const $input = $copyButton.closest(".emails-container").find(".copy-input");
    // Make the text field selected, to communicate to the user what text was copied
    $input.select();
    const emails = $input.val();

    // Copy the text inside the text field
    navigator.clipboard.writeText(emails).then(
        // Clipboard successfully set
        () => {
            createPopup($copyButton, `<div class="ui green header">${gettext("Copied to clipboard!")}</div>`);
        },
        // Clipboard write failed
        () => {
            createPopup($copyButton, `<div class="ui red header">${gettext("Failed to copy to clipboard!")}</div>`);
        },
    );
});
