async function contact() {
  const formElement = document.forms.contactForm;
  const formData = new FormData(formElement);
  const response = await fetchData("POST", indexUrl, formData);

  if (response.success) {
    const message = $("<h4></h4>")
      .text(
        "Thank you for reaching out to us! We will respond in due time to your inquiry."
      )
      .addClass("form-completed text-center");
    $("#contact-section").empty();
    $("#contact-section").append(message);
  } else {
    cleanUpFormErrors();
    showFormErrors(response.errors, $("#submit-button").parent());
  }

  return true;
}
