function setupSocket($elem) {
    let chatSocket = new WebSocket(
        'wss://' + window.location.host +
        '/ws/stream/' + $elem.attr("name").replace(/ /g, "-").replace(/ö/g, "o") + '/');

    chatSocket.image = $elem;

    chatSocket.onmessage = function (e) {
        let data = JSON.parse(e.data);
        chatSocket.image.attr('src', 'data:image/jpeg;base64,' + data['image']);
    };

    chatSocket.onclose = function (e) {
        console.error('Socket closed unexpectedly. Restarting');
        setupSocket($elem);
    };
}

$('#' + streamID).each(function () {
    setupSocket($(this));
}).click(function () {
    $(this).toggleClass('fullscreen');
    $('#fader').toggleClass('fullscreen');
    $('#closefullscreen').toggleClass('fullscreen');
});

$("html").keydown(function (event) {
    if (event.key === "Escape") {
        closeFullscreen();
    }
});

let closeFullscreen = function () {
    $('.fullscreen').each(function () {
        $(this).removeClass('fullscreen');
    });
};

$('#closefullscreen').click(closeFullscreen);
