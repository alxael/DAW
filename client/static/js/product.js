async function addProduct() {
  const formElement = document.forms["add-product-form"];
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
    clearForm("add-product-form", ["categories"], true);

    const responseSuccessAlert = $("<div></div>")
      .text(
        "You have successfully created a product. To vizualize the product you created, go to the "
      )
      .attr("id", "response-success")
      .addClass("alert alert-success mt-3");
    const pageListLinkText = $("<a></a>")
      .text("product list page")
      .attr("href", productListUrl)
      .addClass("link-success");
    responseSuccessAlert.append(pageListLinkText);
    $("#add-product-form").parent().append(responseSuccessAlert);

    setTimeout(() => {
      $("#response-success").remove();
    }, 10000);
  } else {
    showFormErrors(response.errors, $("#add-product-form").parent());
  }
  return true;
}

async function editProduct() {
  const formElement = document.forms["edit-product-form"];
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
        "You have successfully edited the product. You may now return to the "
      )
      .attr("id", "response-success")
      .addClass("alert alert-success mt-3");
    const pageListLinkText = $("<a></a>")
      .text("product list page")
      .attr("href", productListUrl)
      .addClass("link-success");
    responseSuccessAlert.append(pageListLinkText);
    $("#edit-product-form").parent().append(responseSuccessAlert);

    setTimeout(() => {
      $("#response-success").remove();
    }, 10000);
  } else {
    showFormErrors(response.errors, $("#edit-product-form").parent());
  }
  return true;
}

async function deleteProduct(uuid) {
  const response = await fetch(productDeleteUrl.replace("uuid", uuid), {
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

async function filterProducts() {
  const formElement = document.forms["filter-form"];
  const formData = new FormData(formElement);

  let url = new URL(productListUrl, window.location.origin);
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

  $("#products-list").empty();
  if (response.success) {
    setPaginationPageNumbers(filterProducts, response.pages);

    for (const product of response.products) {
      const productCard = $("<div></div>")
        .addClass("card product-card")
        .attr("id", product.uuid);

      const cardBody = $("<div></div>").addClass("card-body");

      const cardHeader = $("<div></div>").addClass(
        "title align-items-center mb-3"
      );
      const cardTitle = $("<h3></h3>")
        .text(product.name)
        .addClass("card-title");
      const cardActions = $("<div></div>").addClass("actions");

      const editAction = $("<a></a>")
        .text("Edit")
        .addClass("btn btn-outline-primary")
        .attr("href", productEditUrl.replace("uuid", "") + product.uuid);
      const deleteAction = $("<button></button>")
        .text("Delete")
        .addClass("btn btn-outline-danger");
      deleteAction.on("click", function () {
        const deleteProductModal = new bootstrap.Modal(
          document.getElementById("delete-product-modal"),
          {}
        );
        $("#delete-product-modal-button").data("uuid", product.uuid);
        deleteProductModal.show();
      });

      cardActions.append(editAction);
      cardActions.append(deleteAction);

      cardHeader.append(cardTitle);
      cardHeader.append(cardActions);
      cardBody.append(cardHeader);

      const cardDescription = $("<h6></h6>")
        .text(product.description)
        .addClass("card-subtitle text-muted mb-2");
      cardBody.append(cardDescription);

      const categoryTagList = $("<div></div>").addClass(
        "d-flex flex-row flex-wrap"
      );
      for (const category of product.categories) {
        const categoryTag = $("<span></span>")
          .text(category.name)
          .addClass("badge bg-primary p-2 m-1");
        categoryTagList.append(categoryTag);
      }
      cardBody.append(categoryTagList);

      productCard.append(cardBody);

      $("#products-list").append(productCard);
    }
  } else {
    console.log("Failed!");
  }

  return true;
}

const clearFilters = () => {
  clearForm("filter-form");
  resetPagination();
  filterProducts();
};

$(document).ready(function () {
  if (window.location.pathname === productListUrl) {
    filterProducts();
    createConfirmDeleteModal(
      "delete-product-modal",
      "Delete product",
      "Are you sure you want to delete this product? After deletion, the product can not be restored!"
    );
    $("#delete-product-modal-button").on("click", async function () {
      const uuid = $(this).data("uuid");
      const response = await deleteProduct(uuid);
      if (response) {
        $(`#${uuid}`).remove();
        filterProducts();
      }
    });
  }
  setPaginationRecordsPerPage(filterProducts);
});
