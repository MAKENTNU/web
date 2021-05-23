$(".skip-to-main-content").click(function (event) {
    event.preventDefault();
    const $mainContent = $("#main");
    $mainContent.attr("tabindex", 0);
    $mainContent.focus();
    $mainContent.removeAttr("tabindex");
});
