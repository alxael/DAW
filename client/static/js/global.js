$(window).on("load", function () {
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerElement) {
    return new bootstrap.Tooltip(tooltipTriggerElement);
  });
  fetchCurrencyData();
  if (isAuthenticated) {
    setupCart();
    refreshCartItemsCount();
  }
});

// Requests

const fetchData = async (method, url, body) => {
  try {
    const response = await fetch(url, {
      method: method,
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
      },
      body: body,
    }).then((data) => data.json());
    return response;
  } catch (exception) {
    console.log(exception);
  }
};

// Forms

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

// Modals

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

// Toaster

let toastId = 0;

const createToast = (message, color) => {
  toastId += 1;

  const toast = $("<div></div>")
    .addClass(`toast text-bg-${color}`)
    .attr("id", `toast-${toastId}`)
    .attr("role", "alert")
    .attr("aria-live", "assertive")
    .attr("aria-atomic", "true");

  const flexWrapper = $("<div></div>").addClass("d-flex");
  const toastCloseButton = $("<button></button>")
    .addClass("btn-close me-2 m-auto")
    .attr("type", "button")
    .attr("data-bs-dismiss", "toast")
    .attr("aria-label", "Close");
  const toastBody = $("<div></div>").addClass("toast-body").html(message);

  flexWrapper.append(toastBody);
  flexWrapper.append(toastCloseButton);

  toast.append(flexWrapper);

  const toaster = $("#toaster");
  toaster.append(toast);

  const toastElement = document.getElementById(`toast-${toastId}`);
  const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toastElement);
  toastBootstrap.show();
};

// Pagination

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

// Currencies

let currency = localStorage.getItem("currency");
if (currency === null) {
  currency = defaultCurrency;
  localStorage.setItem("currency", currency);
}

const setCurrency = (currencyCode) => {
  currency = currencyCode;
  localStorage.setItem("currency", currency);

  const url = new URL(window.location.href);
  if (url.searchParams.has("currency")) {
    url.searchParams.set("currency", currency);
  }
  window.location.href = url.toString();
};

const fetchCurrencyData = async () => {
  const response = await fetchData("GET", currencyListUrl, null);

  const currencyDropdown = $("#currency-dropdown");
  for (const currencyData of response.currencies) {
    const currencyDropdownItem = $("<li></li>");
    const currencyDropdownButton = $("<button></button>")
      .addClass("dropdown-item")
      .text(currencyData.name)
      .attr("id", `currency-${currencyData.code}`);
    if (currencyData.code === currency) {
      currencyDropdownButton.addClass("active");
    }
    currencyDropdownButton.on("click", function () {
      $(`currency-${currency}`).removeClass("active");
      setCurrency(currencyData.code);
      $(`currency-${currencyData.code}`).addClass("active");
    });
    currencyDropdownItem.append(currencyDropdownButton);
    currencyDropdown.append(currencyDropdownItem);
  }
};

// Cart

let stockData = null;

const fetchStockData = async () => {
  const response = await fetchData("GET", stockListOffersUrl, null);
  stockData = response;
};

const getCartOfferUuids = () => {
  const offerUuids = [];
  const localStorageKeys = Object.keys(localStorage);
  for (const key of localStorageKeys) {
    if (key.length === 36) {
      offerUuids.push(key);
    }
  }
  return offerUuids;
};

const setupCart = () => {
  const offerUuids = getCartOfferUuids();
  let cartItemsCount = 0;
  for (const offerUuid of offerUuids) {
    cartItemsCount += Number(localStorage.getItem(offerUuid));
  }
  localStorage.setItem("cartItemsCount", cartItemsCount);
};

const refreshCartItemsCount = () => {
  const cartItemsCount = Number(localStorage.getItem("cartItemsCount"));
  if (cartItemsCount > 0) {
    $("#cart-items-count").text(cartItemsCount);
  } else {
    $("#cart-items-count").text("");
  }
};

const getCartProductQuantity = (productUuid) => {
  const offerUuids = getCartOfferUuids();
  let totalProductQuantity = 0;
  for (const offerUuid of offerUuids) {
    const offerProductUuid = stockData.offer_product[offerUuid];
    if (offerProductUuid === productUuid) {
      totalProductQuantity += Number(localStorage.getItem(offerUuid));
    }
  }
  return totalProductQuantity;
};

const addToCart = (offerUuid, delta, showSuccessToast = true) => {
  if (!isAuthenticated) {
    createToast(
      "<strong>Please sign in</strong> in order to add items to the cart!",
      "warning"
    );
    return;
  }

  const offerProductUuid = stockData.offer_product[offerUuid];
  const stockProductQuantity = stockData.product_stock[offerProductUuid];
  const cartProductQuantity = getCartProductQuantity(offerProductUuid);

  const deltaAdjusted = Math.min(
    delta,
    stockProductQuantity - cartProductQuantity
  );

  let cartItemsCount = Number(localStorage.getItem("cartItemsCount"));
  let newOfferItemsCount = deltaAdjusted;

  if (localStorage.getItem(offerUuid) !== null)
    newOfferItemsCount += Number(localStorage.getItem(offerUuid));
  cartItemsCount += deltaAdjusted;

  if (newOfferItemsCount >= 0) {
    localStorage.setItem(offerUuid, newOfferItemsCount);
  }
  localStorage.setItem("cartItemsCount", String(cartItemsCount));
  refreshCartItemsCount();
  refreshCartItemMarker(offerUuid);

  if (deltaAdjusted !== 0) {
    if (showSuccessToast) {
      createToast(
        "<strong>Success!</strong> You have added a product to your cart!",
        "success"
      );
    }
    return deltaAdjusted;
  } else {
    createToast(
      "<strong>Error!</strong> You may not add another product of this type because you have exceeded our stock!",
      "danger"
    );
    return false;
  }
};

const refreshCartItemMarker = (offerUuid) => {
  const offerProductUuid = stockData.offer_product[offerUuid];
  const productStockQuantity = stockData.product_stock[offerProductUuid];
  const productCartQuantity = localStorage.getItem(offerUuid);

  const offerMarker = $(`#offer-marker-${offerUuid}`);

  if (productStockQuantity === 0) {
    $("#purchase-button").addClass("disabled");
    offerMarker.addClass("text-bg-warning");
    offerMarker.text("Out of stock");
  }

  if (productCartQuantity !== null) {
    offerMarker.addClass("text-bg-danger");
    offerMarker.text("In cart");
  }
};

const clearCart = () => {
  const offerUuids = getCartOfferUuids();
  localStorage.removeItem("cartItemsCount");
  for (const offerUuid of offerUuids) {
    $(`#${offerUuid}`).remove();
    localStorage.removeItem(offerUuid);
  }
  refreshCartItemsCount();
  totalPrice = 0;
  $("#cart-total-price").text(`${totalPrice.toFixed(2)} ${currency}`);
  generateEmptyCartAlert();
};
