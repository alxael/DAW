$(document).ready(async function () {
  if (window.location.pathname === offerListUrl) {
    await fetchStockData();
    await filterOffers();
    setPaginationRecordsPerPage(filterOffers);
  }
  if (
    window.location.pathname.substring(0, 12) ===
    offerViewUrl.replace("uuid", "")
  ) {
    await fetchStockData();
    await viewOffer(window.location.pathname.substring(12));
  }

  if (window.location.pathname === cartUrl) {
    await fetchStockData();
    loadCart();
  }
});

// Offer

async function filterOffers() {
  const formElement = document.forms["filter-form"];
  const formData = new FormData(formElement);

  let url = new URL(offerListUrl, window.location.origin);
  url.searchParams.set("page_number", pageNumber);
  url.searchParams.set("records_per_page", recordsPerPage);
  url.searchParams.set("currency", currency);

  const response = await fetchData("POST", url.toString(), formData);

  $("#offers-list").empty();
  if (response.success) {
    setPaginationPageNumbers(filterOffers, response.pages);

    const offersGrid = $("<div></div>").addClass(
      "row row-eq-height row-cols-xl-3 row-cols-sm-1"
    );
    for (const offer of response.offers) {
      const offerCardWrapper = $("<div></div>").addClass(
        "col gx-2 offer-card-wrapper"
      );
      const offerCard = $("<div></div>").addClass("card offer-card");

      const offerMarker = $("<span></span>")
        .addClass("badge rounded-pill z-1")
        .attr("id", `offer-marker-${offer.uuid}`);

      const cardBody = $("<div></div>").addClass("card-body");

      const cardHeader = $("<div></div>").addClass(
        "title align-items-start mb-1"
      );
      const cardTitle = $("<h4></h4>").text(offer.name).addClass("card-title");

      cardHeader.append(cardTitle);
      cardBody.append(cardHeader);

      const cardDescription = $("<p></p>")
        .text(offer.description)
        .addClass("card-subtitle text-muted text-truncate mb-2");
      cardBody.append(cardDescription);

      const cardFooter = $("<div></div>").addClass("hstack align-items-end");
      const cardPrice = $("<h6></h6>")
        .addClass("text-danger")
        .text(`${offer.price_discounted} ${currency}`);
      if (offer.price !== offer.price_discounted) {
        const cardPriceWithoutDiscount = $("<h6></h6>")
          .addClass("text-muted text-decoration-line-through mx-2")
          .text(`${offer.price} ${currency}`);
        cardFooter.append(cardPriceWithoutDiscount);
      }
      const cardViewButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-outline-primary ms-auto");
      cardViewButton.on("click", function () {
        let url = new URL(
          offerViewUrl.replace("uuid", offer.uuid),
          window.location.origin
        );
        url.searchParams.set("currency", currency);
        window.location.href = url.toString();
      });
      const cardViewButtonIcon = $("<i></i>").addClass("bi bi-eye");
      cardViewButton.append(cardViewButtonIcon);

      const cardPurchaseButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-primary mx-2");
      cardPurchaseButton.on("click", function () {
        addToCart(offer.uuid, 1);
      });
      const cardPurchaseButtonIcon = $("<i></i>").addClass("bi bi-cart");
      cardPurchaseButton.append(cardPurchaseButtonIcon);

      const offerProductUuid = stockData.offer_product[offer.uuid];
      const productStockQuantity = stockData.product_stock[offerProductUuid];
      const productCartQuantity = localStorage.getItem(offer.uuid);

      if (productStockQuantity !== 0) {
        offerCard.on("mouseenter", function () {
          $(this).addClass("text-bg-light");
        });
        offerCard.on("mouseleave", function () {
          $(this).removeClass("text-bg-light");
        });
      } else {
        offerCard.addClass("text-bg-light");
      }

      if (productStockQuantity === 0) {
        cardPurchaseButton.addClass("disabled");
        offerMarker.text("Out of stock");
        offerMarker.addClass("text-bg-warning");
      }

      if (productCartQuantity !== null && isAuthenticated) {
        offerMarker.text("In cart");
        offerMarker.addClass("text-bg-danger");
      }

      cardHeader.append(offerMarker);

      cardFooter.append(cardPrice);
      cardFooter.append(cardViewButton);
      cardFooter.append(cardPurchaseButton);
      cardBody.append(cardFooter);

      offerCard.append(cardBody);
      offerCardWrapper.append(offerCard);

      offersGrid.append(offerCardWrapper);
    }
    $("#offers-list").append(offersGrid);
  } else {
    // replace with toast
  }

  return true;
}

