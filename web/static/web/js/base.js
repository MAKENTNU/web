$(".skip-to-main-content").click(function (e) {
    e.preventDefault();
    const $mainContent = $("#main");
    $mainContent.attr("tabindex", 0);
    $mainContent.focus();
    $mainContent.removeAttr("tabindex");
});
