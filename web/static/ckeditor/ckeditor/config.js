/*
  Note: To make this configuration file apply, the `ckeditor` app must be listed after `web` in `INSTALLED_APPS`.
*/

CKEDITOR.editorConfig = function (config) {
    // Define changes to default configuration here. For example:
    // config.language = 'fr';
    // config.uiColor = '#AADC6E';

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
