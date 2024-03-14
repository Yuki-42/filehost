function updateQuality() {
    const qualitySelector = document.getElementById("quality");
    const selectedQuality = qualitySelector.options[qualitySelector.selectedIndex].value;

    const videoPlayer = document.getElementById("video");
    videoPlayer.src = "" + selectedQuality;  // TODO: Update the video source
}

function download(url) {
    const iframe = document.createElement("iframe");
    iframe.style.display = "none";

    iframe.src = url;
    document.body.appendChild(iframe);
}
