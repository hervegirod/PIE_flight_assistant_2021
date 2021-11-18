$(function() {
    $("#flight_autocomplete").autocomplete({
        source: function(request, response) {
            $.getJSON('/_autocomplete',{
                q: request.term,
            }, function(data) {
                response($.map(data.matching_results, function(item) {
                  return {
                    label: item.str,
                    value: item.str,
                    flight_id : item.id
                  }
                }));
            });
        },
        minLength: 2,
        select: function(event, ui) {
          select_flight(ui.item);
        }
    });
});