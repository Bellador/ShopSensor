//HARD REFRESH CTRL +F5
map = L.map("map").setView([46.803820, 8.261719], 9)
markersLayer = L.layerGroup().addTo(map);
map.zoomControl.setPosition('bottomright')
// or id: mapbox/satellite-v9 mapbox/streets-v11-->
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}?access_token={accessToken}', {
attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="https://www.mapbox.com/">Mapbox</a>',
maxZoom: 18,
id: 'mapbox/streets-v11',
tileSize: 512,
zoomOffset: -1,
accessToken: '<ADD HERE>'
}).addTo(map);

let sidebar = L.control.sidebar('sidebar').addTo(map)
sidebar.open('home');

map.on('moveend', onMapInteraction);

function openStatisticTab() {
    sidebar.open('statistics');
}

function onMapInteraction(e) {
    // define zoom level from which searching is allowed to avoid too big queries
    var searchZoom = 14;
    if (map.getZoom() >= searchZoom){
      //enable search button
      $("#searchButton").removeClass("disabled")
      $("#searchButton").html("Search!")
      $("#searchButton").prop('disabled', false);
      $("#searchButtonNav").prop('disabled', false);
      $("#searchButtonNavIcon").removeClass("btn-inaktive").addClass("btn-aktive")
    }
    else {
        $("#searchButton").addClass("disabled")
        $("#searchButton").html("Zoom in to search!")
        $("#searchButton").prop('disabled', true);
        $("#searchButtonNav").prop('disabled', true);
        $("#searchButtonNavIcon").removeClass("btn-aktive").addClass("btn-inaktive")
    }
}

function addQueryStatistic(json){
    // draw general statistics to the performed query, such as returned places and list the top 3 ranks with their marker colors
    let placeCount = Object.keys(json).length -1
    let sensorCount = json.statistic.places_w_sensordata
    let observationCount = json.statistic.nr_of_observations
    $( "#placeCount" ).text(`${placeCount}`);
    $( "#sensorCount" ).text(`${sensorCount}`);
    $( "#observationCount" ).text(`${observationCount}`);
}

function addMarkers(json){
    // first remove all markers from previous searches
    markersLayer.clearLayers();
    // add search result data to statistics navbar tab
    $('#queryReturn').addClass('visible').removeClass('invisible');
    sidebar.open('statistics');
    addQueryStatistic(json);
    $.each(json,function(key, markerData) {
        // check if the key is actually a place_id and not the query statistic
        if (key != 'statistic' && key != 'message') {
        
            var marker = L.marker([markerData.lat, markerData.lng])
            // add marker to map layer
            marker.addTo(markersLayer)
            marker.data = markerData //add all marker specific data as attribute to the marker for later assiciations
            marker = addPopupToMarker(key, marker)
            marker = setMarkerStyle(marker)
            marker.on("click", drawLinechart)
            
        }
    });
    // hide loading Spinner
    $('#loadingSpinner').addClass('invisible').removeClass('visible')
}

