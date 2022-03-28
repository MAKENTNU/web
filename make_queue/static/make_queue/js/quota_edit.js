const $userInput = $("#user");
const $userField = $userInput.closest(".field");
const $userDropdown = $userInput.closest(".dropdown");

$(".checkbox").checkbox();
$("#id_all").closest(".checkbox.field").checkbox({
    fireOnInit: true,
    onChecked: function () {
        $userField.toggleClass("disabled", true);
        $userDropdown.dropdown("clear");
    },
    onUnchecked: function () {
        $userField.toggleClass("disabled", false);
    },
});
