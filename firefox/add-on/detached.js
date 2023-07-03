let project_id = document.querySelector("meta[name=ol-project_id]").content;
let active = false;

// We set this to prevent programatic closing on reattach?
window.close = ()=>{}

const detachChannelId = `detach-${project_id}`
const channel = new BroadcastChannel(detachChannelId);
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

let buttonMaker = (text)=>{
  let button = document.createElement("button");
  button.type = "button";
  button.classList ="split-menu-button no-left-radius btn btn-primary";
  button.innerHTML = `
    <i aria-hidden="true" class="fa split-menu-icon"></i>
    <span class="split-menu-button">${text}</span>
  `;
  return button;
}

//
channel.onmessage = (message)=>{
  console.log(message)
  if (message.data.event == "action-firstRenderDone") {
    if (document.querySelector(".split-menu").id != "airlatex") {
      let dark = buttonMaker("");
      dark.onclick = function(){
         if (document.body.style.length == 0) {
           document.body.style = 'filter: grayscale(1) invert(1) sepia(0.5) contrast(75%)';
          } else {
           document.body.style = '';
          }
      };
      let title = buttonMaker("AirLatex");
      // Allows us to repair if we need.
      title.onclick = function(){
        browser.runtime.sendMessage({type: "pair", role: "detached", id: project_id});
      }
      document.querySelector(".split-menu").prepend(title, dark)
      document.querySelector(".split-menu").id = "airlatex"
    }
    browser.runtime.sendMessage({type: "pair", role: "detached", id: project_id});
    if (active) {
      button.remove();
    }
  }
}

let button = document.createElement('div');
button.className = "toolbar-pdf-right"
button.innerHTML = `
<button
  aria-label="Pair Neovim Plugin"
  type="button"
  class="btn-secondary btn btn-xs"
  style="float:right;position:absolute;top:0">
    <span>&nbsp;Pair AirLatex</span>
</button>`;
button.onclick = ()=>{
  active = true;
  channel.postMessage({role: "detacher", event: "closed"})
  let iframe = document.createElement('iframe');
  iframe.src = `/project/${project_id}/detacher?iframe=true`;
  document.body.appendChild(iframe)
}
document.body.appendChild(button);

browser.runtime.onMessage.addListener(request => {
  console.log("Triggering")

  // TODO: Fix compilation trigger.
  // Trigger Compilation
  // Compiles once and breaks.
  // window.broadcastEvent("detached", "action-startCompile")

  // Create a new KeyboardEvent
  // Dispatch the event on the iframe's window
  // Also compiles once and breaks.
});
