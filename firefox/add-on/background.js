// background.js
let pairs = {};

browser.runtime.onMessage.addListener(function(message, sender, sendResponse) {
  console.log(message)
  if (message.type == "pair") {
    console.log("yes pair...")
    if (!pairs[message.id]){
      pairs[message.id] = {}
    }
    let paired = pairs[message.id];
    paired[message.role] = sender.tab.id;
    console.log(paired);
    if (Object.keys(paired).length == 2) {
      let port = browser.runtime.connectNative("airlatex");
      console.log("ping:", paired);
      port.onMessage.addListener((response) => {
        // Send the response to the paired tab
        let data = response.split(",")
        console.log("server:", response, paired);
        console.log(Object.keys(paired).length == 2, message.id == data[0])
        console.log(message.id, data[0])
        if (Object.keys(paired).length == 2 && message.id == data[0]) {
          console.log("server:", response, paired);
          browser.tabs.sendMessage(
            paired["detacher"],
            {
            changed: data[1] | 0,
            data: {
              file:data[2],
              line:data[3] | 0,
              column: data[4] | 0
            }});
        }
      });
    }
  }
});
