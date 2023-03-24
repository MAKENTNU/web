const SECRETS_SHOWN_SECONDS = 10;
const SECRET_ID_DATA_NAME = "secret-id";
const HIDDEN_CLASS_NAME = "display-none";

const secretTimers = {};

$(".secret-show-button").click(function () {
    const $secretShowButton = $(this);
    const secretID = $secretShowButton.data(SECRET_ID_DATA_NAME);
    const $secret = $(`#${secretID}`);
    $secret.removeClass(HIDDEN_CLASS_NAME);
    $secretShowButton.addClass(HIDDEN_CLASS_NAME);
    secretTimers[secretID] = setTimeout(() => {
        hideSecret($secret, $secretShowButton);
    }, SECRETS_SHOWN_SECONDS * 1000);
});

$(".secret-hide-button").click(function () {
    const $secretHideButton = $(this);
    const secretID = $secretHideButton.data(SECRET_ID_DATA_NAME);
    const $secretShowButton = $(`#button-${secretID}`);
    const $secret = $(`#${secretID}`);
    hideSecret($secret, $secretShowButton);
    clearTimeout(secretTimers[secretID]);
});

function hideSecret($secret, $secretShowButton) {
    $secret.addClass(HIDDEN_CLASS_NAME);
    $secretShowButton.removeClass(HIDDEN_CLASS_NAME);
}
