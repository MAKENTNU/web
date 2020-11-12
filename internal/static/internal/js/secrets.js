const SECRET_SHOW_DURATION_SECONDS = 10;

$(".secret-button").click(function () {
    const secretButton = $(this);
    const secretId = secretButton.data("secret-id");
    const secret = $(`#${secretId}`);
    secret.removeClass("hidden");
    secretButton.addClass("hidden");
    setTimeout(() => {æ
        secret.addClass("hidden");
        secretButton.removeClass("hidden");
    }, SECRET_SHOW_DURATION_SECONDS * 1000);
});
