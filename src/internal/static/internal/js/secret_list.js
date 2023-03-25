/* These variables must be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var secretsShownSeconds;

const SECRET_ID_DATA_NAME = "secret-id";
const HIDDEN_CLASS_NAME = "display-none";

// This is filled lazily the first time each secret-related button is pressed
const secretDataObjects = {};

function populateSecretDataFor(secretID) {
    const secretData = {
        $secret: $(`#${secretID}`),
        $secretShowButton: $(`.secret-show-button[data-${SECRET_ID_DATA_NAME}="${secretID}"]`),
        timer: null,
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
