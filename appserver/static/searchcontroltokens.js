require([
    "jquery",
    "splunkjs/mvc/dropdownview",
    "splunkjs/mvc",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/searchbarview",
    "splunkjs/mvc/searchcontrolsview",
    "splunkjs/mvc/tableview",
    "splunkjs/mvc/simplexml/ready!",

], function(
    jquery,
    DropDownView,
    mvc,
    SearchManager,
    SearchbarView,
    SearchControlsView,
    TableView
) {
    // Create the search manager and views
    var mysearch = new SearchManager({
        id: "search1",
        search: mvc.tokenSafe("$searchquery$"),
        earliest_time: mvc.tokenSafe("$earlyval$"),
        latest_time: mvc.tokenSafe("$lateval$"),
        app: "search",
        preview: true,
        required_field_list: "*",
        status_buckets: 300
    });

    var mysearchbar = new SearchbarView({
        id: "searchbar1",
        managerid: "search1",
        value: mvc.tokenSafe("$searchquery$"),
        timerange_earliest_time: mvc.tokenSafe("$earlyval$"),
        timerange_latest_time: mvc.tokenSafe("$lateval$"),
        default: "index = avanti | rename name AS cluster | stats first(createdAt) AS createdAt, first(status) AS status, first(lastUpdatedAt) AS lastUpdatedAt, first(region.name) AS regionName, first(provider.name) AS provider BY cluster| table cluster provider createdAt lastUpdatedAt regionName status",
        el: $("#mysearchbar1")
    }).render();

    var mysearchcontrols = new SearchControlsView({
        id: "searchcontrols1",
        managerid: "search1",
        el: $("#mysearchcontrols1")
    }).render();

    var mytable = new TableView({
        id: "table1",
        managerid: "search1",
        el: $("#mytable1")
    }).render();
});
