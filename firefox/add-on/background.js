// background.js
let port = browser.runtime.connectNative("airlatex");
let pairedTabId = null;

port.onMessage.addListener((response) => {
  // Send the response to the paired tab
  if (pairedTabId !== null) {
    console.log(response, pairedTabId);
    browser.tabs.sendMessage(pairedTabId, {scroll: parseFloat(response)});
  }
});

browser.browserAction.onClicked.addListener((tab) => {
  console.log("Sending:  ping");
  // Pair with the current tab
  pairedTabId = tab.id;
  port.postMessage("ping");
});
