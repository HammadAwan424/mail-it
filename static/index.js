document.addEventListener("DOMContentLoaded", function () {
  //Turns on autocomplete on SearchBar (func defined below)
  mailField = document.getElementById("searchbar");
  autoComplete(
    (url = `/autocomplete/mails`),
    (field = document.getElementById("searchbar")),
    (outputDest = mailField
      .closest(".search_bar")
      .querySelector(".search-result"))
  );

  //Turns on little UI interaction on navbar (child of sidebar) for Desktop (func defined below)
  navDeskActivate(".navv");

  //Manages checkboxes (class defined below)
  const checkboxManager = new checkbox();
  checkboxManager.children = "td .form-check-input";
  checkboxManager.parent = "#all-checkboxes";
  checkboxManager.activate();

  //Manages new pages desktop-only (func requestPage defined below)
  document
    .querySelector(".page-nav")
    .addEventListener("click", function (event) {
      if (event.target == this.querySelector("#next"))
        requestPage(event.target, "#previous", 1, checkboxManager);
      else if (event.target == this.querySelector("#previous"))
        requestPage(event.target, "#next", -1, checkboxManager);
    });

  //Loads the Form for desktop to send mail (func defined below)
  let composeBtn = document.querySelector(".sidebar-desk .compose-btn");
  composeBtn.addEventListener("click", renderComposeForm);

  //Set up trash icons to send mail-delete requests with corresponding id (func defined below)
  mailDeleter(".third");

  //Activates Sidebar for mobile (func defined below)
  activateMobSidebar(".search_bar > .bubble-menu", ".sidebar-mob");

  //Takes json data, parses it, and render when it was received (func defined below)
  let jsonMailData = document.getElementById("jsonContainer").dataset.json;
  let mails = JSON.parse(jsonMailData).mails;
  dateManager(mails);

  //Plays an animation for mobile devices when mail is selected (func defined below)
  mailSelectAnimation()

  //Makes a mail read (unbold) when clicked, simulating it is read by user
  document.querySelectorAll("tr > .sixth").forEach(function (tr) {
    tr.addEventListener("click", async function () {
      let id = this.closest("tr").dataset.mailId;
      let response = fetch(`/read?mail_id=${id}`);
    });
  });

  document.querySelector(".sidebar-desk").classList.toggle("animate"); //Makes expanded-sidebar by-default

  // Activates Sidebar for Desktop
  document.getElementById("hamburger").addEventListener("click", function () {
    document.querySelector(".sidebar-desk").classList.toggle("animate");
  });

});



















//Toggles active class on Nav bar, takes a <ul> tag selector which contains nav (currently Desktop only)
function navDeskActivate(selector) {
  document.querySelector(selector).addEventListener("click", function (e) {
    let li = e.target.closest("li");
    li.classList.add("active");
    list = this.querySelectorAll("li");
    this.querySelectorAll("li").forEach((element) => {
      if (element != li) {
        element.classList.remove("active");
      }
    });
  });
}


//Makes it a little bit easier to Do POST requests
async function POST(url, body) {
  options = {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  };
  return await fetch(url, (options = options));
}


//Takes url and Input field to capture data and render HTML to outputDest
function autoComplete(url, field, outputDest) {
  field.addEventListener("input", async function () {
    value = field.value.trim();
    if (!value) {
      makeEmpty(outputDest);
      return;
    }
    let response = await fetch(`${url}/${value}`);
    response.text().then((val) => {
      makeEmpty(outputDest);
      outputDest.innerHTML = val;
    });
  });
}


//Removes all child nodes of a given HTML element
function makeEmpty(element) {
  if (!element.hasChildNodes) {
    return;
  }
  while (element.firstChild) {
    element.removeChild(element.lastChild);
  }
}


function mailDeleter(trashIconsSelector) {
  let trash_icons = document.querySelectorAll(trashIconsSelector);

  for (let icon of trash_icons) {
    icon.addEventListener("click", function () {
      let tr = this.closest("tr");
      tr.querySelector(".side").classList.remove("side");
      tr.classList.add("delete");
      let mail_id = tr.dataset.mailId;
      POST("/delete", { mail_id: mail_id }).then((res) => {
        if (res.status == 200) {
        }
      });
    });
  }
}


//Takes mails object and renders dates acc to browser Timezone
function dateManager(mails) {
  let dateElems = document.querySelectorAll(".menu > .date");
  const currentDate = new Date();

  for (let i = 0; i < mails.length; i++) {
    let date = new Date(`${mails[i].date}T${mails[i].time}Z`);

    let delta = (currentDate - date) / (1000 * 60); // stores minutes in delta
    if (delta < 1) {
      dateElems[i].innerHTML = `Just now`;
    } else if (delta < 60) {
      dateElems[i].innerHTML = `${Math.floor(delta)}mins`;
    } else if (delta < 1400) {
      dateElems[i].innerHTML = `${Math.floor(delta / 60)}hours`;
    } else {
      dateElems[i].innerHTML = date.toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
      });
    }
  }
}


// Side bar activation for mobile
function activateMobSidebar(toggleBtn, sidebar) {
  document.querySelector(toggleBtn).addEventListener("click", function () {
    let bar = document.querySelector(sidebar);
    bar.classList.add("sidebar-toggle");
    window.setTimeout(function () {
      window.onclick = (pointer) => {
        if (pointer.clientX > bar.getBoundingClientRect().right) {
          console.log("You clicked right to the sidebar");
          bar.classList.remove("sidebar-toggle");
          window.onclick = null;
        }
      };
    }, 100);
  });
}