function addPopupToMarker(key, marker){
    // define responsive pop-up size as well as font size
    let font_size = '2vw'
    let smiley_size = '5vh'
    let title_color = '#0074d9' // light blue
    let nodata_color = '#fcb603' // light orange
    let window_height = $(window).height()
    let window_width = $(window).width()
    let desired_height = 0.6 * window_height
    let desired_width = 0.6 * window_width
    // process place attributes
    var place_id = key
    var place_name = marker.data.place_name
    var open_hours = marker.data.open_hours.toString().replace(/,/g, '<br>'); //split by comma for prettier placement
    // check what data (sensor, observation) is present for the given marker
    let has_sensorData = false
    let has_observationData = false
    // presence of observationRank indicates recent observations that count towards the place ranking
    let has_observationRank = false
    let has_popularityRank = false
    // check if a observation rank is present
    try {
        var observationRank = marker.data.observation_data.observation_rank
        if (observationRank != null || observationRank != undefined) {
            has_observationRank = true
        }
      } catch(err) {
        // no rank found
    }
    // check if a absolute (popularity) rank is present
    try {
        var rank = marker.data.popularity_rank
        if (rank != null) {
            has_popularityRank = true
        }
      } catch(err) {
        // no rank found
    }
    if ('popular_times' in marker.data) {
        has_sensorData = true
        // get sensor data from marker attributes
        var current_popularity = marker.data.popular_times.most_recent.current;
        var ratio = marker.data.popular_times.most_recent.ratio;
        var percentage_nr = Math.round(Math.abs(ratio * 100 - 100));
        var curr_unix_time = marker.data.popular_times.most_recent.unix_time
        var curr_str_time = timeConverter(curr_unix_time)
    }
    if ('observation_data' in marker.data) {
        has_observationData = true
        
        // get observation data from marker attribute
        // most_recent has to exist
        var firstObsPeople = marker.data.observation_data.most_recent.prediction_people
        var firstObsQueue = marker.data.observation_data.most_recent.prediction_queue
        var firstObsDate = marker.data.observation_data.most_recent.unix_time
        var firstObsDate = timeConverter(firstObsDate)
        // color formatting
        if (firstObsPeople === 'few') {
            var firstObsPeopleColor = '#28a745'
        } else if (firstObsPeople === 'some') {
            var firstObsPeopleColor = '#ffc107'
        } else {
            var firstObsPeopleColor = '#dc3545'
        }

        if (firstObsQueue === 'no') {
            var firstObsQueueColor = '#28a745'
        } else {
            var firstObsQueueColor = '#dc3545'
        }
        // default values in case no history exists
        var secObsPeople = '-'
        var secObsQueue = '-'
        var secObsDate = '-'
        var secObsPeopleColor = '#212121'
        var secObsQueueColor = '#212121'

        var thirdObsPeople = '-'
        var thirdObsQueue = '-'
        var thirdObsDate = '-'
        var thirdObsPeopleColor = '#212121'
        var thirdObsQueueColor = '#212121'
        // iterate over historical observation records
        var historical_observations = marker.data.observation_data.historical
        $.each(historical_observations, function (index, entry) {
            // second most recent observation
            if ( index == 0) {
                secObsPeople = entry.prediction_people
                secObsQueue = entry.prediction_queue
                secObsDate = entry.unix_time
                secObsDate = timeConverter(secObsDate)
                // color formatting
                if (secObsPeople === 'few') {
                    secObsPeopleColor = '#28a745'
                } else if (secObsPeople === 'some') {
                    secObsPeopleColor = '#ffc107'
                } else {
                    secObsPeopleColor = '#dc3545'
                }

                if (secObsQueue === 'no') {
                    secObsQueueColor = '#28a745'
                } else {
                    secObsQueueColor = '#dc3545'
                }
            // third most recent observation
            }  else if ( index == 1) {
                thirdObsPeople = entry.prediction_people
                thirdObsQueue = entry.prediction_queue
                thirdObsDate = entry.unix_time
                thirdObsDate = timeConverter(thirdObsDate)
                // color formatting
                if (thirdObsPeople === 'few') {
                    thirdObsPeopleColor = '#28a745'
                } else if (thirdObsPeople === 'some') {
                    thirdObsPeopleColor = '#ffc107'
                } else {
                    thirdObsPeopleColor = '#dc3545'
                }

                if (thirdObsQueue === 'no') {
                    thirdObsQueueColor = '#28a745'
                } else {
                    thirdObsQueueColor = '#dc3545'
                }
            // to neglect
            } else { }
        })
    }

    // differentiate between markers that have sensor data and not
    if (has_sensorData) {
        //always positive smiley
        if (current_popularity < 30){
            var smiley = '/static/img/smiley_positive.png'
            var color_to_use = '#33cc33'; // green
            if (ratio > 1){
                percentage_text = `Few people but ${percentage_nr}% more than expected`;
                if (ratio > 1.75){
                    // color over 75%
                    var color_to_use = '#f5a742'; //orange
                }
            } else if (ratio < 1){
                percentage_text = `Few people <em>and</em> ${percentage_nr}% less than expected`;
            } else {
                percentage_text = 'Few people as usual';
            }
        } 
        // either positive smiley or uncertain smiley depending on the ratio between normal and current popularity
        else if (current_popularity >= 30 && current_popularity < 50){
            var smiley = '/static/img/smiley_positive.png';
            if (ratio > 1){
                percentage_text = `Some people <em>but</em> ${percentage_nr}% more than expected`;
                if (ratio < 1.25){
                    var color_to_use = '#33cc33'; // green
                } else if (ratio >= 1.25 && ratio <= 1.5){
                    // color over 25% - 50%
                    var color_to_use = '#f5a742'; //orange
                } else if (ratio > 1.5){
                    // color over 50%
                    var smiley = '/static/img/smiley_uncertain.png';
                    var color_to_use = '#f54242'; //red
                }
            } else if (ratio < 1){
                percentage_text = `Some people <em>but</em> ${percentage_nr}% less than expected`;
                var color_to_use = '#33cc33'; // green
            } else {
                percentage_text = 'Some people as usual';
                var color_to_use = '#b5b5b5'; //light grey
            }
        } 
        // either uncertain or negative smiley
        else if (current_popularity >= 50 && current_popularity < 75){
            var smiley = '/static/img/smiley_uncertain.png';
            if (ratio > 1){
                percentage_text = `Quite many people <em>and</em> ${percentage_nr}% more than expected`;
                var color_to_use = '#f5a742'; //orange
                if (ratio > 1.25){
                    // color over 25%
                    var smiley = '/static/img/smiley_negative.png';
                    var color_to_use = '#f54242'; //red
                }
            } else if (ratio < 1){
                percentage_text = `Quite many people <em>but</em> ${percentage_nr}% less than expected`;
                var color_to_use = '#33cc33'; // green
            } else {
                percentage_text = 'Many people as usual';
                var color_to_use = '#b5b5b5'; //light grey
            }
        }
        // always negative smiley
        else {
            var smiley = '/static/img/smiley_negative.png';
            if (ratio > 1){
                var percentage_text = `<em>Many people and also</em> ${percentage_nr}% more than expected`;
                var color_to_use = '#f54242'; //red
                
            } else if (ratio < 1){
                var percentage_text = `Many people but ${percentage_nr}% less than expected`;
                var color_to_use = '#f5a742'; //orange
            } else {
                var percentage_text = 'Many people as usual';
                var color_to_use = '#f5a742'; //orange
            }
        }
        // change smiley if observationRank is present - higher priority
        if (has_observationRank){
            // always positive smiley
            if (observationRank == 0){
                smiley = '/static/img/smiley_positive.png'
                color_to_use = '#33cc33'; // green
                percentage_text = `Few people and no queue were reported by a user`;
            } 
            // uncertain smiley 
            else if (observationRank == 50){
                smiley = '/static/img/smiley_uncertain.png';
                color_to_use = '#f5a742'; //orange
                percentage_text = `Some people and no queue were reported by a user`;
            } 
            // always negative smiley - current_popularity >= 100
            else {
                smiley = '/static/img/smiley_negative.png';
                color_to_use = '#f54242'; //red
                percentage_text = `Many people were reported by a user!`;
            }
        }
        // no observation data
        if (!has_observationData) {
            // build the marker pop-up text (original smiley height: 100px)
            var popupTxt = `<div class="container-fluid" style="min-width: ${desired_width}">
                                <div class="row row-margin-1vh align-items-center">
                                    <div class="col-2"><button type="button" class="btn btn-info observation-button-popup float-left" onclick="openObservationModal('${place_id}', '${place_name}')"><i class="fa fa-eye" aria-hidden="true"></i></button></div>
                                    <div class="col-2"><button type="button" class="btn btn-info stats-button-popup float-left" onclick="openStatisticTab()"><i class="fa fa-line-chart" aria-hidden="true"></i></button></div>
                                    <div class="col-8"><font size=${font_size} color=${title_color}><b>&nbsp;&nbsp;&nbsp;&nbsp;Sensor Data</b></font></div>  
                                </div>
                                <div class="row row-margin-1vh">
                                    <div class="col"><font size=${font_size}><b>Rank ${marker.data.popularity_rank}</b><a href="${marker.data.store_url}" class="text-decoration-none">&nbsp;&nbsp;&nbsp;<b>${marker.data.place_name}</font></b></a></div>
                                </div>
                                <div class="row text-center align-items-center row-margin-1vh">
                                    <div class="col"><img src=${smiley} style="height:${smiley_size}" class="rounded mx-auto d-block"></div>
                                </div>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><font size=${font_size} style="color: ${color_to_use}"><b>${percentage_text}</b></font></div>  
                                </div>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><font size=${font_size}><b>Date:</b> ${curr_str_time}</font></div>  
                                </div><hr>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No Observation Data</div>
                                </div>
                                <div class="row row-margin row-margin-2vh">
                                    <div class="col"><font size="1vw"><b>Address:</b><br>${marker.data.address}</font></div> 
                                </div>
                                <div class="row">
                                    <div class="col"><font size="1vw"><b>Open hours:</b><br>${open_hours}</font></div>
                                </div>
                            </div>
                            `;
        // sensor AND observation data
        } else {
            var popupTxt = `<div class="container-fluid" style="min-width: ${desired_width}">
                                <div class="row row-margin-1vh align-items-center">
                                    <div class="col-2"><button type="button" class="btn btn-info observation-button-popup float-left" onclick="openObservationModal('${place_id}', '${place_name}')"><i class="fa fa-eye" aria-hidden="true"></i></button></div>
                                    <div class="col-2"><button type="button" class="btn btn-info stats-button-popup float-left" onclick="openStatisticTab()"><i class="fa fa-line-chart" aria-hidden="true"></i></button></div>
                                    <div class="col-8"><font size=${font_size} color=${title_color}><b>&nbsp;&nbsp;&nbsp;&nbsp;Sensor Data</b></font></div>  
                                </div>
                                <div class="row row-margin-1vh">
                                    <div class="col"><font size=${font_size}><b>Rank ${marker.data.popularity_rank}</b><a href="${marker.data.store_url}" class="text-decoration-none">&nbsp;&nbsp;&nbsp;<b>${marker.data.place_name}</font></b></a></div>
                                </div>
                                <div class="row text-center align-items-center row-margin-1vh">
                                    <div class="col"><img src=${smiley} style="height:${smiley_size}" class="rounded mx-auto d-block"></div>
                                </div>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><font size=${font_size} style="color: ${color_to_use}"><b>${percentage_text}</b></font></div>  
                                </div>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><font size=${font_size}><b>Date:</b> ${curr_str_time}</font></div>  
                                </div><hr>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><font size=${font_size} color=${title_color}><b>Observation Data</b></font></div>  
                                </div>
                            
                                <table class="table borderless">
                                    <thead>
                                        <tr>
                                        <th scope="col">#</th>
                                        <th scope="col">People</th>
                                        <th scope="col">Queue</th>
                                        <th scope="col">Date</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                        <th scope="row">1</th>
                                        <td><font size=${font_size}><b style="color: ${firstObsPeopleColor}">${firstObsPeople}</b></font></td>
                                        <td><font size=${font_size}><b style="color: ${firstObsQueueColor}">${firstObsQueue}</b></font></td>
                                        <td><font size=${font_size}>${firstObsDate}</font></td>
                                        </tr>
                                        <tr>
                                        <th scope="row">2</th>
                                        <td><font size=${font_size}><b style="color: ${secObsPeopleColor}">${secObsPeople}</b></font></td>
                                        <td><font size=${font_size}><b style="color: ${secObsQueueColor}">${secObsQueue}</b></font></td>
                                        <td><font size=${font_size}>${secObsDate}</font></td>
                                        </tr>
                                        <tr>
                                        <th scope="row">3</th>
                                        <td><font size=${font_size}><b style="color: ${thirdObsPeopleColor}">${thirdObsPeople}</b></font></td>
                                        <td><font size=${font_size}><b style="color: ${thirdObsQueueColor}">${thirdObsQueue}</b></font></td>
                                        <td><font size=${font_size}>${thirdObsDate}</font></td>
                                        </tr>
                                    </tbody>
                                </table>
                                <hr>
                                <div class="row row-margin row-margin-2vh">
                                    <div class="col"><font size="1vw"><b>Address:</b><br>${marker.data.address}</font></div> 
                                </div>
                                <div class="row">
                                    <div class="col"><font size="1vw"><b>Open hours:</b><br>${open_hours}</font></div>
                                </div>
                            </div>`;
            }
    // no sensor data
    } else {
        // no data at all!
        if (!has_observationData) {
            // build the marker pop-up text
            var popupTxt = `<div class="container-fluid">
                                <div class="row row-margin-1vh">
                                    <div class="col-4"><button type="button" class="btn btn-info observation-button" onclick="openObservationModal('${place_id}', '${place_name}')"><i class="fa fa-eye" aria-hidden="true"></i></button></div>
                                    <div class="col-8"><font size=${font_size}><a href="${marker.data.store_url}" class="text-decoration-none"><b>${marker.data.place_name}</b></a></font></div>
                                </div>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No Sensor Data</div>
                                </div><hr>
                                <div class="row text-center row-margin-1vh">
                                    <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No Observation Data</div>
                                </div>
                                <div class="row row-margin row-margin-2vh">
                                    <div class="col"><font size="1vw"><b>Address:</b><br>${marker.data.address}</font></div> 
                                </div>
                                <div class="row">
                                    <div class="col"><font size="1vw"><b>Open hours:</b><br>${open_hours}</font></div>
                                </div>
                            </div>
                            `;
        // no sensor data BUT observation data
        } else {
            // check if observationRank is present
            if (has_observationRank) {
                // change smiley if observationRank is present - higher priority
                // always positive smiley
                if (observationRank == 0){
                    smiley = '/static/img/smiley_positive.png'
                    color_to_use = '#33cc33'; // green
                    percentage_text = `Few people and no queue says a recent user`;
                } 
                // uncertain smiley 
                else if (observationRank == 50){
                    smiley = '/static/img/smiley_uncertain.png';
                    color_to_use = '#f5a742'; //orange
                    percentage_text = `Some people and no queue says a recent user`;
                } 
                // always negative smiley - current_popularity >= 100
                else {
                    smiley = '/static/img/smiley_negative.png';
                    color_to_use = '#f54242'; //red
                    percentage_text = `Many people says a recent user!`;
                }
                var popupTxt = `<div class="container-fluid">
                                    <div class="row row-margin-1vh">
                                        <div class="col-3"><button type="button" class="btn btn-info observation-button" onclick="openObservationModal('${place_id}', '${place_name}')"><i class="fa fa-eye" aria-hidden="true"></i></button></div>
                                        <div class="col-9"><font size=${font_size}><b>Rank ${marker.data.popularity_rank}</b><a href="${marker.data.store_url}" class="text-decoration-none">&nbsp;&nbsp;&nbsp;<b>${marker.data.place_name}</font></b></a></div>
                                    </div>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No Sensor Data</div>
                                    </div><hr>
                                    <div class="row text-center align-items-center row-margin-1vh">
                                        <div class="col"><img src=${smiley} style="height:${smiley_size}" class="rounded mx-auto d-block"></div>
                                    </div>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><font size=${font_size} style="color: ${color_to_use}"><b>${percentage_text}</b></font></div>  
                                    </div>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><font size=${font_size} color=${title_color}><b>Observation Data</b></font></div>  
                                    </div>
                                
                                    <table class="table borderless">
                                        <thead>
                                            <tr>
                                            <th scope="col">#</th>
                                            <th scope="col">People</th>
                                            <th scope="col">Queue</th>
                                            <th scope="col">Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                            <th scope="row">1</th>
                                            <td><font size=${font_size}><b style="color: ${firstObsPeopleColor}">${firstObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${firstObsQueueColor}">${firstObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${firstObsDate}</font></td>
                                            </tr>
                                            <tr>
                                            <th scope="row">2</th>
                                            <td><font size=${font_size}><b style="color: ${secObsPeopleColor}">${secObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${secObsQueueColor}">${secObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${secObsDate}</font></td>
                                            </tr>
                                            <tr>
                                            <th scope="row">3</th>
                                            <td><font size=${font_size}><b style="color: ${thirdObsPeopleColor}">${thirdObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${thirdObsQueueColor}">${thirdObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${thirdObsDate}</font></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <hr>
                                    <div class="row row-margin row-margin-2vh">
                                        <div class="col"><font size="1vw"><b>Address:</b><br>${marker.data.address}</font></div> 
                                    </div>
                                    <div class="row">
                                        <div class="col"><font size="1vw"><b>Open hours:</b><br>${open_hours}</font></div>
                                    </div>
                                </div>`;

            } else {
                var popupTxt = `<div class="container-fluid">
                                    <div class="row row-margin-1vh">
                                        <div class="col-4"><button type="button" class="btn btn-info observation-button" onclick="openObservationModal('${place_id}', '${place_name}')"><i class="fa fa-eye" aria-hidden="true"></i></button></div>
                                        <div class="col-8"><font size=${font_size}><a href="${marker.data.store_url}" class="text-decoration-none"><b>${marker.data.place_name}</b></a></font></div>
                                    </div>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No Sensor Data</div>
                                    </div><hr>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><font size=${font_size} color=${title_color}><b>Observation Data</b></font></div>  
                                    </div>
                                    <div class="row text-center row-margin-1vh">
                                        <div class="col"><i class="fa fa-question-circle" aria-hidden="true" style="color: ${nodata_color}"></i> No recent entries</div>  
                                    </div>
                                    <table class="table borderless">
                                        <thead>
                                            <tr>
                                            <th scope="col">#</th>
                                            <th scope="col">People</th>
                                            <th scope="col">Queue</th>
                                            <th scope="col">Date</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                            <th scope="row">1</th>
                                            <td><font size=${font_size}><b style="color: ${firstObsPeopleColor}">${firstObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${firstObsQueueColor}">${firstObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${firstObsDate}</font></td>
                                            </tr>
                                            <tr>
                                            <th scope="row">2</th>
                                            <td><font size=${font_size}><b style="color: ${secObsPeopleColor}">${secObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${secObsQueueColor}">${secObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${secObsDate}</font></td>
                                            </tr>
                                            <tr>
                                            <th scope="row">3</th>
                                            <td><font size=${font_size}><b style="color: ${thirdObsPeopleColor}">${thirdObsPeople}</b></font></td>
                                            <td><font size=${font_size}><b style="color: ${thirdObsQueueColor}">${thirdObsQueue}</b></font></td>
                                            <td><font size=${font_size}>${thirdObsDate}</font></td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <hr>
                                    <div class="row row-margin row-margin-2vh">
                                        <div class="col"><font size="1vw"><b>Address:</b><br>${marker.data.address}</font></div> 
                                    </div>
                                    <div class="row">
                                        <div class="col"><font size="1vw"><b>Open hours:</b><br>${open_hours}</font></div>
                                    </div>
                                </div>`;
            }
        }
    }
    marker.bindPopup(popupTxt, {'maxHeight': `${desired_height}`, 'maxWidth': `${desired_width}`})
    return marker
}

