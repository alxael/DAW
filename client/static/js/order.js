$(document).ready(function () {
  if (window.location.pathname === orderListUrl) {
    fetchOrders();
    setPaginationRecordsPerPage(fetchOrders);
  }
});

async function fetchOrders() {
  let url = new URL(orderListUrl, window.location.origin);
  url.searchParams.set("page_number", pageNumber);
  url.searchParams.set("records_per_page", recordsPerPage);

  const response = await fetchData("POST", url.toString(), null);

  console.log(response);
  $("#orders-list").empty();
  if (response.success) {
    setPaginationPageNumbers(fetchOrders, response.pages);

    for (const order of response.orders) {
      const orderCard = $("<div></div>")
        .addClass("card mb-3")
        .attr("id", order.uuid);

      const orderCardBody = $("<div></div>").addClass(
        "card-body d-flex flex-row"
      );

      const offersColumn = $("<div></div>").addClass("col col-md-7");
      const offersList = $("<ul></ul>").addClass("list-group list-group-flush");

      for (const offer of order.offers) {
        const offerListItem = $("<li></li>")
          .addClass("list-group-item d-flex flex-row")
          .attr("id", offer.offerUuid);
        const offerListItemName = $("<span></span>")
          .addClass("col col-4")
          .text(offer.name);
        const offerListItemQunatity = $("<span></span>")
          .addClass("col col-4")
          .text(`Quantity: ${offer.quantity}`);
        const offerListItemPrice = $("<span></span>")
          .addClass("col col-4")
          .text(`Price: ${offer.price}`);

        offerListItem.append(offerListItemName);
        offerListItem.append(offerListItemQunatity);
        offerListItem.append(offerListItemPrice);
        offersList.append(offerListItem);
      }
      offersColumn.append(offersList);

      const divider = $("<div></div>").addClass("vr");

      const orderInformationColumn = $("<div></div>").addClass("col col-md-4");
      const orderInformation = $("<div></div>").addClass(
        "d-flex flex-column px-3 py-2"
      );

      const orderPrice = $("<h6></h6>").text(`Total price: ${order.price}`);
      const orderDate = $("<h6></h6>").text(`Date: ${order.date}`);
      const orderStatus = $("<h6></h6>").text(`Status: ${order.status}`);

      const orderInvoice = $("<h6></h6>").text("Invoice: ");
      const orderInvoiceLink = $("<a></a>")
        .attr("href", order.invoice)
        .text(order.invoice.substr(order.invoice.lastIndexOf("/") + 1));
      orderInvoice.append(orderInvoiceLink);

      orderInformation.append(orderPrice);
      orderInformation.append(orderDate);
      orderInformation.append(orderStatus);
      orderInformation.append(orderInvoice);

      orderInformationColumn.append(orderInformation);

      orderCardBody.append(offersColumn);
      orderCardBody.append(divider);
      orderCardBody.append(orderInformationColumn);

      orderCard.append(orderCardBody);

      $("#orders-list").append(orderCard);
    }
  } else {
    // replace with toast
  }

  return true;
}

const clearFilters = () => {
  resetPagination();
  fetchOrders();
};
