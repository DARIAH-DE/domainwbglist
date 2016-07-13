
$.mockjaxSettings.logging = 1

$.mockjax({
  url: "api/list/white",
  responseText: ["white","domain"]
});

$.mockjax({
  url: "api/list/grey",
  responseText: []
});

$.mockjax({
  url: "api/list/black",
  responseText: ["black","list"]
});

QUnit.test("load whitelist", function( assert ) {
  $("body").append('<div id="qunit-fixture"><span id="whitenumber"></span></div>');
  var done = assert.async();
  ajaxresponse = loadlist('white').then(function (){
    var number = document.getElementById("whitenumber").textContent;
    assert.equal(number, 2, "Passed!" );
    done();
  });
});

