function isFilled(element, value) {
    /**
     * Checks if the given element has content or not.
     *
     * @value Used to explicitly pass the value of the element, e.g. in the case of CKEditor
     */
    if (value !== undefined) {
        return value !== "";
    }
    return $(element).val() !== "";
}

function checkFilled(element, value) {
    /**
     * Checks if the given element has content or not. If there is no content (and value is empty), the
     * menu element connected to the current tab is tagged as not filled.
     *
     * @value Used to explicitly pass the value of the element, e.g. in the case of CKEditor
     */
    const tabValue = $(element).closest(".ui.tab").data("tab");
    $(`.menu > .item[data-tab="${tabValue}"]`).toggleClass("language-not-filled", !isFilled(element, value));
}

$(".multilingual-input").each(function () {
    const $widget = $(this);
    const $widgetField = $widget.closest(".field");
    const $widgetForm = $widgetField.closest("form");
    const widgetRequired = Boolean($widget.attr("required"));
    // If there were a CSS predecessor element selector (there will be one in CSS4), this could have been solved with pure CSS
    const $widgetLabel = $widget.prev("label");
    $widgetLabel.toggleClass("multilingual-label", true);

    $widget.find(".menu .item").tab({
        onVisible: function (tabPath) {
            // Set the label's `for` attribute to the ID of the text input that has been made visible
            const $activeSubwidgetTab = $widget.find(`.tab[data-tab="${tabPath}"]`);
            const subwidgetInputID = $activeSubwidgetTab.find("input, textarea").attr("id");
            $widgetLabel.attr("for", subwidgetInputID);
        },
    });

    const $tabs = $widget.find(".ui.tab");

    $tabs.find(".django-ckeditor-widget").each(function () {
        // CKEditor is set up first after the DOM has loaded
        $(document).ready(function () {
            $(this).find("textarea").each(function () {
                CKEDITOR.instances[this.id].on("change", function () {
                    if (widgetRequired)
                        checkFilled(this.element.$, this.getData());

                    // `$DIRTY_FORMS` is defined in `common_deferred_code.js`
                    if ($widgetForm.is($DIRTY_FORMS)) {
                        // Prevent leaving the page after having edited the CKEditor widget at least once
                        $widgetForm.dirty("setAsDirty");
                    }
                });
            });
        }.bind(this));
    });

    if (widgetRequired) {
        $tabs.find("input, textarea").each(function () {
            checkFilled(this);
            $(this).keyup(function () {
                checkFilled(this);
            }.bind(this));
        });

        // Shouldn't use the `submit` event on the form, as that seems to mess with `jquery.dirty.js`,
        // causing it to not prevent leaving after the event function below has run once
        $widgetForm.find("input[type=submit]").click(function (event) {
            // `checkFilled()` sets the `language-not-filled` class
            const $languagesNotFilled = $widget.find(".menu .item.language-not-filled");

            // Remove old error messages; we will create new ones if there are still errors
            $widgetField.find(".error-message").remove();
            if ($languagesNotFilled.length > 0) {
                $widgetField.toggleClass("error", true);
                // Change to the first non-filled tab
                const $firstLanguageNotFilled = $languagesNotFilled.first();
                $firstLanguageNotFilled.tab("change tab", $firstLanguageNotFilled.data("tab"));

                // Add an error message label
                const $languageMissingTextIndicator = $(`
                    <div class="error-message ui label"
                         style="display: block; width: fit-content; width: -moz-fit-content; margin-left: auto;">
                `);
                $languageMissingTextIndicator.text(interpolate(
                    ngettext(
                        "The field is missing a value for %(num)s language",
                        "The field is missing a value for %(num)s languages",
                        $languagesNotFilled.length,
                    ),
                    {num: $languagesNotFilled.length}, true,
                ));
                $widgetField.prepend($languageMissingTextIndicator);
                $languageMissingTextIndicator[0].scrollIntoView();

                // Prevent the form from submitting while there are errors
                event.preventDefault();
            } else {
                $widgetField.toggleClass("error", false);
            }
        });
    }
});
