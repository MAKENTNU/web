function setupSocket($elem) {
    const chatSocket = new WebSocket(
        `wss://${window.location.host}/ws/stream/${$elem.data("stream-name")}/`,
    );

    chatSocket.image = $elem;

    chatSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        chatSocket.image.attr("src", `data:image/jpeg;base64,${data["image"]}`);
    };

    chatSocket.onclose = async function () {
        console.error("Socket closed unexpectedly. Restarting");
        // `sleep` is defined in `common_utils.js`
        await sleep(1000);
        setupSocket($elem);
    };
}

$(".stream.image").each(function () {
    setupSocket($(this));
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
