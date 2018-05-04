$(function () {
    $('.burger').click(function () {
        $('.nav').toggleClass('active');
    });
    $('.logo').click(function () {
        window.location.href = '/';
    });
});