const clearFilters = () => {
  clearForm("filter-form");
  resetPagination();
  filterOffers();
};

const viewOffer = async (offerUuid) => {
  const offerProductUuid = stockData.offer_product[offerUuid];
  const productStockQuantity = stockData.product_stock[offerProductUuid];
  const productCartQuantity = localStorage.getItem(offerUuid);

  const offerMarker = $("<span></span>")
    .addClass("badge mx-4 z-1")
    .attr("id", `offer-marker-${offerUuid}`);

  if (productStockQuantity === 0) {
    $("#purchase-button").addClass("disabled");
    offerMarker.addClass("text-bg-warning");
    offerMarker.text("Out of stock");
  }

  if (productCartQuantity !== null && isAuthenticated) {
    offerMarker.addClass("text-bg-danger");
    offerMarker.text("In cart");
  }

  $("#offer-title").append(offerMarker);
  $("#offer-price").append(" " + currency);
  $("#offer-price-discounted").append(" " + currency);
};

// Cart

let cartData = null;
let totalPrice = 0;

const generateEmptyCartAlert = () => {
  const cartItemsCount = localStorage.getItem("cartItemsCount");
  if (cartItemsCount == 0 || cartItemsCount === null) {
    const emptyCartAlert = $("<div></div>").addClass(
      "card p-2 text-bg-warning"
    );

    const body = $("<div></div>").addClass("card-body");
    const title = $("<h4></h4>").addClass("card-title").text("Cart is empty!");

    const content = $("<p></p>")
      .addClass("card-text")
      .text(
        "Head over to the offers page in order to add products to your cart!"
      );

    body.append(title);
    body.append(content);

    emptyCartAlert.append(body);
    $("#cart-list").append(emptyCartAlert);
  }
};

const updateCartItem = (offerUuid, quantity) => {
  const offerCartQuantity = Number(localStorage.getItem(offerUuid));
  const actionOutcome = addToCart(
    offerUuid,
    quantity - offerCartQuantity,
    false
  );
  if (actionOutcome !== false) {
    quantity = offerCartQuantity + actionOutcome;
    const offerPriceNew = Number(cartData[offerUuid].price) * quantity;
    const totalPriceDelta = Number(cartData[offerUuid].price) * actionOutcome;
    $(`#cart-price-${offerUuid}`).text(
      `${offerPriceNew.toFixed(2)} ${currency}`
    );
    $(`#cart-quantity-${offerUuid}`).text(quantity);
    if (quantity === 0) {
      $(`#${offerUuid}`).remove();
      localStorage.removeItem(offerUuid);
    }
    $(`#cart-input-${offerUuid}`).val(quantity);
    generateEmptyCartAlert();
    totalPrice += totalPriceDelta;
    $("#cart-total-price").text(`${totalPrice.toFixed(2)} ${currency}`);
  }
  return actionOutcome === false ? false : quantity;
};

