async function signin() {
  const formElement = document.forms["sign-in-form"];
  const formData = new FormData(formElement);
  const response = await fetchData("POST", signInUrl, formData);

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
  const response = await fetchData("POST", signUpUrl, formData);

  if (response.success) {
    $(window).scrollTop();
    $("#background").empty();
    const successCard = $("<div></div>").addClass(
      "card p-3 text-white text-bg-success mt-5"
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
  const response = await fetchData("POST", changePasswordUrl, formData);

  if (response.success) {
    // replace with toast
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
    const offerUuids = getCartOfferUuids();
    localStorage.removeItem("cartItemsCount");
    for (const offerUuid of offerUuids) {
      localStorage.removeItem(offerUuid);
    }

    window.location.href = signInUrl;
  } else {
    // replace with toast
  }
}
