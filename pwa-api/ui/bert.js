
// The width and height of the captured photo. We will set the
// width to the value defined here, but the height will be
// calculated based on the aspect ratio of the input stream.

const width = 320; // We will scale the photo width to this
let height = 0; // This will be computed based on the input stream

// |streaming| indicates whether or not we're currently streaming
// video from the camera. Obviously, we start at false.

let streaming = false;

// The various HTML elements we need to configure or control. These
// will be set by the startup() function.

let video = null;
let canvas = null;
let photo = null;
let photo_img = null;
let startButton = null;
let camera_open = false;
let imageCapture = null;
let wscli = null;
let user_id = null;
let messages = null;
let ui_errormsg = null;
let gloc = [{
    "accuracy": -1,
    "latitude": -1,
    "longitude": -1,
    "altitude": -1,
    "altitudeAccuracy": -1,
    "heading": null,
    "speed": null,
    'timestamp': -1
}]
let geolocwatchid = null;

function geo_success(position) {
    cords = position.coords

    gloc.push({
        "accuracy": cords.accuracy,
        "latitude": cords.latitude,
        "longitude": cords.longitude,
        "altitude": cords.altitude,
        "altitudeAccuracy": cords.altitudeAccuracy,
        "heading": cords.heading,
        "speed": cords.speed,
        'timestamp': position.timestamp
    })

    if (gloc.length > 3) {
        gloc.pop()
    }

}

function geo_error() {
    log_message("Sorry, no position available.");
}

const geo_options = {
    enableHighAccuracy: true,
    maximumAge: 30000,
    timeout: 27000,
};


function startWsClient(user_id) {
    return new Promise((resolve, reject) => {
        if (wscli != null && wscli.readyState === WebSocket.OPEN) {
            resolve("done")
            return;
        }
        ws = new WebSocket("ws://" + document.location.host + "/bertws/" + user_id);
        ws.onmessage = function (event) {
            log_message(event.data)
        };
        ws.onopen = () => {
            console.log("WebSocket is connected.");
            wscli = ws
            resolve(ws); // Resolve the promise when the WebSocket is ready.
        };

        ws.onerror = (error) => {
            wscli = null
            reject(new Error("WebSocket connection error: " + error.message));
        };
    });

}

function log_message(text_msg) {
    var message = document.createElement('li')
    var content = document.createTextNode(text_msg)
    message.appendChild(content)
    messages.appendChild(message)
}
function sendPdu(pdu_type, user_id_str, callbackfn) {

    startWsClient(user_id_str).then((ws) => {
        req = {
            'type': pdu_type,
            'geolocation': gloc[gloc.length - 1],
            'image': Array.from(new Uint8Array(photo_img)),
            'width': canvas.width,
            'height': canvas.height
        }
        wscli.send(JSON.stringify(req))
        callbackfn()

    }).catch((err) => {
        ui_errormsg.textContent = err
    });

}
function send_register() {
    if (user_id.value.trim() === "") {
        ui_errormsg.textContent = "Error: Please enter User Id"
        return
    }
    if (photo_img == null) {
        ui_errormsg.textContent = "Please take photo before register"
        return
    }
    ui_errormsg.textContent = ""
    sendPdu('register', user_id.value.trim(), () => {
        clearPhoto()
        user_id.disabled = true
        document.getElementById("chkin_btn").disabled = false
    }
    )

}
function send_checkin() {
    if (photo_img == null) {
        ui_errormsg.textContent = "Please take photo before check-in"
        return
    }
    sendPdu('checkin', user_id.value.trim(), () => {
        clearPhoto()
    }
    )
}


function showViewLiveResultButton() {
    if (window.self !== window.top) {
        // Ensure that if our document is in a frame, we get the user
        // to first open it in its own tab or window. Otherwise, it
        // won't be able to request permission for camera access.
        document.querySelector(".content-area").remove();
        const button = document.createElement("button");
        button.textContent = "View live result of the example code above";
        document.body.append(button);
        button.addEventListener("click", () => window.open(location.href));
        return true;
    }
    return false;
}

