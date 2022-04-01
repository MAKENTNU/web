/*
  Note: To make this configuration file apply, the `ckeditor` app must be listed after `web` in `INSTALLED_APPS`.
*/
// `CKEDITOR_CONFIG_FROM_DJANGO` is defined in `config_from_django.js`
var CKEDITOR_CONFIG_FROM_DJANGO = (typeof CKEDITOR_CONFIG_FROM_DJANGO !== "undefined") ? CKEDITOR_CONFIG_FROM_DJANGO : {};

const customStylesName = "my_styles";
CKEDITOR.stylesSet.add(customStylesName, [
    {name: gettext("Big"), element: "big"},
    {name: gettext("Small"), element: "small"},
    {name: gettext("Code"), element: "code"},
    {name: gettext("Quotation"), element: "q"},
]);

CKEDITOR.editorConfig = function (config) {
    // Define changes to default configuration here. For example:
    // config.language = 'fr';
    // config.uiColor = '#AADC6E';
    config.format_tags = "p;h1;h2;h3;h4;h5;h6;pre";
    config.stylesSet = customStylesName;

    if (CKEDITOR_CONFIG_FROM_DJANGO.shouldAllowAllTags) {
        // Code based on https://stackoverflow.com/a/24575744
        // (This doesn't strictly speaking allow *all* tags, but the ones deemed necessary for most cases)
        config.allowedContent = {
            script: true,
            div: true,
            $1: {
                // This will set the default set of elements
                elements: CKEDITOR.dtd,
                attributes: true,
                styles: true,
                classes: true,
            },
        };
    }
};

// Set the default link target to "_blank"
CKEDITOR.on("dialogDefinition", function (evt) {
    const dialogName = evt.data.name;
    if (dialogName === "link") {
        const dialogDefinition = evt.data.definition;
        const targetTab = dialogDefinition.getContents("target");
        const targetField = targetTab.get("linkTargetType");
        targetField["default"] = "_blank";
    }
});

// Set the link target based on whether the link type is `anchor` or not
for (const [_name, instance] of Object.entries(CKEDITOR.instances)) {
    instance.on("dialogShow", function (evt) {
        const dialog = evt.data;
        // Code based on https://stackoverflow.com/a/7040445
        dialog._.contents.info.linkType.on("change", function (evt) {
            // `anchor` links (<a> tags with an `href` that starts with `#` followed by the ID of an HTML element)
            // should not have `target="_blank"`
            const linkTarget = (this.getValue() === "anchor") ? "notSet" : "_blank";
            dialog.setValueOf("target", "linkTargetType", linkTarget);
        });
    });
}
