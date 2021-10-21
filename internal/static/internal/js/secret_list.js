const SECRET_SHOW_DURATION_SECONDS = 10;
const SECRET_ID_DATA_NAME = "secret-id";
const HIDDEN_CLASS_NAME = "display-none";

const secretTimers = {};

$(".secret-button").click(function () {
    const secretButton = $(this);
    const secretId = secretButton.data(SECRET_ID_DATA_NAME);
    const secret = $(`#${secretId}`);
    secret.removeClass(HIDDEN_CLASS_NAME);
    secretButton.addClass(HIDDEN_CLASS_NAME);
    secretTimers[secretId] = setTimeout(() => {
        hideButtons(secret, secretButton);
    }, SECRET_SHOW_DURATION_SECONDS * 1000);
});

$(".secret-close-button").click(function () {
    const secretCloseButton = $(this);
    const secretId = secretCloseButton.data(SECRET_ID_DATA_NAME);
    const secretButton = $(`#button-${secretId}`);
    const secret = $(`#${secretId}`);
    hideButtons(secret, secretButton);
    clearTimeout(secretTimers[secretId])
});

function hideButtons(secret, secretButton) {
    secret.addClass(HIDDEN_CLASS_NAME);
    secretButton.removeClass(HIDDEN_CLASS_NAME);
}
