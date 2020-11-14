let popupTimer;

function delayPopup($popup) {
    popupTimer = setTimeout(function () {
        $popup.popup('hide');
    }, 4200);
}

$(".copy-token").click(function () {
    const $copyButton = $(this);
    clearTimeout(popupTimer);

    const $input = $copyButton.closest("div").find(".copy-input");
    // Select the text field
    $input.select();

    // Copy the text inside the text field
    document.execCommand('copy');

    $copyButton
        .popup({
            title: gettext("Successfully copied to clipboard!"),
            on: 'manual',
            exclusive: true,
        })
        .popup('show');
    // Hide popup after 5 seconds
    delayPopup($copyButton);
});
