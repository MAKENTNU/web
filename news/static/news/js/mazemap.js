$('.ui.search')
    .search({
        apiSettings: {
            onResponse: function (mazemap_response) {
                let response = {results: []};
                $.each(mazemap_response.result, function (index, item) {
                    response.results.push({
                        title: item.poiNames[1] + " (" + item.poiNames[0] + ")",
                        description: item.dispBldNames + " " + item.zName,
                        id: item.poiId,
                    });
                });
                return response;
            },
            url: 'https://api.mazemap.com/search/equery/?q={query}&rows=5&start=0&withpois=true&withbuilding=false&withtype=false&withcampus=false&campusid=1',
        },
        onSelect: function (result, response) {
            $("input[name=place_url").val(
                `https://use.mazemap.com/?campusid=1&desttype=poi&dest=${result.id}`
            );
        },
    })
;
