async function filterOffers() {
  const formElement = document.forms["filter-form"];
  const formData = new FormData(formElement);

  let url = new URL(offerListUrl, window.location.origin);
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

  $("#offers-list").empty();
  if (response.success) {
    setPaginationPageNumbers(filterOffers, response.pages);

    const offersGrid = $("<div></div>").addClass(
      "row row-eq-height row-cols-xl-4 row-cols-sm-2 row-cols-1"
    );
    for (const offer of response.offers) {
      const offerCardWrapper = $("<div></div>").addClass(
        "col gx-2 offer-card-wrapper"
      );
      const offerCard = $("<div></div>")
        .addClass("card offer-card text-bg-light")
        .attr("id", offer.uuid);
      offerCard.on("mouseenter", function () {
        $(this).addClass("bg-light");
      });
      offerCard.on("mouseleave", function () {
        $(this).removeClass("bg-light");
      });
      offerCard.on("click", function () {
        window.location.href = offerViewUrl.replace("uuid", $(this).attr("id"));
      });

      const cardBody = $("<div></div>").addClass("card-body");

      const cardHeader = $("<div></div>").addClass(
        "title align-items-center mb-1"
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
        .text(offer.price_discounted);
      if (offer.price !== offer.price_discounted) {
        const cardPriceWithoutDiscount = $("<h6></h6>")
          .addClass("text-muted text-decoration-line-through mx-2")
          .text(offer.price);
        cardFooter.append(cardPriceWithoutDiscount);
      }
      const cardPurchaseButton = $("<button></button>")
        .attr("type", "button")
        .addClass("btn btn-primary ms-auto");
      const cardPurchaseButtonIcon = $("<i></i>").addClass("bi bi-cart");
      cardPurchaseButton.append(cardPurchaseButtonIcon);
      cardFooter.append(cardPrice);
      cardFooter.append(cardPurchaseButton);
      cardBody.append(cardFooter);

      offerCard.append(cardBody);
      offerCardWrapper.append(offerCard);

      offersGrid.append(offerCardWrapper);
    }
    $("#offers-list").append(offersGrid);
  } else {
    console.log("Failed!");
  }

  return true;
}

const clearFilters = () => {
  clearForm("filter-form");
  resetPagination();
  filterOffers();
};

$(document).ready(function () {
  if (window.location.pathname === offerListUrl) {
    filterOffers();
    createConfirmDeleteModal(
      "delete-offer-modal",
      "Delete offer",
      "Are you sure you want to delete this offer? After deletion, the offer can not be restored!"
    );
  }
  setPaginationRecordsPerPage(filterOffers);
});
