$(document).ready(function(){
    $("ul#results-listing li").click(function(evt){
        var item_id = $(evt.currentTarget).attr('id');
        var div_id = item_id.replace(/match-title-/, 'match-text-');
        $("div.match-text:visible").hide();
        $("div#" + div_id).show();
    });
});
