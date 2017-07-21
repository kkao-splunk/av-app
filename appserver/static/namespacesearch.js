require([
    "splunkjs/mvc",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/searchbarview",
    "splunkjs/mvc/searchcontrolsview",
    "splunkjs/mvc/tableview",
    "splunkjs/mvc/singleview",
    "splunkjs/mvc/simplexml/ready!",
    "jquery",
    "splunk.util"
], function(
    mvc,
    SearchManager,
    SearchbarView,
    SearchControlsView,
    TableView,
    SingleView,
    ready,
    jquery,
    splunkutil
) {

  var load =  function() {
    var PROVIDER = 'aws'
    var REGION = 'us-west-1'

    //getting auth token here
    var tokens = mvc.Components.get("default");
    var service = mvc.createService({ owner: "nobody" });
    /*
    tokens.on('change',function(var1) {
      console.log(var1.attributes.cluster_tok);
    });
    */
    var request = service.request("storage/collections/data/token/",
                   "GET",
                   null,
                   null,
                   null,
                      {"Content-Type": "application/json"},
                   null);
    var access_token = localStorage.getItem("id_token");
    request
      .done(function(response) {
        access_token = response.accessId
      })
      .fail(function() {
        console.log('Something went wrong');
      });

    //forming request to get namespaces from Avanti Endpoint
    var cluster_tok = tokens.get("cluster_tok");
    var request = "http://127.0.0.1:8080" + "/avanti/v0.3/ListNamespaces?provider=" + PROVIDER
    request = request + "&region=" + REGION + "&cluster=" + cluster_tok + "&access_token=" + access_token

    service.del("storage/collections/data/cluster/");
    var get = service.get("storage/collections/data/cluster/");
    var finish = get.done(function(answer) {
        var record = {
                'cluster' : cluster_tok
               }
        service.request(
               "storage/collections/data/cluster/",
                "POST",
                null,
                null,
                JSON.stringify(record),
              {"Content-Type": "application/json"},
              null);
    });

    finish
    .done(function(answer) {
    var service = mvc.createService();
    var req = service.request(path = '/namespace_endpoint');

    req
    .done(function(response) {
      var i = 0
      var namespace_subnet = []
      var response_parsed = JSON.parse(response);
      /*
      if success, print out the names of the name spaces
      *note: This data DOES NOT go into splunk; rather it becomes a token that's passed around
      */

      try {
      while (i < response_parsed.assets.length) {
        namespace_subnet.push(" " + response_parsed.assets[i].name + ": " + response_parsed.assets[i].subnet + " ");
        i += 1;
      }
      document.getElementById('placeholder').innerHTML = "Namespace Subnets: " + namespace_subnet;
      document.getElementById('placeholder').style.fontSize = 'large';

      tokens.set("namespace_tok",namespace_subnet);
    }

      catch (e) {
        console.log(e);
        //If this is the response message, means token is expired
        if (response_parsed.message == 'square/go-jose/jwt: validation failed, token is expired (exp)') {
          console.log('expired token');
          document.getElementById('placeholder').innerHTML = "Your token has expired - Please log in again";
          return;
        }
        //length is 0, which means that there are no subnets on the cluster
        document.getElementById('placeholder').innerHTML = "There are no subnets";
        return;
      }
      });
    })
    //general catch for errors
    .fail(function(response) {
      alert("Something went wrong - please try again");
    })
  }

  var currentPage = window.location.href;
  load();
  setInterval(function()
  {
      if (currentPage != window.location.href)
      {
        currentPage = window.location.href;
            load();
        }
}, 500);



});
