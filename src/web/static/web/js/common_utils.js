const DisplayState = Object.freeze({
    SHOWN: Symbol("shown"),
    HIDDEN: Symbol("hidden"),
});

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
