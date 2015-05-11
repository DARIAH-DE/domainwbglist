jQuery(document).ready(function($) {
    jQuery('a.btnCheck').on('click', function(){
        newwindow=window.open($(this).attr('href'),'','height=700,width=900,scrollbars=yes,resizable=yes,location=yes,status=yes,toolbar=yes');
        if (window.focus) {newwindow.focus()}
        $('#btnWhiteList').prop('disabled', false);
        $('#btnGrayList').prop('disabled', false);
        $('#btnBlackList').prop('disabled', false);
        return false;
    });
    $('#pruefModal').on('shown.bs.modal', function () {
        $('#pruefModalDecideBtn').prop('disabled', true);
        $('#pruefModalAlert').toggleClass('alert', false);
        $('#pruefModalAlert').toggleClass('alert-success', false);
        $('#pruefModalAlert').toggleClass('alert-danger', false);
        $('#pruefModalAlert').toggleClass('alert-warning', false);
        $('#pruefModalDecideBtn').text('Decide');
        var input = $('#InputEmail').val();
        var domain = '';
        var result = '';
        var atsymb = input.indexOf("@");
        if (input == '') { result = 'Keine Eingabe.'}
        else { 
          if (atsymb < 0) { result = 'Kein @ enthalten.'}
          else {
            domain = input.substring(atsymb);
            $('#pruefModalDecideBtn').prop('disabled', false);
            $('#pruefModalForm').attr('action', '/decide/'+domain);

            $('#pruefModalAlert').toggleClass('alert', true);
            $('#pruefModalAlert').toggleClass('alert-success', false);
            $('#pruefModalAlert').toggleClass('alert-danger', false);
            $('#pruefModalAlert').toggleClass('alert-warning', true);
            result = 'Domain ' + domain + ' unbekannt!';
            if (whitelist.indexOf(domain) > -1) {
              $('#pruefModalAlert').toggleClass('alert', true);
              $('#pruefModalAlert').toggleClass('alert-success', true);
              $('#pruefModalAlert').toggleClass('alert-danger', false);
              $('#pruefModalAlert').toggleClass('alert-warning', false);
              $('#pruefModalDecideBtn').text('Ändern');
              result = 'Domain ' + domain + ' ist auf Whitelist!';
            }
            if (graylist.indexOf(domain) > -1) {
              $('#pruefModalAlert').toggleClass('alert', true);
              $('#pruefModalAlert').toggleClass('alert-success', false);
              $('#pruefModalAlert').toggleClass('alert-danger', false);
              $('#pruefModalAlert').toggleClass('alert-warning', true);
              $('#pruefModalDecideBtn').text('Ändern');
              result = 'Domain ' + domain + ' ist auf Graylist!';
            }
            if (blacklist.indexOf(domain) > -1) {
              $('#pruefModalAlert').toggleClass('alert', true);
              $('#pruefModalAlert').toggleClass('alert-success', false);
              $('#pruefModalAlert').toggleClass('alert-danger', true);
              $('#pruefModalAlert').toggleClass('alert-warning', false);
              $('#pruefModalDecideBtn').text('Ändern');
              result = 'Domain ' + domain + ' ist auf Blacklist!';
            }
          }
        }
        $('#pruefModalAlert').text(result);
      // do something...
    });
});

