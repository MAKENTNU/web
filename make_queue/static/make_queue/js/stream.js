count = 0;

$('.stream.image').each(function () {
    var chatSocket = new WebSocket(
        'ws://' + window.location.host +
        '/stream/' + $(this).attr("name") + '/');

    chatSocket.onmessage = function (e) {
        console.log('img');
        var data = JSON.parse(e.data);
        var blob = new Blob([data], {type: 'image/jpg'});
        var url = URL.createObjectURL(blob);
        var image = $(this);
        var img = new Image();
        img.onload = function () {
            var ctx = image.getContext("2d");
            ctx.drawImage(img, 0, 0);
        }
        img.src = url;
    };

    chatSocket.onclose = function (e) {
        console.error('Chat socket closed unexpectedly');
    };
});

$('.stream.image').click(function () {
    $(this).toggleClass('fullscreen');
    $('#fader').toggleClass('fullscreen');
    $('#closefullscreen').toggleClass('fullscreen');
});

$('#closefullscreen').click(function () {
    $('.fullscreen').each(function () {
        $(this).removeClass('fullscreen');
    });
});
