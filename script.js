let prompt = document.querySelector("#prompt");
let submit = document.querySelector("#submit");
let chatcontainer = document.querySelector(".chat-container");
let imagebtn = document.querySelector("#image");
let imageContainer = document.querySelector("#documentBox");
let imageinput = document.querySelector("#image input");

let userCharArr = [];

let user = {
  message: null,
  file: {
    mime_type: null,
    data: null,
  },
};

//  Create chat box
function createChatBox(html, classes) {
  let div = document.createElement("div");
  div.innerHTML = html;
  div.classList.add(classes);
  return div;
}

//  Fetch answer from backend
async function getAnswerFromBackend(message) {
  try {
    let user = sessionStorage.getItem("User");
    let isAdmin = sessionStorage.getItem("isAdmin");

    let accNo = null;

    if (user) {
      user = JSON.parse(user);
      accNo = user.account;
    } else if (isAdmin) {
      accNo = ""; // Admin queries don't require acc_no
    } else {
      window.location.href = "login.html";
      return;
    }

    const res = await fetch("http://127.0.0.1:3000/get-answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: message, acc_no: accNo }),
    });

    const data = await res.json();
    return data.answer || "Sorry, I couldn't understand that.";
  } catch (err) {
    console.error("Error contacting backend:", err);
    return "Error connecting to the bot server.";
  }
}


//  Handle chat response
function handlechatResponse(message) {
  user.message = message;
  userCharArr.push({ type: "user", message });

  // Show user message
  const html = `
    <img src="user.jpg" alt="" class="userimage">
    <div class="user-chat-area">
      ${user.message}
      ${
        user.file.data
          ? `<img src="data:${user.file.mime_type};base64,${user.file.data}" class="chooseimg"/>`
          : ""
      }
    </div>`;
  prompt.value = "";
  let userchatBox = createChatBox(html, "user-chat-box");
  chatcontainer.appendChild(userchatBox);
  chatcontainer.scrollTo({
    top: chatcontainer.scrollHeight,
    behavior: "smooth",
  });

  // Bot thinking animation
  const loadingHtml = `
    <img src="bot.png" alt="" id="aiimage">
    <div class="ai-chat-area">
      <img src="loading.gif" alt="" class="load" width="50px">
    </div>`;
  let aichatbox = createChatBox(loadingHtml, "ai-chat-box");
  chatcontainer.appendChild(aichatbox);

  // Get response from backend
  getAnswerFromBackend(user.message).then((response) => {
    aichatbox.innerHTML = `
        <img src="bot.png" alt="" id="aiimage">
        <div class="ai-chat-area">${response}</div>`;
    userCharArr.push({ type: "bot", message: response });
    chatcontainer.scrollTo({
      top: chatcontainer.scrollHeight,
      behavior: "smooth",
    });
  });

  image.src = "";
  imageContainer.classList.add("document-hidden-box");
  imageContainer.classList.remove("document-show-box");
}

//  Event bindings
document.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && prompt.value.trim() !== "") {
    handlechatResponse(prompt.value.trim());
  }
});

submit.addEventListener("click", () => {
  if (prompt.value.trim()) {
    handlechatResponse(prompt.value.trim());
  }
});

//  File upload
imageinput.addEventListener("change", () => {
  const file = imageinput.files[0];
  if (!file) return;
  let reader = new FileReader();
  reader.onload = (e) => {
    let base64string = e.target.result.split(",")[1];
    user.file = {
      mime_type: file.type,
      data: base64string,
    };
    imageContainer.classList.remove("document-hidden-box");
    imageContainer.classList.add("document-show-box");

    // Show image preview
    if (file.type.includes("image/")) {
      const image = document.createElement("img");
      image.height = 50;
      image.width = 50;
      image.src = `data:${user.file.mime_type};base64,${user.file.data}`;
      image.classList.add("choose", "uploaded-img");
      image.id = "uploaded-img";
      imageContainer.append(image);
    } else {
      const object = document.createElement("object");
      object.data = `data:${user.file.mime_type};base64,${user.file.data}`;
      object.type = user.file.mime_type;
      imageContainer.append(object);
    }
  };
  reader.readAsDataURL(file);
});

//  File picker
imagebtn.addEventListener("click", () => {
  imagebtn.querySelector("input").click();
});

// Debug
console.log("Chat History Array:", userCharArr);
sessionStorage.getItem("isAdmin", true);
function fetchClient() {
  const chatBox = document.querySelector(".ai-chat-area");
  chatBox.innerHTML += "<br/>🔍 Fetching client details...";
    chatBox.innerHTML += "<br/>Please enter Clients account Number";

}

function checkBalance() {
  const chatBox = document.querySelector(".ai-chat-area");
  chatBox.innerHTML += "<br/>💰 Checking balance...";
    chatBox.innerHTML += "<br/>Please Enter the client details to check balance";

}

function viewTransactions() {
  const chatBox = document.querySelector(".ai-chat-area");
  chatBox.innerHTML += "<br/>📄 Viewing transactions...";
    chatBox.innerHTML += "<br/>Add client account number to check past transactions";

}

function clearChat() {
  const chatBox = document.querySelector(".ai-chat-area");
  chatBox.innerHTML = "Chat cleared.<br/>";
}

function logoutAdmin() {
  alert("Logging out...");
  window.location.href = "login.html"; // Adjust if needed
}
// Update this function to handle button clicks and send to backend
function handleAdminButtonClick(queryText) {
  const accNo = prompt("Enter account number:");

  if (!accNo) {
    alert("Account number is required.");
    return;
  }

  fetch("http://localhost:3000/get-answer", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: queryText,
      acc_no: accNo,
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      const aiBox = document.querySelector(".ai-chat-area");
      aiBox.innerHTML += `<br><strong>Bot:</strong> ${data.answer}`;
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