function timeConverter(UNIX_timestamp){
    var a = new Date(UNIX_timestamp * 1000);
    var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    var year = a.getFullYear();
    var month = months[a.getMonth()];
    var date = a.getDate();
    var hour = a.getHours();
    if (hour < 10){
        hour = '0' + hour
    }
    var min = a.getMinutes();
    if (min < 10){
        min = '0' + min
    }
    var time = date + ' ' + month + ' ' + year + ' ' + hour + ':' + min;
    return time;
  }


function setMarkerStyle(marker){
    let place_name = marker.data.place_name
    let icon
    // check what data (sensor, observation) is present for the given marker
    let has_sensorData = false
    let has_observationData = false
    let has_popularity_rank = false

    // check if a popularity rank is present
    try {
        var rank = marker.data.popularity_rank
        if (rank != null) {
            has_popularity_rank = true
        }
      } catch(err) {
        // no rank found
    }
    if ('popular_times' in marker.data) {
        has_sensorData = true
    }
    if ('observation_data' in marker.data) {
        has_observationData = true
    }
    // markers that hold sensor data by checking of the rank is assigned

    if (has_popularity_rank)
        switch(rank) {
            case 1:
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-green.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [32, 55],
                    iconAnchor : [15, 55],
                    popupAnchor : [1, -55],
                    shadowSize : [55, 55]   
                })
                // update the query overview for rankOne
                $("#rankOne").text(`${place_name}`);
                // draw linchart (if sensor data is available) for rank 1 already since the popup is opend automatically and not by on marker click
                drawLinechart(marker)
                marker.openPopup()
                break;
            case 2:
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-blue.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [32, 55],
                    iconAnchor : [15, 55],
                    popupAnchor : [1, -55],
                    shadowSize : [55, 55]   
                })
                $("#rankTwo").text(`${place_name}`);
                break;
            case 3:
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-red.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [32, 55],
                    iconAnchor : [15, 55],
                    popupAnchor : [1, -55],
                    shadowSize : [55, 55]       
                })
                $("#rankThree").text(`${place_name}`);
                break;
            default:
                // holds sensor data or observation data but not among the top 3
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-gold.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [25, 41],
                    iconAnchor : [12, 41],
                    popupAnchor : [1, -41],
                    shadowSize : [41, 41] 
                })
        } else {
            // holds sensor data or observation data but not among the top 3
            if (has_sensorData || has_observationData) {
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-gold.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [25, 41],
                    iconAnchor : [12, 41],
                    popupAnchor : [1, -41],
                    shadowSize : [41, 41] 
                })
            // markers that do not hold any data 
            } else {
                icon = new L.Icon({
                    iconUrl : "/static/img/marker-icon-2x-grey.png",
                    shadowUrl : '/static/img/marker-shadow.png',
                    iconSize : [12, 20],
                    iconAnchor : [6, 20],
                    popupAnchor : [1, -20],
                    shadowSize : [20, 20]
                })
            }
        }
    marker.setIcon(icon)
    return marker
    }

function zoomToPlace(place) {
    sidebar.close('home');
    disableTutorial()

    let places = {
        "Zurich":[47.367139, 8.541128],
        "Zug": [47.171080, 8.513711],
        "Bern": [46.948169, 7.446376],
        "Biel": [47.136260, 7.246292],
        "Ettingen": [47.481047, 7.544535]
    }

    map.flyTo(places[place], 14);
    map.once('zoomend', function () {
        search(); //call-back function which fires when flyTo is complete
    });
}

function disableTutorial(){
    $("#tutorial").hide();
}
  