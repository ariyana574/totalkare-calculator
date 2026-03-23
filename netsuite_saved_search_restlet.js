/**
 * @NApiVersion 2.1
 * @NScriptType Restlet
 */

define(['N/search'], function (search) {

    function getSavedSearchResults(savedSearchId) {
        var results = [];
        var searchObj = search.load({ id: savedSearchId });

        var pagedData = searchObj.runPaged({ pageSize: 1000 });

        pagedData.pageRanges.forEach(function (pageRange) {
            var page = pagedData.fetch({ index: pageRange.index });
            page.data.forEach(function (result) {
                var row = {};

                result.columns.forEach(function (col) {
                    row[col.label || col.name] = result.getValue(col);
                });

                results.push(row);
            });
        });

        return results;
    }

    return {
        get: function (request) {
            var savedSearchId = request.searchId || 3977; // default to your search
            return getSavedSearchResults(savedSearchId);
        }
    };

});