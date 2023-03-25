/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var secretsShownSeconds;
// noinspection ES6ConvertVarToLetConst
var secretsShownDelayedSeconds;

const DISABLE_SECRET_DELAY_HIDING_BUTTON_SECONDS = secretsShownDelayedSeconds - secretsShownSeconds;
const SECRET_ID_DATA_NAME = "secret-id";
const HIDDEN_CLASS_NAME = "display-none";
const DISABLED_CLASS_NAME = "disabled";

// This is filled lazily the first time each secret-related button is pressed
const secretDataObjects = {};

function populateSecretDataFor(secretID) {
    const secretData = {
        $secret: $(`#${secretID}`),
        $secretShowButton: $(`.secret-show-button[data-${SECRET_ID_DATA_NAME}="${secretID}"]`),
        $secretDelayHidingButton: $(`.secret-delay-hiding-button[data-${SECRET_ID_DATA_NAME}="${secretID}"]`),
        timer: null,
        delayHidingButtonTimer: null,
    };
    secretDataObjects[secretID] = secretData;
    return secretData;
}

function getSecretData($elementWithSecretID) {
    const secretID = $elementWithSecretID.data(SECRET_ID_DATA_NAME);
    let secretData = secretDataObjects[secretID];
    if (!secretData)
        secretData = populateSecretDataFor(secretID);

    return secretData;
}

function hideSecret(secretData) {
    secretData.$secret.addClass(HIDDEN_CLASS_NAME);
    secretData.$secretShowButton.removeClass(HIDDEN_CLASS_NAME);
    // Also reset the potentially disabled delay button
    clearTimeout(secretData.delayHidingButtonTimer);
    enableSecretDelayHidingButton(secretData);
}

function enableSecretDelayHidingButton(secretData) {
    secretData.$secretDelayHidingButton.removeClass(DISABLED_CLASS_NAME);
}

function setHideTimeout(inNumSeconds, secretData) {
    secretData.timer = setTimeout(() => {
        hideSecret(secretData);
    }, inNumSeconds * 1000);
}

$(".secret-show-button").click(function () {
    const secretData = getSecretData($(this));
    secretData.$secret.removeClass(HIDDEN_CLASS_NAME);
    secretData.$secretShowButton.addClass(HIDDEN_CLASS_NAME);
    setHideTimeout(secretsShownSeconds, secretData);
});

$(".secret-hide-button").click(function () {
    const secretData = getSecretData($(this));
    hideSecret(secretData);
    clearTimeout(secretData.timer);
});

$(".secret-delay-hiding-button").click(function () {
    const secretData = getSecretData($(this));
    // Delay hiding
    clearTimeout(secretData.timer);
    setHideTimeout(secretsShownDelayedSeconds, secretData);
    // Disable button until the standard hide duration remains (see the declaration of `DISABLE_SECRET_DELAY_HIDING_BUTTON_SECONDS`)
    secretData.$secretDelayHidingButton.addClass(DISABLED_CLASS_NAME);
    secretData.delayHidingButtonTimer = setTimeout(() => {
        enableSecretDelayHidingButton(secretData);
    }, DISABLE_SECRET_DELAY_HIDING_BUTTON_SECONDS * 1000);
});
