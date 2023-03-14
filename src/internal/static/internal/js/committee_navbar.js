// Code based on https://fomantic-ui.com/javascript/menu.js
$(".committee-navbar .item").click(function () {
    const $this = $(this);
    $this.addClass("active");
    $this.closest(".ui.menu").find(".item").not($this).removeClass("active");
});
