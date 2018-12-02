$('.ui.search')
    .search({
        apiSettings: {
            onResponse: function (mazemap_response) {
                let response = {results: []};
                $.each(mazemap_response.result, function (index, item) {
                    response.results.push({
                        title: (
                            item.dispPoiNames[0] +
                            (item.dispBldNames[0] ? ", " + item.dispBldNames[0] : "")
                        ).replace(/<[/]?em>/g, ""),
                        description: (item.dispPoiNames[1] ? item.dispPoiNames[1] : "").replace(/<[/]?em>/g, ""),
                        id: item.poiId,
                    });
                });
                return response;
            },
            url: 'https://api.mazemap.com/search/equery/?q={query}&rows=5&withpois=true&withbuilding=false&withtype=false&withcampus=false&campusid=1',
        },
        onSelect: function (result, response) {
            $("input[name=place_url").val(
                `https://use.mazemap.com/?campusid=1&desttype=poi&dest=${result.id}`
            );
        },
        searchDelay: 0,
        fullTextSearch: true,
    })
;
