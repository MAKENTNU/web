$(document).ready(function() {
    $("aimg[href], img[href]").click(function(e) {
	e.preventDefault();
	window.location = $(this).attr("href");
    });
});
