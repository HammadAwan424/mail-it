document.addEventListener("DOMContentLoaded", function () {
  let parent = document.getElementById("receiver")
  let dest = document.getElementById("usernames_result")
  parent.querySelector("input").addEventListener('input', async function() {
    value = this.value.trim()
    if (!value) {
      makeEmpty(dest)
      return
    }
    let response = await fetch(`/autocomplete/username/${value}`)
    response.text().then((val) => {
      makeEmpty(dest)
      dest.innerHTML = val
    })
  })


  //Manages autocomplete for search bar
  let input = document.getElementById("searchbar");
  input.addEventListener("input", async function () {
    value = input.value.trim()
    let destination = input.closest(".search_bar").querySelector(".search-result")
    if (!value) {
      makeEmpty(destination)
      return
    }
    let response = await fetch(`/autocomplete/${"mails"}/${value}`);
    response.text().then((val) => {
      makeEmpty(destination)
      destination.innerHTML  = val
    });
  });


  function navActivate(selector) {
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
  navActivate(".navv");

  document.querySelector(".sidebar-desk").classList.toggle("animate");

  async function request_page(activeNav, sideSelector, requestedPage) {
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

    checkboxManager.parent = "#all-checkboxes";
    checkboxManager.children = "td .form-check-input";
    checkboxManager.activate();

    dateManager(json["mails"]["mails"]);
    console.log(json);
  }
  document.querySelector(".page").addEventListener("click", function (event) {
    if (event.target == this.querySelector("#next"))
      request_page(event.target, "#previous", 1);
    else if (event.target == this.querySelector("#previous"))
      request_page(event.target, "#next", -1);
  });


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
        document
          .querySelector(".topbar > .onselection")
          .classList.add("hidden");
      }
      if (num > 0) {
        document
          .querySelector(".topbar > .onselection")
          .classList.remove("hidden");
        document.querySelector(
          ".onselection .rect"
        ).innerHTML = `${num} items selected`;
        if (num == max) {
          obj.parentCheckbox.checked = true;
        } else {
          obj.parentCheckbox.checked = false;
        }
      }
    }
  }
  const checkboxManager = new checkbox();
  checkboxManager.children = "td .form-check-input";
  checkboxManager.parent = "#all-checkboxes";
  checkboxManager.activate();


  function innerHTML(selector) {
    return document.querySelector(selector).value;
  }


  function renderComposePage() {
    if (document.querySelector(".compose-area")) {
      return;
    }
    let compose = document.createElement("div");
    compose.classList.add("no-mobile", "compose-area");
    let html = `
          <div class="ca-menu fw-bold light">
              <span class="m0">New Message</span>
              <div class="c-cross small">X</div>
          </div>
          <span class="light">To</span>
          <input placeholder="Recepient" class="light" name="receiver" type="text">
          <input placeholder="Subject" class="light" type="text" name="subject">
          <textarea placeholder="Message" class="small light" name="message"></textarea>
          <button class="send light">Send</button>
      `;
    compose.innerHTML = html;
    document.querySelector(".grid").appendChild(compose);

    compose.querySelector(".c-cross").addEventListener("click", function () {
      document.querySelector(".compose-area").remove();
    });
    compose.querySelector(".send").addEventListener("click", async function () {
      let data = {
        receiver: innerHTML("input[placeholder='Recepient']"),
        subject: innerHTML("input[placeholder='Subject']"),
        message: innerHTML("textarea[placeholder='Message']"),
      };
      res = await POST('/send', body=data)
      if (res.status == 200) {
        console.log("The message has been sent to the server")
      } 
    });
  }


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

  //Removes all child nodes of a given HTML element
  function makeEmpty(element) {
    if (!element.hasChildNodes) {
      return
    }
    while (element.firstChild) {
      element.removeChild(element.lastChild)
    }
  }


  //Compose page loader
  let composeBtn = document.querySelector(".sidebar-desk .compose-btn");
  composeBtn.addEventListener("click", renderComposePage);


  document.querySelectorAll("tr > .sixth").forEach(function (tr) {
    tr.addEventListener("click", async function () {
      let id = this.dataset.mailId;
      let response = fetch(`/read?mail_id=${id}`);
    });
  });


  (function deleter() {
    let trash_icons = document.getElementsByClassName("third");

    for (let icon of trash_icons) {
      icon.addEventListener("click", function () {
        let tr = this.closest("tr");
        tr.querySelector(".side").classList.remove("side");
        tr.classList.add("delete");
      });
    }
  })();


  /* PC */
  document
    .querySelector(".basic > .bubble")
    .addEventListener("click", function () {
      document.querySelector(".sidebar-desk").classList.toggle("animate");
    });


  // Mobile
  document
    .querySelector(".search_bar > .bubble-menu")
    .addEventListener("click", function () {
      let bar = document.querySelector(".sidebar-mob");
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


  let json_mails = document.getElementById("jsonContainer").dataset.json
  let mails = JSON.parse(json_mails).mails
  console.log(mails)
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
  dateManager(mails);
  let dateElems = document.querySelectorAll(".menu > .date");


  if (window.innerWidth < 768) {
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
});
