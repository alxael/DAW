$(document).ready(function () {
  if (window.location.pathname === promotionListUrl) {
    filterPromotions();
    createConfirmDeleteModal(
      "delete-promotion-modal",
      "Delete promotion",
      "Are you sure you want to delete this promotion? After deletion, the promotion can not be restored!"
    );
    $("#delete-promotion-modal-button").on("click", async function () {
      const uuid = $(this).data("uuid");
      const response = await deletePromotion(uuid);
      if (response) {
        $(`#${uuid}`).remove();
        filterPromotions();
      }
    });
    setPaginationRecordsPerPage(filterPromotions);
  }
});

async function addPromotion() {
  const formElement = document.forms["add-promotion-form"];
  const formData = new FormData(formElement);

  const response = await fetch(window.location.href, {
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
  $("#response-success").remove();

  console.log(response);
  if (response.success) {
    clearForm("add-promotion-form", ["category"], true);

    const responseSuccessAlert = $("<div></div>")
      .text(
        "You have successfully created a promotion. To vizualize the promotion you created, go to the "
      )
      .attr("id", "response-success")
      .addClass("alert alert-success mt-3");
    const pageListLinkText = $("<a></a>")
      .text("promotion list page")
      .attr("href", promotionListUrl)
      .addClass("link-success");
    responseSuccessAlert.append(pageListLinkText);
    $("#add-promotion-form").parent().append(responseSuccessAlert);

    setTimeout(() => {
      $("#response-success").remove();
    }, 10000);
  } else {
    showFormErrors(response.errors, $("#add-promotion-form").parent());
  }
  return true;
}

async function editPromotion() {
  const formElement = document.forms["edit-promotion-form"];
  const formData = new FormData(formElement);

  const response = await fetch(window.location.href, {
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
  $("#response-success").remove();

  if (response.success) {
    const responseSuccessAlert = $("<div></div>")
      .text(
        "You have successfully edited the promotion. You may now return to the "
      )
      .attr("id", "response-success")
      .addClass("alert alert-success mt-3");
    const pageListLinkText = $("<a></a>")
      .text("promotion list page")
      .attr("href", promotionListUrl)
      .addClass("link-success");
    responseSuccessAlert.append(pageListLinkText);
    $("#edit-promotion-form").parent().append(responseSuccessAlert);

    setTimeout(() => {
      $("#response-success").remove();
    }, 10000);
  } else {
    showFormErrors(response.errors, $("#edit-promotion-form").parent());
  }
  return true;
}

async function deletePromotion(uuid) {
  const response = await fetch(promotionDeleteUrl.replace("uuid", uuid), {
    method: "DELETE",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
  }).then((data) => data.json());
  return response.success;
}

async function filterPromotions() {
  const formElement = document.forms["filter-form"];
  const formData = new FormData(formElement);

  let url = new URL(promotionListUrl, window.location.origin);
  url.searchParams.set("page_number", pageNumber);
  url.searchParams.set("records_per_page", recordsPerPage);

  const response = await fetch(url.toString(), {
    method: "POST",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      "X-Requested-With": "XMLHttpRequest",
      "X-CSRFToken": csrfToken,
    },
    body: formData,
  }).then((data) => data.json());

  $("#promotions-list").empty();
  if (response.success) {
    setPaginationPageNumbers(filterPromotions, response.pages);

    for (const promotion of response.promotions) {
      const promotionCard = $("<div></div>")
        .addClass("card promotion-card")
        .attr("id", promotion.uuid);

      const cardBody = $("<div></div>").addClass("card-body");

      const cardHeader = $("<div></div>").addClass(
        "title align-items-center mb-1"
      );
      const cardTitle = $("<h3></h3>")
        .text(promotion.name)
        .addClass("card-title");

      const cardStatus = $("<span></span>").addClass("mx-2 badge");
      if (promotion.active) {
        cardStatus.addClass("text-bg-success").text("Active");
      } else {
        cardStatus.addClass("text-bg-secondary").text("Inactive");
      }
      cardTitle.append(cardStatus);

      const cardActions = $("<div></div>").addClass("actions");

      const editAction = $("<a></a>")
        .text("Edit")
        .addClass("btn btn-outline-primary")
        .attr("href", promotionEditUrl.replace("uuid", "") + promotion.uuid);
      const deleteAction = $("<button></button>")
        .text("Delete")
        .addClass("btn btn-outline-danger");
      deleteAction.on("click", function () {
        const deletePromotionModal = new bootstrap.Modal(
          document.getElementById("delete-promotion-modal"),
          {}
        );
        $("#delete-promotion-modal-button").data("uuid", promotion.uuid);
        deletePromotionModal.show();
      });

      cardActions.append(editAction);
      cardActions.append(deleteAction);

      cardHeader.append(cardTitle);
      cardHeader.append(cardActions);
      cardBody.append(cardHeader);

      const cardDescription = $("<ul></ul>").addClass(
        "list-group list-group-flush"
      );
      const cardDescriptionDataList = [
        `Discount percentage: ${promotion.discount}`,
        `Category: ${promotion.category_name}`,
        `Start date: ${promotion.start_date}`,
        `End date: ${promotion.end_date}`,
      ];
      for (const cardDescriptionData of cardDescriptionDataList) {
        const cardDescriptionItem = $("<li></li>")
          .addClass("list-group-item")
          .text(cardDescriptionData);
        cardDescription.append(cardDescriptionItem);
      }

      cardBody.append(cardDescription);

      promotionCard.append(cardBody);

      $("#promotions-list").append(promotionCard);
    }
  } else {
    console.log("Failed!");
  }

  return true;
}

const clearFilters = () => {
  clearForm("filter-form");
  resetPagination();
  filterPromotions();
};