function stop_camera() {
    video.srcObject.getTracks().forEach(function (track) {
        track.stop();
    });
    imageCapture = null;
    camera_open = false
}
function open_camera() {
    if (camera_open == false) {
        navigator.mediaDevices
            .getUserMedia({ video: true, audio: false })
            .then((stream) => {
                video.srcObject = stream;
                video.play();
            })
            .catch((err) => {
                console.error(`An error occurred: ${err}`);
            });
        camera_open = true
    }
}
function startup() {
    console.log("Startup fired ...")
    if (showViewLiveResultButton()) {
        alert('Camera not accessible...')
        return;
    }
    if ('geolocation' in navigator) {
        geolocwatchid = navigator.geolocation.watchPosition(geo_success, geo_error, geo_options);
        console.log("Geo location service activated ..")
    } else {
        console.log('Geolocation service not available ')
    }
    ui_errormsg = document.getElementById('ui_errors')
    messages = document.getElementById('messages')
    user_id = document.getElementById("user_id")
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    photo = document.getElementById("photo");
    startButton = document.getElementById("start-button");
    ctButton = document.getElementById("camera-button");
    stopButton = document.getElementById("stop-button")
    stopButton.addEventListener(
        "click",
        (ev) => {
            stop_camera()
            ev.preventDefault()
        }
    )


    video.addEventListener(
        "canplay",
        (ev) => {
            if (!streaming) {
                height = video.videoHeight / (video.videoWidth / width);

                // Firefox currently has a bug where the height can't be read from
                // the video, so we will make assumptions if this happens.

                if (isNaN(height)) {
                    height = width / (4 / 3);
                }

                video.setAttribute("width", width);
                video.setAttribute("height", height);
                canvas.setAttribute("width", width);
                canvas.setAttribute("height", height);
                streaming = true;
            }
        },
        false,
    );

    startButton.addEventListener(
        "click",
        (ev) => {
            takePicture();
            stop_camera();
            ev.preventDefault();
        },
        false,
    );
    ctButton.addEventListener(
        "click", (ev) => {
            open_camera()
            ev.preventDefault()
        }
    )

    clearPhoto();
}

// Fill the photo with an indication that none has been
// captured.

function clearPhoto() {
    const context = canvas.getContext("2d");
    context.fillStyle = "#AAA";
    context.fillRect(0, 0, canvas.width, canvas.height);

    const data = canvas.toDataURL("image/png");
    photo.setAttribute("src", data);

    photo_img = null
}

// Capture a photo by fetching the current contents of the video
// and drawing it into a canvas, then converting that to a PNG
// format data URL. By drawing it on an offscreen canvas and then
// drawing that to the screen, we can change its size and/or apply
// other changes before drawing it.

function takePicture() {
    const context = canvas.getContext("2d");
    if (width && height) {
        canvas.width = width;
        canvas.height = height;
        context.drawImage(video, 0, 0, width, height);

        //const data = canvas.toDataURL("image/jpeg", 1.0);
        //console.log(data)
        //photo_img = data
        //console.log(photo_img)
        //photo.setAttribute("src", data);
        canvas.toBlob(async (blob) => {
            photo_img = await blob.arrayBuffer();
            const url = URL.createObjectURL(blob);

            photo.onload = () => {
                // no longer need to read the blob so it's revoked
                URL.revokeObjectURL(url);
            };

            photo.setAttribute("src", url);

        }, "image/jpeg", 1.0);

    } else {
        clearPhoto();
    }
}

// Set up our event listener to run the startup process
// once loading is complete.
window.addEventListener("load", startup, false);
window.addEventListener("unload", (ev) => {
    if (geolocwatchid != null && 'geolocation' in navigator) {
        navigator.geolocation.clearWatch(geolocwatchid)
        console.log(" location watcher is cleared ")
    }

}, false)



