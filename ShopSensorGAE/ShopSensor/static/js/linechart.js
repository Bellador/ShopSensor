function drawLinechart(e) {
    // go to statistics tab when someone clicks on a marker
    //sidebar.open('statistics');
    try {
        // when called from an event - on marker click
        var data = e.target.data      
    }
    catch(err) {
        // used when drawing the inital linechart for rank 1 
        var data = e.data
    }

    var place = data.place_name
    // add place to the statistics tab
    $( "#lineChartPlace" ).html(`<p><b>Selected</b> &nbsp; ${place}</p>`);

    // check if sensor data is present
    var has_sensorData = false
    if ('popular_times' in data) {
        has_sensorData = true
        sidebar.open('statistics');
    }
    // only draw the linechart for markers that actually have sensor data
    if (has_sensorData) {
        var historicalSensorData = data.popular_times.historical
        let graphData = []
        for (let i = 0; i < historicalSensorData.length; i++) {
            let dateTime = new Date(historicalSensorData[i].unix_time * 1000)            
            graphData.push({date: dateTime, normal: historicalSensorData[i].normal, current: historicalSensorData[i].current});
        }

        c3.generate({
            bindto: '#lineChart',
            padding: {
                right: 10
                , left: 20
                , bottom: 130
            },
            data: {
                json: graphData,
                keys: {
                    x: 'date',
                    value: ['normal', 'current']
                }
            },
            axis: {
                x: {
                    type: 'timeseries',
                    tick: {
                        rotate: -45,
                        format: '%a %d.%m %H:%M' //'%d.%m %H:%M' '%d.%m.%Y - %H:%M'
                    },
                    label: 'Date'
                },
                y: {
                    tick: {
                        format: function (x) {
                            return d3.round(x, 1);
                        }
                    },
                    label: 'Percent store capacity'
                }
            },
            zoom: {
                enabled: true
            }
        });
    } else {
        //if the marker doesn't have a rank that means there is no sensor data and the linechart must not be drawn
        $( "#lineChart" ).html(`<p>No Sensor Data available</p>`);
    }
}