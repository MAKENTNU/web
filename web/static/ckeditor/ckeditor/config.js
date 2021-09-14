/*
  Note: To make this configuration file apply, the `ckeditor` app must be listed after `web` in `INSTALLED_APPS`.
*/

CKEDITOR.editorConfig = function (config) {
    // Define changes to default configuration here. For example:
    // config.language = 'fr';
    // config.uiColor = '#AADC6E';
};

CKEDITOR.on("dialogDefinition", function (ev) {
    // Set the default link target to "_blank"
    if (ev.data.name === "link") {
        const targetTab = ev.data.definition.getContents("target");
        const targetField = targetTab.get("linkTargetType");
        targetField["default"] = "_blank";
    }
});
