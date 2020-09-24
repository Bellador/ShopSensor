function navBarSearch() {
    search()
    sidebar.close('navsearch');
}

function search(data){
    // show loading Spinner
    $('#loadingSpinner').addClass('visible').removeClass('invisible');
    // get selected shop-types
    var shopTypeList = []
    if($('#all_shops').prop('checked')){
        shopTypeList.push('all_shops')
    } else {
        $(".custom-control-input").each(function() {
            // check not to be id all_shops
            let shopType = $(this).attr('id')
            if (shopType != 'all_shops') {
                // chech if checkbox is checked lol
                if($(this).prop('checked')){
                    shopTypeList.push(shopType)
                }
            }
        });
    }
    // get bounding box parameters
    var bbox = map.getBounds();
    var payload = {"shopTypes": shopTypeList,
                    "bbox": bbox}
    var endpoint = "/searchresults";
    $.ajax({
        type: "POST",
        url: endpoint,
        // the key needs to match your method's input parameter (case-sensitive).
        data: JSON.stringify(payload),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(data){addMarkers(data)},
        failure: function(errMsg) {
            document.getElementById("searchErrorMsgBox").style.display = 'block';
        }
    });
}