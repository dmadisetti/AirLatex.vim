console.log("Loaded detacher")

let project_id = document.querySelector("meta[name=ol-project_id]").content;
window.broadcastEvent = (role, event, data) => {
  const message = {
    role: role,
    event: event,
    data: {args:[]}
  }
  if (data) {
    message.data = data
  }
  console.log(message)
  channel.postMessage(message)
}
const detachChannelId = `detach-${project_id}`
const channel = new BroadcastChannel(detachChannelId);
const enter = {
  key: "Enter",
  code: "Enter",
  keyCode: 13,
  ctrlKey: true,
  bubbles: true,
  cancelable: true
}
function move(params) {
  return fetch(`https://${window.location.hostname}/project/${project_id}/sync/code?${params}`).then(
    (response)=>{
      console.log(response);
      return response.json()
    }).then(
    (response)=>{
      window.broadcastEvent("detacher", "action-setHighlights", {args:[response["pdf"]]})
    })
}

console.log(new URLSearchParams(window.location.search).get("iframe"))
browser.runtime.sendMessage({type: "pair", role: "detacher", id:project_id});
// if (new URLSearchParams(window.location.search).get("iframe")) {
//}

browser.runtime.onMessage.addListener(request => {
  console.log("Triggering")
  let params = new URLSearchParams(request.data).toString();
  if (request.changed) {
    // Trigger Compilation
    document.querySelector(".editor").dispatchEvent(
      new KeyboardEvent("keydown", enter));
    document.querySelector(".editor").dispatchEvent(
      new KeyboardEvent("keyup", enter));

    // if (window.location != `https://${window.location.hostname}/project/${project_id}/detacher?iframe=true`) { }
    let active = false;
    channel.onmessage = (event) => {
      console.log(event);
      if(event.data.role == 'detacher' && event.data.event == 'state-position' && !active){
        console.log("Triggered");
        active = true;
        // reset default behavior
        channel.onmessage = console.log
        move(params)
      }
     }
    } else {
      move(params)
    }
});
