### ChemManager Coffee(Java)script function ###
# Compile with:
# cat *.coffee | coffee -c -s -b > ../core/static/core/js/cm.js

add_bookmark = (dlg_id, api_url) ->
  path = window.location.pathname
  name = $('#bm_name').val()
  data =
    'path': path
    'name': name
  UIkit.modal(dlg_id).hide()
  $.post api_url, data, (res) ->
    $('#bookmarks').prepend res
    return
  return

chem_format = (elem) ->
  result = ''
  in_sub = false
  in_hydro = false
  cursor = 0
  target = ''
  formula = elem.text()
  while cursor < formula.length
    if !isNaN(target = formula.charAt(cursor))
      target = '#'
    switch target
      when '#'
        if in_sub == false and in_hydro == false
          result = "#{result}<sub>"
          in_sub = true
        if in_hydro
          in_hydro = false
        result = "#{result}#{formula.charAt(cursor)}"
        if in_sub
          result = "#{result}</sub>"
          in_sub = false
      when ' ', '.', '-'
        result = "#{result}#{formula.charAt(cursor)}"
      when '·', '*'
        in_hydro = true
        if in_sub
          result = "#{result}</sub>"
          in_sub = false
        result = "#{result}#{formula.charAt(cursor)}"
      else
        if in_hydro
          in_hydro = false
        if in_sub
          result = "#{result}</sub>"
          in_sub = false
        result = "#{result}#{formula.charAt(cursor)}"
    cursor++
  if in_sub
    result = "#{result}</sub>"
  elem.html result
  return

make_datatable = (elem, options) ->
  i18n =
    'sEmptyTable': gettext('No data available in table')
    'sInfo': gettext('Showing _START_ to _END_ of _TOTAL_ entries')
    'sInfoEmpty': gettext('Showing 0 to 0 of 0 entries')
    'sInfoFiltered': gettext('(filtered from _MAX_ total entries)')
    'sInfoPostFix': ''
    'sInfoThousands': gettext(',')
    'sLengthMenu': gettext('Show _MENU_ entries')
    'sLoadingRecords': gettext('Loading...')
    'sProcessing': gettext('Processing...')
    'sSearch': gettext('Search:')
    'sZeroRecords': gettext('No matching records found')
    'oPaginate':
      'sFirst': gettext('First')
      'sLast': gettext('Last')
      'sNext': gettext('Next')
      'sPrevious': gettext('Previous')
    'oAria':
      'sSortAscending': gettext(': activate to sort column ascending')
      'sSortDescending': gettext(': activate to sort column descending')
  opts = $.extend({ 'language': i18n }, options)
  elem.dataTable opts
  return

make_more_link = (options) ->
  opts = $.extend({
    'show_char': 100
    'ellipsestext': '...'
    'moretext': gettext(' Show more >')
    'lesstext': gettext(' < Show less')
    'duration': 500
  }, options)
  $('.more').each ->
    content = $(this).html()
    if content.length > opts['show_char']
      c = content.substr(0, opts['show_char'])
      h = content.substr(opts['show_char'], content.length - (opts['show_char']))
      html = "#{c}<span class='moreellipses'>#{opts['ellipsestext']}</span>" +
             "<span class='morecontent'><span>#{h}</span>" +
             "<a href='' class='morelink'>#{opts['moretext']}</a></span>"
      $(this).html html
    return
  $('.morelink').click ->
    if $(this).hasClass('less')
      $(this).removeClass 'less'
      $(this).html opts['moretext']
    else
      $(this).addClass 'less'
      $(this).html opts['lesstext']
    $(this).parent().prev().toggle opts['duration']
    $(this).prev().toggle opts['duration']
    false
  return

jQuery.fn.highlight = (str) ->
  regex = new RegExp(str, 'gi')
  @each ->
    $(this).contents().filter(->
      @nodeType == 3 and regex.test(@nodeValue)
    ).replaceWith ->
      (@nodeValue or '').replace regex, (match) ->
        "<mark>#{match}</mark>"
    return

load_inventory = ->
  $('.storage-data').each ->
    td = $(this)
    url = td.data('url')
    $.getJSON url, (data) ->
      cell = "<td class='uk-text-right'><a href='#{data['url']}'>" +
             "#{data['value']} #{data['unit']}</a></td>"
      td.replaceWith cell
      return
    return
  return

load_limit = ->
  $('.limit-data').each ->
    td = $(this)
    url = td.data('url')
    $.get url, (data) ->
      td.replaceWith data
      return
    return
  return

$(document).ready ->
  # Parse chemical formulas
  $('.formula').each (i) ->
    f = $(this)
    chem_format f
    return
  # 'Read more' link generation
  more_link_options =
    'show_char': 160
    'duration': 100
  make_more_link more_link_options
  return
