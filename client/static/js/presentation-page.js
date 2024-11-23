async function contact() {
  const formElement = document.forms.contactForm;
  const formData = new FormData(formElement);

  const response = await fetch(indexUrl, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  console.log(response);
  if (response.success) {
    const message = $("<h4></h4>")
      .text(
        "Thank you for reaching out to us! We will respond in due time to your inquiry."
      )
      .addClass("form-completed text-center");
    $("#contact-section").empty();
    $("#contact-section").append(message);
  } else {
    $("div.invalid-feedback").remove();
    $("div.alert").remove();
    $(".is-invalid").each((element) => {
      $(element).removeClass("is-invalid");
    });

    for (const field in response.errors) {
      const errors = response.errors[field];
      const errorMessages = $("<div></div>")
        .text(errors.join(" "))
        .addClass("invalid-feedback");
      const fieldElement = $(`#id_${field}`);
      fieldElement.addClass("is-invalid");
      fieldElement.parent().append(errorMessages);
    }
    if (response.errors["__all__"]) {
      const errorMessagesAlert = $("<div></div>")
        .text(response.errors["__all__"].join(" "))
        .addClass("alert alert-danger mt-3");
      $("#submit-button").parent().append(errorMessagesAlert);
    }
  }

  return true;
}
