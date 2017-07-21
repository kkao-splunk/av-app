require([
    "splunkjs/mvc",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/dropdownview",
    "splunkjs/mvc/tableview",
    "splunkjs/mvc/textinputview",
    "splunkjs/mvc/simplexml/ready!"
], function(
    mvc,
    SearchManager,
    DropdownView,
    TableView,
    TextInputView
) {


    var tokens = mvc.Components.get("default");
    var service = mvc.createService({ owner: "nobody" });
    var request = service.request("storage/collections/data/namespace/",
                   "GET",
                   null,
                   null,
                   null,
                      {"Content-Type": "application/json"},
                   null);
    var req = service.request(path = '/namespace_endpoint');

    req.done(function(response) {
    // Search query is based on the selected index
    var indexsearch = new SearchManager({
        id: "indexsearch",
        cache: true,
        search: mvc.tokenSafe("$searchQuery$")
    });
    var response_parsed = JSON.parse(response);
    var jsonObj = []
    var i = 0;
    while (i < response_parsed.assets.length) {
      item = {}
      item['label'] = response_parsed.assets[i].name;
      item['value'] = response_parsed.assets[i].name;
      jsonObj.push(item);
      i += 1;
    }

    var indexlist = new DropdownView({
        id:"indexlist",
        choices: jsonObj,
        showClearButton: false,
        value: mvc.tokenSafe("$indexName$"),
        el: $("#indexlist")
    }).render();

    // When the $indexName$ token changes, form the search query
    var defaultTokenModel = mvc.Components.get("default");
    defaultTokenModel.on("change:indexName", function(formQuery, indexName) {
        var newQuery = " | stats count by sourcetype, index";
        if (indexName == "all") {
            newQuery = "index=_internal OR index=_audit OR index=main" + newQuery;
        } else {
            newQuery = "index=" + indexName + newQuery;
            request.done(function(response) {
              console.log(response);
              console.log(indexName);
            })
        }

        // Update the $searchQuery$ token value
        defaultTokenModel.set('searchQuery', newQuery);
    });

    // Display the search results
    var textinput1 = new TextInputView({
        id: "textinput1",
        value: mvc.tokenSafe("$searchQuery$"),
        el: $("#text1")
    }).render();


    var tableindex = new TableView({
        id: "tableindex",
        managerid: "indexsearch",
        pageSize: 5,
        el: $("#tableindex")
    }).render();
      });
});
