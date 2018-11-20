$(function () {
    $('.burger').click(function () {
        $('#header').toggleClass('active');
    });
    $('.logo').click(function () {
        window.location.href = '/';
    });
});
