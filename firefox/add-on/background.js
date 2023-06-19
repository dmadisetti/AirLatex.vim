// background.js
let port = browser.runtime.connectNative("airlatex");
let paired = {};

port.onMessage.addListener((response) => {
  // Send the response to the paired tab
  let data = response.split(",")
  if (Object.keys(paired).length == 2) {
    console.log("server:", response, paired);
    browser.tabs.sendMessage(
      paired["detacher"],
      {file:data[0], line:data[1] | 0, column: data[2] | 0});
  }
  port.postMessage("pair");
});

browser.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  console.log(message)
  if (message.type == "pair") {
    paired[message.role] = sender.tab.id;
    if (Object.keys(paired).length == 2) {
      port.postMessage("pair");
    }
  }
});
