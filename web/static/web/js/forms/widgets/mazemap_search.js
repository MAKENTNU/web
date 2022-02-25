function removeTagsAndSanitize(str) {
    return str.replaceAll(/<[^>]*>/g, "")
        .replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

jQuery.fn.extend({
    mazeMapSearch: function () {
        // Data attributes set by the widget
        const campusID = this.data("campus-id");
        const maxResults = this.data("max-results");
        const urlField = this.data("url-field");

        this.parent().search({
            searchDelay: 0,
            fullTextSearch: true,
            apiSettings: {
                // Search for POIs (Points Of Interest) at the given campus
                url: `https://api.mazemap.com/search/equery/?q={query}`
                    + `&withpois=true&withbuilding=false&withtype=false&withcampus=false`
                    + `&rows=${maxResults}&campusid=${campusID}`,

                // Convert MazeMap search results to fit Fomantic-UI search format
                onResponse: mazeMapResponse => ({
                    results: mazeMapResponse.result.map(item => {
                        const buildingName = item.dispBldNames[0];
                        const roomName = item.dispPoiNames[0];
                        const roomID = item.dispPoiNames[1];
                        return {
                            title: removeTagsAndSanitize(
                                roomName + (buildingName ? `, ${buildingName}` : ""),
                            ),
                            description: roomID ? removeTagsAndSanitize(roomID) : "",
                            id: item.poiId,
                        };
                    }),
                }),
            },
            templates: {
                // Template for error messages.
                // This copies the default one provided by Fomantic-UI, but adds translations.
                message: (type, message) => (`
                    <div class="message empty">
                        <div class="header">
                            ${gettext("No Results")}
                        </div>
                        <div class="description">
                            ${gettext("Your search returned no results")}
                        </div>
                    </div>
                `),
            },
            // Autofill of MazeMap-URL if `urlField` is given
            onSelect: function (result, response) {
                if (!urlField)
                    return;

                $(`input[name=${urlField}]`).val(
                    `https://use.mazemap.com/?campusid=${campusID}&desttype=poi&dest=${result.id}`,
                );
            },
        });
    },
});