//Manages checkboxes and their count, set two properties (children and parent) and call activate()
class checkbox {
  constructor() {}
  set children(cssSelector) {
    this.childCheckboxes = document.querySelectorAll(cssSelector);
  }
  set parent(cssSelector) {
    this.parentCheckbox = document.querySelector(cssSelector);
  }

  activate() {
    this.activateChildren();
    this.activateParent();
  }
  activateParent() {
    // array of children checkboxes
    let array = this.childCheckboxes;
    if (array.length < 0) {
      return;
    }
    this.parentCheckbox.addEventListener("change", function () {
      if (this.checked) {
        array.forEach(function (box) {
          if (!box.checked) {
            box.click();
          }
        });
      } else {
        array.forEach(function (box) {
          box.click();
        });
      }
    });
  }
  activateChildren() {
    let obj = this;
    let array = obj.childCheckboxes;
    let num = 0;
    for (let i = 0; i < array.length; i++) {
      array[i].addEventListener("change", function () {
        array[i].closest("tr").classList.toggle("selection");
        if (array[i].checked) {
          num += 1;
        } else {
          num -= 1;
        }
        obj.counter(num, obj);
      });
    }
  }
  counter(num, obj) {
    // checked checkboxes num and max number of checkboxex
    let max = obj.childCheckboxes.length;
    if (num == 0) {
      document.querySelector(".topbar > .onselection").classList.add("hidden");
      obj.parentCheckbox.checked = false;
      return;
    }
    if (num > 0) {
      document
        .querySelector(".topbar > .onselection")
        .classList.remove("hidden");
      document.querySelector(
        ".onselection .rect"
      ).innerHTML = `${num} items selected`;
    }
    if (num == max) {
      obj.parentCheckbox.checked = true;
    } else {
      obj.parentCheckbox.checked = false;
    }
  }
}


//Renders mails for new page, changes state about Page info at top right 'x-x of x'
async function requestPage(
  activeNav,
  sideSelector,
  requestedPage,
  checkboxObj
) {
  let secondaryNav = null;
  let clickedNav = activeNav.dataset;

  if (clickedNav.page == 0) {
    alert("You are already at first page");
    return;
  }

  let response = await fetch(`/api/page/${clickedNav.page}`);
  if (response.status != 200) {
    alert("No more pages");
    return;
  }

  if (requestedPage > 0) {
    secondaryNav = document.querySelector(sideSelector).dataset;
  } else {
    secondaryNav = document.querySelector(sideSelector).dataset;
  }

  children = document.querySelectorAll("tr");
  children.forEach(function (child) {
    child.remove();
  });

  //json containing mails data and template data
  let json = await response.json();
  document.querySelector("tbody").innerHTML = json["template"];

  let unique = (Number(clickedNav.page) - 1) * json.mails.perPage;
  let from = unique + 1;
  let to = unique + json.mails.count;

  document.querySelector(
    ".page > .rect"
  ).innerHTML = `${from}-${to} of ${json.mails.total}`;
  clickedNav.page = Number(clickedNav.page) + requestedPage;
  secondaryNav.page = Number(secondaryNav.page) + requestedPage;

  checkboxObj.parent = "#all-checkboxes";
  checkboxObj.children = "td .form-check-input";
  checkboxObj.activate();

  dateManager(json["mails"]["mails"]);
  console.log(json);
}


function innerHTML(selector) {
  return document.querySelector(selector).value;
}


//On clicking compose btn, form is returned for sending mails
function renderComposeForm() {
  if (document.querySelector(".compose-area")) {
    return;
  }
  let composeForm = document.createElement("form");

  composeForm.classList.add("no-mobile", "compose-area");
  composeForm.id = "composeForm";
  let html = `
  <div class="ca-menu fw-bold light">
      <span class="m0">New Message</span>
      <div class="c-cross small">X</div>
  </div>
  <span class="light">To</span>
  <div id="receiver">
      <div class="recepient">
          <input id="userSearch" class="light input" placeholder="Recepient" name="receiver" type="text" required autocomplete="off" autofocus>
          <div id="userSearchResult">
          </div>
      </div>
  </div>
  <input placeholder="Subject" class="light" type="text" name="subject" required autocomplete="off">
  <textarea placeholder="Message" class="small light" required name="message"></textarea>
  <button class="send light">Send</button>
    `;
  composeForm.innerHTML = html;

  document.querySelector(".grid").appendChild(composeForm);

  let close = composeForm.querySelector(".c-cross");
  close.addEventListener("click", function () {
    composeForm.remove();
  });

  composeForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    let data = {
      receiver: innerHTML("input[placeholder='Recepient']"),
      subject: innerHTML("input[placeholder='Subject']"),
      message: innerHTML("textarea[placeholder='Message']"),
    };
    close.click();
    res = await POST("/send", data);
    if (res.status == 200) {
      alert("Your message has been sent successfully");
    }
  });

  autoComplete(
    (url = "/autocomplete/username"),
    (field = document.getElementById("userSearch")),
    (outputDest = document.getElementById("userSearchResult"))
  );
}


//Animation when a mail is clicked and hold
function mailSelectAnimation() {
  let timeout;
  console.log("ready");

  for (let tr of document.querySelectorAll("tr")) {
    tr.addEventListener("mousedown", function () {
      console.log("detected hold,");
      timeout = setTimeout(function () {
        console.log("The animation should play");
        tr.querySelector(".bubble-sender").classList.add("bubble-animate");
        tr.querySelector(".bubble-sender").addEventListener(
          "click",
          function () {
            this.classList.remove("bubble-animate");
          }
        );
      }, 500);
      console.log(`timer set as ${timeout}`);
    });
  }

  window.addEventListener("mouseup", function () {
    console.log("detected up");
    clearTimeout(timeout);
    console.log("timer cleard");
  });
}