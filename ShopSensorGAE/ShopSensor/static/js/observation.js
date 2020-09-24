function submitObservation(place_id) {
    $('#ObservationModal').modal('hide');
    // remove previous user information from observation nav tab
    $('#successSubmitObservation').addClass('invisible').removeClass('visible');
    $('#failSubmitObservation').addClass('invisible').removeClass('visible');
    // get client data
    let predictionPeople = $('input[name=PeopleSelection]:checked').val()
    let predictionQueue = $('input[name=QueueSelection]:checked').val()
    // create json out of the client observation

    let observation = {
        "place_id": place_id,
        "prediction_people": predictionPeople,
        "prediction_queue": predictionQueue
        };

    let endpoint = "/observation";
    $.ajax({
        type: "POST",
        url: endpoint,
        // The key needs to match your method's input parameter (case-sensitive).
        data: JSON.stringify(observation),
        contentType: "application/json; charset=utf-8",
        dataType: "json",
        success: function(data){
            if (data.message === 'success') {
                $('#successSubmitObservation').addClass('visible').removeClass('invisible');
                sidebar.open('observations');
            }
            else {
                timeToWait = data.time_to_wait
                $('#timeToWait').html(timeToWait)
                $('#failSubmitObservation').addClass('visible').removeClass('invisible');
                sidebar.open('observations');
            }
            // uncheck deactivate all button (around radio buttons) for the next observation
            $(".observation-button").map(function() {
                try {
                    $(this).removeClass('active')
                } catch(err) {
                    console.log(err)
                }
            });
        },
        failure: function(errMsg) {
        }
    });
}

function openObservationModal(place_id, place_name){
    let observationModal = `<div id="ObservationModal" class="modal fade hide" role="dialog" style="position:absolute; z-index: 9001">
                                <div class="modal-dialog">

                                <!-- Modal content-->
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h4 class="modal-title">Add your live observation</h4>
                                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                                    </div>
                                    <div class="modal-body">
                                        <div class="container-fluid">
                                            <div class="row" style="margin-left: 0.5vw"><b>Place:&nbsp; </b><b id="PlaceOfObservation" style="color: #007bff;"></b></div>
                                            <div class="row" style="height: 1.5vh"></div>
                                            <div class="row" style="margin-left: 0.5vw"><p>How many people are there currently?</p></div>
                                            <div class="row">
                                                <div class="col">
                                                    <div class="btn-group btn-group-justified" data-toggle="buttons">
                                                        <label class="btn btn-success observation-button"><input style="margin-right: 0.5vw" type="radio" name="PeopleSelection" value="few" autocomplete="off">Few</label>
                                                        <label class="btn btn-warning observation-button"><input style="margin-right: 0.5vw" type="radio" name="PeopleSelection" value="some" autocomplete="off">Some</label>
                                                        <label class="btn btn-danger observation-button"><input style="margin-right: 0.5vw" type="radio" name="PeopleSelection" value="many" autocomplete="off">Many</label>
                                                    </div>
                                                </div>
                                            </div><hr>
                                            <div class="row" style="margin-left: 0.5vw"><p>Is there a queue outside?</p></div>
                                            <div class="row">
                                                <div class="col">
                                                    <div class="btn-group btn-group-justified" data-toggle="buttons">
                                                        <label class="btn btn-success observation-button"><input style="margin-right: 0.5vw" type="radio" name="QueueSelection" value="no" autocomplete="off">No</label>
                                                        <label class="btn btn-danger observation-button"><input style="margin-right: 0.5vw" type="radio" name="QueueSelection" value="yes" autocomplete="off">Yes</label>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                        <div class="modal-footer">
                                            <p>Thank you for your help <i class="fa fa-heart-o" aria-hidden="true"></i></p>
                                            <input type="hidden" id="placeIdHiddenInput" name="placeId" value="">
                                            <button type="button" class="btn btn-primary" onclick="submitObservation($('#placeIdHiddenInput').val())">Submit</button>
                                            <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                                        </div>
                                    </div>
                                </div>
                            </div>`
    $('#ObservationModalDiv').html(observationModal)
    place_name = String(place_name)
    $('#PlaceOfObservation').html(place_name) // show selected place name to client
    $('#placeIdHiddenInput').val(place_id) //set the hidden input field that the place id can be passed to the submitObservation
    $('#ObservationModal').modal('show');
}