const loadCart = async () => {
  const offerUuids = getCartOfferUuids();

  let url = new URL(cartUrl, window.location.origin);
  url.searchParams.set("currency", currency);

  try {
    const response = await fetchData(
      "POST",
      url.toString(),
      JSON.stringify({ offers: offerUuids })
    );

    $("#cart-list").empty();
    generateEmptyCartAlert();

    cartData = {};
    for (const offer of response.offers) {
      cartData[offer.uuid] = offer;
      const offerCartQuantity = Number(localStorage.getItem(offer.uuid));

      const card = $("<div></div>")
        .attr("id", offer.uuid)
        .addClass("card mb-3");

      const cardBody = $("<div></div>").addClass("card-body");

      const cardTitleWrapper = $("<div></div>").addClass(
        "card-title d-flex flex-row"
      );
      const cardTitle = $("<h4></h4>").text(offer.name);
      const cardActions = $("<div></div>").addClass("ms-auto");

      const cardDeleteButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-sm btn-outline-danger mx-1");
      cardDeleteButton.on("click", function () {
        updateCartItem(offer.uuid, 0);
      });
      const cardDeleteButtonIcon = $("<i></i>").addClass("bi bi-trash");
      cardDeleteButton.append(cardDeleteButtonIcon);

      const cardViewButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-sm btn-primary mx-1");
      cardViewButton.on("click", function () {
        let url = new URL(
          offerViewUrl.replace("uuid", offer.uuid),
          window.location.origin
        );
        url.searchParams.set("currency", currency);
        window.location.href = url.toString();
      });
      const cardViewButtonIcon = $("<i></i>").addClass("bi bi-eye");
      cardViewButton.append(cardViewButtonIcon);
      cardActions.append(cardDeleteButton);

      cardActions.append(cardViewButton);

      cardTitleWrapper.append(cardTitle);
      cardTitleWrapper.append(cardActions);

      const cardText = $("<p></p>")
        .addClass("card-subtitle text-muted text-truncate")
        .text(offer.description);

      cardBody.append(cardTitleWrapper);
      cardBody.append(cardText);

      const cardFooter = $("<div></div>").addClass(
        "card-footer d-flex flex-row justify-content-between"
      );

      const offerQuantity = $("<div></div>")
        .addClass("card-text")
        .text("Quantity");
      const offerQuantityValue = $("<span></span>")
        .addClass("badge text-bg-danger mx-2")
        .text(offerCartQuantity)
        .attr("id", `cart-quantity-${offer.uuid}`);
      offerQuantity.append(offerQuantityValue);

      const offerQuantityControl = $("<div></div>").addClass("d-flex flex-row justify-content-center");

      const offerSubtractQuantityButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-sm btn-outline-primary mx-1");
      offerSubtractQuantityButton.on("click", function () {
        updateCartItem(
          offer.uuid,
          Number(localStorage.getItem(offer.uuid)) - 1
        );
      });

      const offerQuantityInput = $("<input></input>")
        .addClass("form-control form-control-sm w-25")
        .attr("id", `cart-input-${offer.uuid}`)
        .attr("min", "0")
        .val(offerCartQuantity)
        .data("value", offerCartQuantity);

      offerQuantityInput.keyup(function () {
        const offerQuantity = Number(this.value);
        if (!isNaN(offerQuantity)) {
          const actionOutcome = updateCartItem(offer.uuid, offerQuantity);
          if (actionOutcome === false) {
            const previousValue = $(this).data("value");
            $(this).val(previousValue);
          } else {
            $(this).data("value", actionOutcome);
          }
        } else {
          const previousValue = $(this).data("value");
          $(this).val(previousValue);
        }
      });

      const offerSubtractQuantityButtonIcon =
        $("<i></i>").addClass("bi bi-dash");
      offerSubtractQuantityButton.append(offerSubtractQuantityButtonIcon);
      const offerAddQuantityButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-sm btn-outline-primary mx-1");
      offerAddQuantityButton.on("click", function () {
        updateCartItem(
          offer.uuid,
          Number(localStorage.getItem(offer.uuid)) + 1
        );
      });
      const offerAddQuantityButtonIcon = $("<i></i>").addClass("bi bi-plus");
      offerAddQuantityButton.append(offerAddQuantityButtonIcon);

      offerQuantityControl.append(offerSubtractQuantityButton);
      offerQuantityControl.append(offerQuantityInput);
      offerQuantityControl.append(offerAddQuantityButton);

      const offerPriceTotal = Number(offer.price) * offerCartQuantity;
      totalPrice += offerPriceTotal;

      const offerPrice = $("<div></div>").addClass("card-text").text("Price:");
      const offerPriceValue = $("<span></span>")
        .addClass("card-text text-danger mx-2")
        .text(`${offerPriceTotal.toFixed(2)} ${currency}`)
        .attr("id", `cart-price-${offer.uuid}`);
      offerPrice.append(offerPriceValue);

      cardFooter.append(offerQuantity);
      cardFooter.append(offerQuantityControl);
      cardFooter.append(offerPrice);

      card.append(cardBody);
      card.append(cardFooter);

      $("#cart-list").append(card);
    }

    $("#cart-total-price").text(`${totalPrice.toFixed(2)} ${currency}`);
  } catch (exception) {
    // replace with toast
  }
};
