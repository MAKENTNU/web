/* `connectStreamsOutsideViewport` can optionally be defined when linking this script */
// noinspection ES6ConvertVarToLetConst
var connectStreamsOutsideViewport;

const STREAM_INIT_TIMEOUT_SECONDS = 10;
const streamNameToData = {};
const streamNameToOriginalImg = {};

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

    return {newImage, timeoutID};
}

function uninitStream($streamImage) {
    const streamName = getStreamName($streamImage);
    const streamData = streamNameToData[streamName];
    // Stream hasn't been initialized for this element yet (usually happens on page load)
    if (!streamData)
        return;

    const {newImage, timeoutID} = streamData;
    clearTimeout(timeoutID);
    newImage.onload = undefined;
    newImage.onerror = undefined;
    newImage.src = "";
    $streamImage.attr("src", streamNameToOriginalImg[streamName]);
}

// Code based on https://stackoverflow.com/a/45618188
const observer = new IntersectionObserver(
    function (entries, opts) {
        entries.forEach(function (entry) {
            const $streamImage = $(entry.target);
            // Only connect (and stay connected) to streams while they're visible
            if (entry.isIntersecting) {
                const streamData = initStream($streamImage);
                streamNameToData[getStreamName($streamImage)] = streamData;
            } else
                uninitStream($streamImage);
        });
    }, {
        root: null, // makes it observe intersections between the viewport and the observed elements
        threshold: 0, // triggers the callback above just as the observed element comes into / out of view
    },
);

$(".stream.image").each(function () {
    const $streamImage = $(this);
    const streamName = getStreamName($streamImage);
    streamNameToOriginalImg[streamName] = $streamImage.attr("src");

    if (connectStreamsOutsideViewport)
        initStream($streamImage);
    else
        observer.observe(this);
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
