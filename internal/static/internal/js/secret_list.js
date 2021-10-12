const SECRET_SHOW_DURATION_SECONDS = 10;

let timer;

$(".secret-button").click(function () {
    const secretButton = $(this);
    const secretId = secretButton.data("secret-id");
    const secret = $(`#${secretId}`);
    secret.removeClass("display-none");
    secretButton.addClass("display-none");
    timer = setTimeout(() => {
        hideButtons(secret, secretButton);
    }, SECRET_SHOW_DURATION_SECONDS * 1000);
});

$(".secret-close-button").click(function () {
    const secretCloseButton = $(this);
    const secretId = secretCloseButton.data("secret-id");
    const secretButton = $(`#${"button-"+secretId}`);
    const secret = $(`#${secretId}`);
    hideButtons(secret, secretButton);
    clearTimeout(timer)
});

function hideButtons(secret, secretButton) {
    secret.addClass("display-none");
    secretButton.removeClass("display-none");
}
