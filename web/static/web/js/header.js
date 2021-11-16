let shouldKeepDropdownOpen = false;

const $headerDropdowns = $("#nav-user-dropdown, #makerspace-dropdown");
$headerDropdowns.focusout(function (e) {
    // Manually makes sure to prevent hiding the dropdowns when navigating with the "tab" key,
    // as there is no setting for doing this otherwise (https://fomantic-ui.com/modules/dropdown.html#/settings).
    const $thisDropdown = $(this);
    const $targetGainingFocus = $(e.relatedTarget);
    if ($thisDropdown.has($targetGainingFocus).length > 0) {
        shouldKeepDropdownOpen = true;
    } else {
        shouldKeepDropdownOpen = false;
        // Hide the dropdown manually, as the event is not fired when one of the dropdown's elements loses focus
        $thisDropdown.dropdown("hide");
    }
});
$headerDropdowns.dropdown({
    selectOnKeydown: false,
    action: function (text, value, $element) {
        $element.click();
    },
    onShow: function () {
        // When not mobile layout:
        if (!window.matchMedia("(max-width: 991.98px)").matches) {
            // Fixes Fomantic-UI not adding this class when the username is within a certain length range
            // (seems to happen when the dropdown menu is wider than approx. 150px)
            $(this).find("nav.menu").addClass("left");
        }
    },
    onHide: function () {
        if (shouldKeepDropdownOpen) {
            return false;
        }
    },
});
// Code based on this workaround: https://github.com/Semantic-Org/Semantic-UI/issues/5531#issuecomment-316422402
$headerDropdowns.find("a.item")
    .focusin(function () {
        $(this).addClass("active selected");
    })
    .focusout(function () {
        $(this).removeClass("active selected");
    });

$(".lang-link").click(function (event) {
    event.preventDefault();
    $("#lang-form").submit();
});

$("#burger").click(function (e) {
    e.preventDefault();
    $("#header").toggleClass("active");
});
