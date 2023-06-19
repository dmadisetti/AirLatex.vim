let project_id = document.querySelector("meta[name=ol-project_id]").content;
const detachChannelId = `detach-${project_id}`
const channel = new BroadcastChannel(detachChannelId);
channel.onmessage = console.log
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

let button = document.createElement('div');
button.className = "toolbar-pdf-right"
button.innerHTML = `
<button aria-label="Pair Neovim Plugin" type="button" class="synctex-control btn-secondary detach-synctex-control btn btn-xs" style="float:right;position:absolute;top:0">
  <span>&nbsp;Pair AirLatex</span>
</button>`;
button.onclick = ()=>{
  browser.runtime.sendMessage({type: "pair", role: "detached"});
  channel.postMessage({role: "detacher", event: "closed"})
  let iframe = document.createElement('iframe');
  iframe.src = `/project/${project_id}/detacher?iframe=true`;
  document.body.appendChild(iframe)
}
document.body.appendChild(button);

browser.runtime.onMessage.addListener(request => {
  let project_id = document.querySelector("meta[name=ol-project_id]").content;
  // Trigger Compilation
  // Compiles once and breaks.
  // window.broadcastEvent("detached", "action-startCompile")
  // Create a new KeyboardEvent
  // Dispatch the event on the iframe's window
  console.log("Triggering")
  // console.log("Triggering")
  document.querySelector(".pdf").dispatchEvent(
    new KeyboardEvent("keydown", {
      key: "Enter",
      code: "Enter",
      ctrlKey: true,
      bubbles: true,
      cancelable: true
    }));

  // Trigger highlight for position.
  // let params = new URLSearchParams(request).toString();
  // fetch(`https://${window.location.hostname}/project/${project_id}/sync/code?${params}`).then(
  //  (response)=>{
  //    console.log(response);
  //    return response.json()
  //  }).then(
  //  (response)=>{
  //    window.broadcastEvent("detacher", "action-setHighlights", {args:[response["pdf"]]})
  //  })
  // We need to wait for compilation to finish triggering, so we just listen for
  // what should be the last event.
  // let active = false;
  // channel.onmessage = (event) => {
  //   console.log(event);
  //   if(event.data.role == 'detacher' && event.data.event == 'state-position' && !active){
  //     active = true;
  //     // reset default behavior
  //     // channel.onmessage = console.log
  //     fetch(`https://${window.location.hostname}/project/${project_id}/sync/code?${params}`).then(
  //       (response)=>{
  //         console.log(response);
  //         return response.json()
  //       }).then(
  //       (response)=>{
  //         window.broadcastEvent("detacher", "action-setHighlights", {args:[response["pdf"]]})
  //       })
  //   }
  //  }
});
