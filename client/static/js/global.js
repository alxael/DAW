$(window).on("load", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerElement) {
    return new bootstrap.Tooltip(tooltipTriggerElement);
  });
});

const cleanUpFormErrors = () => {
  $("div.invalid-feedback").remove();
  $("#response-error").remove();
  $(".is-invalid").each(function () {
    $(this).removeClass("is-invalid");
  });
};

const showFormErrors = (errors, responsePromptParent) => {
  for (const field in errors) {
    const fieldErrors = errors[field];
    const errorMessages = $("<div></div>")
      .text(fieldErrors.join(" "))
      .addClass("invalid-feedback");
    const fieldElement = $(`#id_${field}`);
    fieldElement.addClass("is-invalid");
    fieldElement.parent().append(errorMessages);
  }
  if (errors["__all__"]) {
    const errorMessagesAlert = $("<div></div>")
      .text(errors["__all__"].join(" "))
      .attr("id", "response-error")
      .addClass("alert alert-danger mt-3");
    responsePromptParent.append(errorMessagesAlert);
  }
};

const clearForm = (formId, selectFields, hasProseEditor) => {
  $(`#${formId}`).trigger("reset");
  if (selectFields) {
    for (const selectField of selectFields)
      $(`#id_${selectField}`).val(null).trigger("change");
  }
  if (hasProseEditor) $(".ProseMirror").empty();
};

const createConfirmDeleteModal = (id, title, text) => {
  const modal = $("<div></div>")
    .addClass("modal fade")
    .attr("tabindex", -1)
    .attr("id", id);
  const modalDialog = $("<div></div>").addClass(
    "modal-dialog modal-dialog-centered"
  );
  const modalContent = $("<div></div>").addClass("modal-content");

  const modalHeader = $("<div></div>").addClass("modal-header");
  const modalTitle = $("<h3></h3>").addClass("modal-title").text(title);
  modalHeader.append(modalTitle);

  const modalBody = $("<div></div>").addClass("modal-body").text(text);

  const modalFooter = $("<div></div>").addClass("modal-footer");
  const modalCloseButton = $("<button></button>")
    .addClass("btn btn-primary")
    .text("Close")
    .attr("data-bs-dismiss", "modal");
  const modalConfirmButton = $("<button></button>")
    .addClass("btn btn-outline-danger")
    .text("Confirm")
    .attr("data-bs-dismiss", "modal")
    .attr("id", id + "-button");

  modalFooter.append(modalCloseButton);
  modalFooter.append(modalConfirmButton);

  modalContent.append(modalHeader);
  modalContent.append(modalBody);
  modalContent.append(modalFooter);

  modalDialog.append(modalContent);
  modal.append(modalDialog);

  $("body").append(modal);
};

const pageNumberDefault = 1;
let pageNumber = pageNumberDefault;

const recordsPerPageDefault = 10;
let recordsPerPage = recordsPerPageDefault;

const setPaginationPageNumbers = (requestFunction, pages) => {
  const pageNumbersNav = $("<nav></nav>");
  const pageNumbers = $("<ul></ul>").addClass("pagination");
  for (const pageLabel of pages) {
    const pageNumberButton = $("<li></li>").addClass("page-item");
    const pageLink = $("<a></a>").addClass("page-link").text(pageLabel);

    if (pageLabel == pageNumber) {
      pageNumberButton.addClass("active");
    }
    if (pageLabel == "…") {
      pageNumberButton.addClass("disabled");
    } else {
      pageLink.bind("click", function () {
        pageNumber = parseInt($(this).text());
        requestFunction();
      });
    }
    pageNumberButton.append(pageLink);
    pageNumbers.append(pageNumberButton);
  }
  pageNumbersNav.append(pageNumbers);

  $("#page_number").empty();
  $("#page_number").append(pageNumbersNav);
};

const setPaginationRecordsPerPage = (requestFunction) => {
  $(document).ready(function () {
    $("#records_per_page").on("change", function () {
      recordsPerPage = parseInt(this.value);
      pageNumber = pageNumberDefault;
      requestFunction();
    });
  });
};

const resetPagination = () => {
  pageNumber = pageNumberDefault;
  recordsPerPage = recordsPerPageDefault;
};

const addToCart = () => {
  console.log("Added to cart!");
};
