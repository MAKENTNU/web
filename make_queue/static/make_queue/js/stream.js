function makeid() {
    var text = "";
    var possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for (var i = 0; i < 5; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

setInterval(function () {
    $('.stream.image').each(function () {
        if (!$(this).attr('nostream')) {
            $(this).attr("src", $(this).attr("url") + "?" + makeid());
        }
    });
}, 1000);

$('.stream.image').click(function() {
    $(this).toggleClass('fullscreen');
    $('#fader').toggleClass('fullscreen');
    $('#closefullscreen').toggleClass('fullscreen');
});

$('#closefullscreen').click(function () {
    $('.fullscreen').each(function () {
       $(this).removeClass('fullscreen');
    });
});
