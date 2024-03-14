function updateQuality() {
    const qualitySelector = document.getElementById('quality');
    const selectedQuality = qualitySelector.options[qualitySelector.selectedIndex].value;

    const videoPlayer = document.getElementById('videoPlayer');
    videoPlayer.src = '' + selectedQuality;  // TODO: Update the video source
}
