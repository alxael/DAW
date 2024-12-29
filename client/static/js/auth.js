async function signin() {
  const formElement = document.forms["sign-in-form"];
  const formData = new FormData(formElement);

  const response = await fetch(signInUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  cleanUpFormErrors();
  clearForm("sign-in-form", [], false);
  if (response.success) {
    window.location.href = profileUrl;
  } else {
    showFormErrors(response.errors, $("#submit-button").parent());
  }
  return true;
}

async function signup() {
  const formElement = document.forms["sign-up-form"];
  const formData = new FormData(formElement);

  const response = await fetch(signUpUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  if (response.success) {
    $(window).scrollTop();
    $("#background").empty();
    const successCard = $("<div></div>").addClass(
      "card p-3 text-white bg-success"
    );

    const body = $("<div></div>").addClass("card-body");
    const title = $("<h4></h4>")
      .addClass("card-title")
      .text("Account created!");

    const content = $("<p></p>")
      .addClass("card-text")
      .text(
        "You have successfully created your account! After you confirm your email you may sign in on the "
      );
    const signInLinkText = $("<a></a>")
      .text("sign in page.")
      .attr("href", signInUrl)
      .addClass("link-light");
    content.append(signInLinkText);

    body.append(title);
    body.append(content);

    successCard.append(body);
    $("#background").append(successCard);
  } else {
    cleanUpFormErrors();
    showFormErrors(response.errors, $("#submit-button").parent());
  }
  return true;
}

async function changePassword() {
  const formElement = document.forms["change-password-form"];
  const formData = new FormData(formElement);

  const response = await fetch(changePasswordUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  if (response.success) {
    // show message in profile page
    window.location.href = profileUrl;
  } else {
    cleanUpFormErrors();
    console.log(response);
    showFormErrors(response.errors, $("#submit-button").parent());
  }
}

async function signout() {
  const response = await fetch(signOutUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
  });
  if (response.status === 200) {
    window.location.href = signInUrl;
  } else {
    console.log("Failed!"); // to be replaced
  }
}
