jQuery(document).ready(function($) {
  queryDomain = $('#decideUrl').text();
  $('#btnWhiteList').prop('disabled', true);
  $.ajax({
    dataType: 'json',
    url: '/api',
    type: 'GET',
    data: 'edugain='+queryDomain,
    success: function(data) { 
      if (data.edugain || data.federation) {
        $('#checkEduresultAlert').toggleClass('alert-success', true);
        $('#checkEduresultAlert').html('<b>Domain '+queryDomain+' hat den eduGain-Test bestanden!</b>');
        $('#btnWhiteList').prop('disabled', false);
      } else {
        $('#checkEduresultAlert').html('Domain '+queryDomain+' hat den eduGain-Test <b>nicht</b> bestanden!');
      }
    }
  });
});

