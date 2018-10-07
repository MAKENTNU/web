$('.stream.image').each(function () {
    var chatSocket = new WebSocket(
        'wss://' + window.location.host +
        '/ws/stream/' + $(this).attr("name") + '/');

    chatSocket.image = $(this);

    chatSocket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        chatSocket.image.attr('src', 'data:image/jpeg;base64,' + data['image']);
    };

    chatSocket.onclose = function (e) {
        console.error('Socket closed unexpectedly');
    };
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
