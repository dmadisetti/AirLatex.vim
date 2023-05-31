console.log("AirLatex loaded")
browser.runtime.onMessage.addListener(request => {
  console.log(request);
  if (request.scroll) {
    height = document.querySelector(".pdfViewer").clientHeight;
    height *= request.scroll;
    height |= 0
    document.querySelector(".pdfjs-viewer-inner").scrollTo({top: height})
  }
});
