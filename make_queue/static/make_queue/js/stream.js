const STREAM_INIT_TIMEOUT_SECONDS = 10;

function getStreamName($streamImage) {
    return $streamImage.data("stream-name");
}

function initStream($streamImage) {
    const streamName = getStreamName($streamImage);
    const newImage = new Image();

    const timeoutID = setTimeout(function () {
        console.error(`Unable to load stream for '${streamName}' after ${STREAM_INIT_TIMEOUT_SECONDS} seconds (${newImage.src})`);
        // Remove the `onload` event handler and cancel image loading
        newImage.onload = undefined;
        newImage.src = "";
    }, STREAM_INIT_TIMEOUT_SECONDS * 1000);

    newImage.onload = function (event) {
        clearTimeout(timeoutID);
        $streamImage.attr("src", newImage.src);
    };
    newImage.onerror = function (event) {
        clearTimeout(timeoutID);
    };
    newImage.src = `/reservation/machines/${streamName}/stream/`; // URL defined in the server's Nginx config
}

$(".stream.image").each(function () {
    initStream($(this));
}).click(function () {
    $(this).toggleClass("fullscreen");
    $("#fader, #close-fullscreen-button").toggleClass("fullscreen");
});

function closeFullscreen() {
    $(".fullscreen").each(function () {
        $(this).removeClass("fullscreen");
    });
}

$("html").keydown(function (event) {
    if (event.key === "Escape")
        closeFullscreen();
});

$("#close-fullscreen-button").click(closeFullscreen);
