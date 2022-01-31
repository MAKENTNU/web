/*
  Note: To make this configuration file apply, the `ckeditor` app must be listed after `web` in `INSTALLED_APPS`.
*/

CKEDITOR.editorConfig = function (config) {
    // Define changes to default configuration here. For example:
    // config.language = 'fr';
    // config.uiColor = '#AADC6E';
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
