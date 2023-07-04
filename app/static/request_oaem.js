function convertUnixTimestamp(unixTimestamp) {
    const timestampNumber = parseInt(unixTimestamp, 10);

    if (isNaN(timestampNumber)) {
        return "Unknown"
    }

    const date = new Date(timestampNumber * 1000);
    return date.toLocaleString();
}

function handle_plot_response(response) {
    let within_area = JSON.parse(response.within_area);

    if (within_area === false) {
        document.getElementById('position').style.color = 'red';
        document.getElementById('position').textContent = `Current Position: ${latitude}°, ${longitude}°, ${height} m\n is outside of the coverage area.`;
    } else {
        document.getElementById('position').style.color = 'black';
    }
    const sunVisibilityText = `Sun Visibility: ${response.visible}`;
    const sunSinceText = `Since: ${convertUnixTimestamp(response.since)}`;
    const sunUntilText = `Until: ${convertUnixTimestamp(response.until)}`;

    document.getElementById('sun').innerHTML = `${sunVisibilityText}<br>${sunSinceText}<br>${sunUntilText}`;

    let fig = JSON.parse(response.data);
    Plotly.newPlot("plot", fig.data, fig.layout);
}

function request_oaem(position) {
    const latitude = position.coords.latitude.toFixed(6);
    const longitude = position.coords.longitude.toFixed(6);
    let height = position.coords.altitude;
    let { heading } = position.coords;

    const winwidth = (window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth) - 20;
    const winheight = (window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight) - 20;

    if (height === null) {
        height = 0.0.toFixed(1);
    } else {
        height = height.toFixed(1);
    }

    if (heading === null) {
        heading = 0.0.toFixed(1)
    } else {
        heading = heading.toFixed(1)
    }

    document.getElementById('position').innerText = `Current Position: ${latitude}°, ${longitude}°, ${height} m`;

    $.ajax({
        url: `/plot?pos_x=${latitude}&pos_y=${longitude}&pos_z=${height}&epsg=4326&width=${winwidth}&height=${winheight}&heading=${heading}`,
        type: "GET",
        dataType: "json",
        success: handle_plot_response,
    });

}

function handle_position_watcher_error(error) {
    console.error('Error getting position:', error);
}

const positionWatcher = navigator.geolocation.watchPosition(
    request_oaem,
    handle_position_watcher_error,
    {
        enableHighAccuracy: true,
        maximumAge: 0
    }
);

function stopWatchingPosition() {
    navigator.geolocation.clearWatch(positionWatcher);
}

window.addEventListener('beforeunload', stopWatchingPosition);
