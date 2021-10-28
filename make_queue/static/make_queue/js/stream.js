function setupSocket($elem) {
    const chatSocket = new WebSocket(
        `wss://${window.location.host}/ws/stream/${$elem.data("stream-name")}/`,
    );

    chatSocket.image = $elem;

    chatSocket.onmessage = function (e) {
        const data = JSON.parse(e.data);
        chatSocket.image.attr("src", `data:image/jpeg;base64,${data["image"]}`);
    };

    chatSocket.onclose = function (e) {
        console.error("Socket closed unexpectedly. Restarting");
        setupSocket($elem);
    };
}

$(".stream.image").each(function () {
    setupSocket($(this));
}).click(function () {
    $(this).toggleClass("fullscreen");
    $("#fader").toggleClass("fullscreen");
    $("#closefullscreen").toggleClass("fullscreen");
});

// The following code is scoped within a block, to avoid variable name collisions when linking this script multiple times
{
    function closeFullscreen() {
        $(".fullscreen").each(function () {
            $(this).removeClass("fullscreen");
        });
    }

    $("html").keydown(function (event) {
        if (event.key === "Escape") {
            closeFullscreen();
        }
    });

    $("#closefullscreen").click(closeFullscreen);
}
