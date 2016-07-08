/*
 * Copyright 2016 SUB Goettingen
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

jQuery(document).ready(function($) {

  for (var currlist of ['white','black','grey']) {
    loadlist(currlist);
  };

  $('#manualcheckbutton').on('click', function(){
    var newwindow = window.open($(this).attr('href'),'','height=700,width=900,scrollbars=yes,resizable=yes,location=yes,status=yes,toolbar=yes');
    if (window.focus) {
      newwindow.focus()
    }
    $('#btnWhiteList').prop('disabled', false);
    $('#btnGreyList').prop('disabled', false);
    $('#btnBlackList').prop('disabled', false);
    return false;
  });

  $('#pruefModal').on('shown.bs.modal', function () {
    var input = $('#InputEmail').val();
    var queryDomain = '';
    var result = '';
    var atsymb = input.indexOf("@");
    if (input === '') {
      $('#pruefModalAlert').text('Keine Eingabe.')
    } else {
      if (atsymb < 0) {
        $('#pruefModalAlert').text('Kein @ enthalten.')
      } else {
        queryDomain = input.substring(atsymb);
        checkdomain(queryDomain);
      }
    }
  });

  $('#pruefModal').on('hidden.bs.modal', function () {
    $('#pruefModalDecideBtn').prop('disabled', true);
    $('#pruefModalAlert').toggleClass('alert', false);
    $('#pruefModalAlert').toggleClass('alert-success', false);
    $('#pruefModalAlert').toggleClass('alert-danger', false);
    $('#pruefModalAlert').toggleClass('alert-warning', false);
    $('#pruefModalDecideBtn').text('Decide');
    $('#pruefModalAlert').text('...');
  });

  $('#decideModal').on('show.bs.modal', function(e) {
    var queryDomain = $(e.relatedTarget).attr('data-domain')
    $.getJSON( 'api/edugain/'+queryDomain, function( data ) {
        if (data.edugain || data.federation) {
          $('#checkEduresultAlert').toggleClass('alert-success', true);
          $('#checkEduresultAlert').html('<b>Domain '+queryDomain+' hat den eduGain-Test bestanden!</b>');
          $('#btnWhiteList').prop('disabled', false);
        } else {
          $('#checkEduresultAlert').html('Domain '+queryDomain+' hat den eduGain-Test <b>nicht</b> bestanden!');
        }
      });
    $('#decideModalTitle').text(queryDomain);
    $('input.domainname').val(queryDomain);
    $('#manualcheckbutton').attr("href", 'http://'+queryDomain.replace('@',''));
  });

  $('#decideModal').on('hidden.bs.modal', function() {
    $('#checkEduresultAlert').toggleClass('alert-success', false);
    $('#checkEduresultAlert').html('Teste eduGain ... <span class="glyphicon glyphicon-refresh glyphicon-spin"></span>');
    $('#btnWhiteList').prop('disabled', true);
    $('#btnGreyList').prop('disabled', true);
    $('#btnBlackList').prop('disabled', true);
  });

  $('#refreshmailsModal').on('show.bs.modal', function() {
    $('#refreshmailsModalText').html('Wirklich alle Mailadressen im LDAP suchen und gegen Listen mappen? <button type="button" class="btn btn-warning" id="refreshmailsModalButton">Ja!</button>');

    $('#refreshmailsModalButton').on('click', function(){
      $('#refreshmailsModalText').html('Working ... <span class="glyphicon glyphicon-refresh glyphicon-spin"></span>');
      $.getJSON( 'api/refresh', function( data ) {
        $('#refreshmailsModalText').html('Adressen schon auf der Whitelist: '+data['mails_on_whitelist']+' <br/>Adressen schon auf der Blacklist: '+data['mails_on_blacklist']+' <br/>Adressen noch in der Greylist: '+data['mails_on_greylist']+' <br/>Adressen jetzt neu auf der Greylist: '+data['mails_from_new_domains']+' <br/>Adressen automatisch neu auf der Whitelist: '+data['mails_automatically_whitelisted']);
        loadlist('grey');
        loadlist('white');
      });
    });

  });

});

function checkdomain(queryDomain){
  $.getJSON( 'api/domain/'+queryDomain, function( data ) {
    switch (data.listed) {
      case 'white':
        $('#pruefModalDecideBtn').prop('disabled', false);
        $('#pruefModalAlert').toggleClass('alert', true);
        $('#pruefModalAlert').toggleClass('alert-success', true);
        $('#pruefModalDecideBtn').text('Ändern');
        result = 'Domain ' + queryDomain + ' ist auf Whitelist!';
        break;
      case 'black':
        $('#pruefModalDecideBtn').prop('disabled', false);
        $('#pruefModalAlert').toggleClass('alert', true);
        $('#pruefModalAlert').toggleClass('alert-danger', true);
        $('#pruefModalDecideBtn').text('Ändern');
        result = 'Domain ' + queryDomain + ' ist auf Blacklist!';
        break;
      case 'grey':
        $('#pruefModalDecideBtn').prop('disabled', false);
        $('#pruefModalAlert').toggleClass('alert', true);
        $('#pruefModalAlert').toggleClass('alert-warning', true);
        $('#pruefModalDecideBtn').text('Ändern');
        result = 'Domain ' + queryDomain + ' ist auf Greylist!';
        break;
      default:
        $('#pruefModalDecideBtn').prop('disabled', false);
        $('#pruefModalDecideBtn').attr("data-domain", queryDomain);
        $('#pruefModalAlert').toggleClass('alert', true);
        $('#pruefModalAlert').toggleClass('alert-warning', true);
        result = 'Domain ' + queryDomain + ' unbekannt!';
    }
    $('#pruefModalAlert').text(result);
  });
}

function loadlist(currlist) {
  $.getJSON( 'api/list/'+currlist, function( data ) {
    var items = [];
    $.each( data, function( key, val ) {
      items.push('<a data-domain="'+val+'" data-toggle="modal" href="#decideModal" class="list-group-item">'+val+'</a>')
    });
    $('#'+currlist+'list').append(items);
    $('#'+currlist+'number').text(items.length);
  });
};

